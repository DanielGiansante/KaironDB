"""
Sistema de Connection Pooling Avançado para KaironDB
"""

import asyncio
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from .typing import PoolConfig, Metrics, HealthCheck, LogLevel
from .exceptions import PoolError, ConnectionError, ConfigurationError


class ConnectionState(Enum):
    """Estados de uma conexão no pool."""
    IDLE = "idle"
    ACTIVE = "active"
    BROKEN = "broken"
    CLOSING = "closing"


@dataclass
class ConnectionInfo:
    """Informações sobre uma conexão no pool."""
    id: str
    state: ConnectionState
    created_at: float
    last_used: float
    use_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedConnectionPool:
    """Pool de conexões avançado com métricas e health checks."""
    
    def __init__(
        self,
        min_connections: int = 1,
        max_connections: int = 10,
        connection_timeout: float = 30.0,
        idle_timeout: float = 300.0,
        max_lifetime: float = 3600.0,
        health_check_interval: float = 60.0,
        health_check_timeout: float = 5.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        logger: Optional[logging.Logger] = None
    ):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        self.max_lifetime = max_lifetime
        self.health_check_interval = health_check_interval
        self.health_check_timeout = health_check_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        self.logger = logger or logging.getLogger('kairondb.pool')
        
        # Estado do pool
        self._connections: Dict[str, ConnectionInfo] = {}
        self._idle_connections: List[str] = []
        self._active_connections: List[str] = []
        self._broken_connections: List[str] = []
        
        # Métricas
        self._metrics = {
            'total_created': 0,
            'total_closed': 0,
            'total_errors': 0,
            'total_health_checks': 0,
            'total_health_check_failures': 0,
            'peak_connections': 0,
            'current_connections': 0,
            'idle_connections': 0,
            'active_connections': 0,
            'broken_connections': 0
        }
        
        # Controle
        self._lock = threading.RLock()
        self._closed = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._on_connection_created: Optional[Callable[[str], None]] = None
        self._on_connection_closed: Optional[Callable[[str], None]] = None
        self._on_connection_broken: Optional[Callable[[str, str], None]] = None
        self._on_health_check_failed: Optional[Callable[[str, str], None]] = None
    
    def set_callbacks(
        self,
        on_connection_created: Optional[Callable[[str], None]] = None,
        on_connection_closed: Optional[Callable[[str], None]] = None,
        on_connection_broken: Optional[Callable[[str, str], None]] = None,
        on_health_check_failed: Optional[Callable[[str, str], None]] = None
    ) -> None:
        """Define callbacks para eventos do pool."""
        self._on_connection_created = on_connection_created
        self._on_connection_closed = on_connection_closed
        self._on_connection_broken = on_connection_broken
        self._on_health_check_failed = on_health_check_failed
    
    async def initialize(self) -> None:
        """Inicializa o pool criando as conexões mínimas."""
        if self._closed:
            raise PoolError("Pool já foi fechado")
        
        self.logger.info(f"Inicializando pool com {self.min_connections} conexões mínimas")
        
        # Criar conexões mínimas
        for _ in range(self.min_connections):
            try:
                await self._create_connection()
            except Exception as e:
                self.logger.error(f"Erro ao criar conexão inicial: {e}")
                raise PoolError(f"Falha ao inicializar pool: {e}")
        
        # Iniciar tasks de manutenção
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info(f"Pool inicializado com {len(self._connections)} conexões")
    
    async def get_connection(self, timeout: Optional[float] = None) -> str:
        """Obtém uma conexão do pool."""
        if self._closed:
            raise PoolError("Pool foi fechado")
        
        timeout = timeout or self.connection_timeout
        start_time = time.time()
        
        with self._lock:
            # Tentar obter conexão idle
            if self._idle_connections:
                conn_id = self._idle_connections.pop(0)
                conn = self._connections[conn_id]
                conn.state = ConnectionState.ACTIVE
                conn.last_used = time.time()
                conn.use_count += 1
                self._active_connections.append(conn_id)
                self._update_metrics()
                return conn_id
            
            # Criar nova conexão se possível
            if len(self._connections) < self.max_connections:
                try:
                    conn_id = await self._create_connection()
                    conn = self._connections[conn_id]
                    conn.state = ConnectionState.ACTIVE
                    conn.last_used = time.time()
                    conn.use_count += 1
                    self._active_connections.append(conn_id)
                    self._update_metrics()
                    return conn_id
                except Exception as e:
                    self.logger.error(f"Erro ao criar nova conexão: {e}")
                    raise PoolError(f"Falha ao criar conexão: {e}")
            
            # Aguardar conexão disponível
            self.logger.warning("Pool esgotado, aguardando conexão disponível")
        
        # Aguardar com timeout
        while time.time() - start_time < timeout:
            await asyncio.sleep(0.1)
            
            with self._lock:
                if self._idle_connections:
                    conn_id = self._idle_connections.pop(0)
                    conn = self._connections[conn_id]
                    conn.state = ConnectionState.ACTIVE
                    conn.last_used = time.time()
                    conn.use_count += 1
                    self._active_connections.append(conn_id)
                    self._update_metrics()
                    return conn_id
        
        raise PoolError(f"Timeout ao obter conexão após {timeout}s")
    
    async def release_connection(self, conn_id: str) -> None:
        """Libera uma conexão de volta para o pool."""
        with self._lock:
            if conn_id not in self._connections:
                self.logger.warning(f"Tentativa de liberar conexão inexistente: {conn_id}")
                return
            
            conn = self._connections[conn_id]
            if conn.state != ConnectionState.ACTIVE:
                self.logger.warning(f"Tentativa de liberar conexão não ativa: {conn_id}")
                return
            
            # Verificar se a conexão ainda é válida
            if self._is_connection_expired(conn):
                await self._close_connection(conn_id, "Conexão expirada")
                return
            
            # Retornar para idle
            conn.state = ConnectionState.IDLE
            conn.last_used = time.time()
            self._active_connections.remove(conn_id)
            self._idle_connections.append(conn_id)
            self._update_metrics()
    
    async def close_connection(self, conn_id: str, reason: str = "Fechamento manual") -> None:
        """Fecha uma conexão específica."""
        await self._close_connection(conn_id, reason)
    
    async def _create_connection(self) -> str:
        """Cria uma nova conexão."""
        conn_id = f"conn_{int(time.time() * 1000)}_{len(self._connections)}"
        
        # Aqui seria onde você criaria a conexão real com o banco
        # Por enquanto, simulamos com um delay
        await asyncio.sleep(0.01)
        
        conn = ConnectionInfo(
            id=conn_id,
            state=ConnectionState.IDLE,
            created_at=time.time(),
            last_used=time.time()
        )
        
        with self._lock:
            self._connections[conn_id] = conn
            self._idle_connections.append(conn_id)
            self._metrics['total_created'] += 1
            self._update_metrics()
        
        if self._on_connection_created:
            self._on_connection_created(conn_id)
        
        self.logger.debug(f"Conexão criada: {conn_id}")
        return conn_id
    
    async def _close_connection(self, conn_id: str, reason: str) -> None:
        """Fecha uma conexão."""
        with self._lock:
            if conn_id not in self._connections:
                return
            
            conn = self._connections[conn_id]
            conn.state = ConnectionState.CLOSING
            
            # Remover de todas as listas
            if conn_id in self._idle_connections:
                self._idle_connections.remove(conn_id)
            if conn_id in self._active_connections:
                self._active_connections.remove(conn_id)
            if conn_id in self._broken_connections:
                self._broken_connections.remove(conn_id)
            
            # Aqui seria onde você fecharia a conexão real
            # Por enquanto, simulamos com um delay
            await asyncio.sleep(0.01)
            
            del self._connections[conn_id]
            self._metrics['total_closed'] += 1
            self._update_metrics()
        
        if self._on_connection_closed:
            self._on_connection_closed(conn_id)
        
        self.logger.debug(f"Conexão fechada: {conn_id} - {reason}")
    
    def _is_connection_expired(self, conn: ConnectionInfo) -> bool:
        """Verifica se uma conexão expirou."""
        now = time.time()
        
        # Verificar lifetime
        if now - conn.created_at > self.max_lifetime:
            return True
        
        # Verificar idle timeout
        if conn.state == ConnectionState.IDLE and now - conn.last_used > self.idle_timeout:
            return True
        
        return False
    
    async def _health_check_loop(self) -> None:
        """Loop de verificação de saúde das conexões."""
        while not self._closed:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no health check loop: {e}")
                self._metrics['total_errors'] += 1
    
    async def _perform_health_checks(self) -> None:
        """Executa verificações de saúde em todas as conexões."""
        self._metrics['total_health_checks'] += 1
        
        with self._lock:
            connections_to_check = list(self._connections.keys())
        
        for conn_id in connections_to_check:
            try:
                await self._check_connection_health(conn_id)
            except Exception as e:
                self.logger.error(f"Erro ao verificar saúde da conexão {conn_id}: {e}")
                self._metrics['total_health_check_failures'] += 1
    
    async def _check_connection_health(self, conn_id: str) -> None:
        """Verifica a saúde de uma conexão específica."""
        with self._lock:
            if conn_id not in self._connections:
                return
            
            conn = self._connections[conn_id]
            
            # Verificar se expirou
            if self._is_connection_expired(conn):
                await self._close_connection(conn_id, "Conexão expirada no health check")
                return
            
            # Aqui seria onde você faria um ping real na conexão
            # Por enquanto, simulamos com um delay
            try:
                await asyncio.wait_for(asyncio.sleep(0.001), timeout=self.health_check_timeout)
                conn.last_error = None
            except asyncio.TimeoutError:
                # Conexão não respondeu
                conn.state = ConnectionState.BROKEN
                conn.last_error = "Health check timeout"
                self._broken_connections.append(conn_id)
                
                if self._on_health_check_failed:
                    self._on_health_check_failed(conn_id, "Health check timeout")
                
                self.logger.warning(f"Conexão {conn_id} falhou no health check")
            except Exception as e:
                # Outro erro
                conn.state = ConnectionState.BROKEN
                conn.last_error = str(e)
                self._broken_connections.append(conn_id)
                
                if self._on_health_check_failed:
                    self._on_health_check_failed(conn_id, str(e))
                
                self.logger.warning(f"Conexão {conn_id} falhou no health check: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Loop de limpeza de conexões expiradas."""
        while not self._closed:
            try:
                await asyncio.sleep(30)  # Limpeza a cada 30 segundos
                await self._cleanup_expired_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no cleanup loop: {e}")
    
    async def _cleanup_expired_connections(self) -> None:
        """Remove conexões expiradas."""
        with self._lock:
            expired_connections = [
                conn_id for conn_id, conn in self._connections.items()
                if self._is_connection_expired(conn)
            ]
        
        for conn_id in expired_connections:
            await self._close_connection(conn_id, "Conexão expirada no cleanup")
    
    def _update_metrics(self) -> None:
        """Atualiza as métricas do pool."""
        self._metrics['current_connections'] = len(self._connections)
        self._metrics['idle_connections'] = len(self._idle_connections)
        self._metrics['active_connections'] = len(self._active_connections)
        self._metrics['broken_connections'] = len(self._broken_connections)
        
        if len(self._connections) > self._metrics['peak_connections']:
            self._metrics['peak_connections'] = len(self._connections)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna as métricas atuais do pool."""
        with self._lock:
            metrics = self._metrics.copy()
            metrics['min_connections'] = self.min_connections
            metrics['max_connections'] = self.max_connections
            return metrics
    
    def get_health_status(self) -> HealthCheck:
        """Retorna o status de saúde do pool."""
        with self._lock:
            total_connections = len(self._connections)
            broken_connections = len(self._broken_connections)
            
            if broken_connections == 0:
                status = "healthy"
            elif broken_connections < total_connections * 0.5:
                status = "degraded"
            else:
                status = "unhealthy"
            
            return {
                'status': status,
                'checks': {
                    'has_connections': total_connections > 0,
                    'has_idle_connections': len(self._idle_connections) > 0,
                    'under_max_connections': total_connections < self.max_connections,
                    'no_broken_connections': broken_connections == 0
                },
                'timestamp': time.time(),
                'response_time': 0.0  # Seria calculado com base em health checks reais
            }
    
    def get_connection_info(self, conn_id: str) -> Optional[ConnectionInfo]:
        """Retorna informações sobre uma conexão específica."""
        with self._lock:
            return self._connections.get(conn_id)
    
    def list_connections(self) -> List[ConnectionInfo]:
        """Lista todas as conexões do pool."""
        with self._lock:
            return list(self._connections.values())
    
    async def close(self) -> None:
        """Fecha o pool e todas as conexões."""
        if self._closed:
            return
        
        self.logger.info("Fechando pool de conexões")
        self._closed = True
        
        # Cancelar tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Fechar todas as conexões
        with self._lock:
            connection_ids = list(self._connections.keys())
        
        for conn_id in connection_ids:
            await self._close_connection(conn_id, "Pool fechado")
        
        self.logger.info("Pool fechado com sucesso")
    
    def __del__(self):
        """Cleanup final."""
        if not self._closed:
            self.logger.warning("Pool não foi fechado explicitamente")
            # Em um ambiente real, você não deveria fazer operações async em __del__
            # Mas para demonstração, vamos apenas marcar como fechado
            self._closed = True
