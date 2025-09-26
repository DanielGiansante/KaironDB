"""
KaironDB Bridge Module

Este módulo contém a classe SQLBridge, que é o componente principal para interação
com bancos de dados através de uma DLL Go. Fornece uma interface assíncrona para
operações de banco de dados com suporte a transações, pooling de conexões,
cache de queries, migrations e monitoramento de performance.

Classes:
    SQLBridge: Classe principal para interação com bancos de dados
    Transaction: Context manager para transações de banco de dados
    TransactionalBridge: Bridge específica para operações transacionais

Funcionalidades:
    - Conexão com múltiplos drivers de banco (PostgreSQL, SQL Server, MySQL, SQLite)
    - Operações assíncronas (SELECT, INSERT, UPDATE, DELETE)
    - Sistema de transações com commit/rollback automático
    - Pool de conexões avançado com health checks
    - Cache de queries com TTL e invalidação
    - Sistema de migrations de banco de dados
    - Profiling e monitoramento de performance
    - Dashboard de métricas em tempo real

Exemplo:
    ```python
    import asyncio
    from kairondb import SQLBridge
    
    async def main():
        # Criar bridge com funcionalidades avançadas
        bridge = SQLBridge(
            driver="postgres",
            server="localhost",
            db_name="mydb",
            user="user",
            password="pass",
            enable_advanced_pool=True,
            enable_query_cache=True,
            enable_profiling=True
        )
        
        # Executar query
        result = await bridge.select("users", ["id", "name"], {"active": True})
        print(result)
        
        # Usar transação
        async with bridge.transaction() as tx:
            await tx.insert("users", {"name": "João", "email": "joao@example.com"})
            await tx.update("users", {"active": True}, {"name": "João"})
        
        await bridge.close()
    
    asyncio.run(main())
    ```

Autor: KaironDB Team
Versão: 1.0.0
"""

import os
import json
import asyncio
import ctypes
import time
import uuid
import traceback
import logging
from typing import Optional, Dict, Any, List, Union, Callable, Tuple
from .query import Q
from .exceptions import ConnectionError, ValidationError, PoolError, ConfigurationError
from .typing import (
    DriverType, ConnectionParams, QueryCondition, QueryFields, QueryJoins,
    QueryResults, DatabaseResult, TransactionID, PoolID, CallbackFunction,
    BridgeConfig, LogLevel
)
from .pool import AdvancedConnectionPool
from .cache import QueryCache, CacheManager, CachePolicy
from .migrations import MigrationManager
from .profiling import Profiler, profile_operation
from .optimizations import PerformanceOptimizer, OptimizationConfig
from .dashboard import MetricsDashboard, DashboardConfig

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
CALLBACK_FUNC_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)

_active_futures: Dict[str, Any] = {}

# Configurar logger para KaironDB
logger = logging.getLogger('kairondb')
logger.setLevel(logging.DEBUG)

# Handler para console (se não houver outros handlers)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Formatter com timestamp e nível
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Logger específico para bridge
bridge_logger = logging.getLogger('kairondb.bridge')


def _on_query_complete_global(result_ptr, request_id_ptr):
    try:
        bridge_logger.debug("Callback global iniciada")
        request_id = ctypes.cast(request_id_ptr, ctypes.c_char_p).value.decode('utf-8')
        bridge_logger.debug(f"Request ID recebido: {request_id}")
        
        future_tuple = _active_futures.get(request_id)
        if not future_tuple:
            bridge_logger.error(f"Future não encontrado para request_id: {request_id}")
            return
            
        future, bridge_instance, loop = future_tuple
        
        if future.done():
            bridge_logger.warning(f"Future já concluído para request_id: {request_id}")
            return

        result_str = ctypes.cast(result_ptr, ctypes.c_char_p).value.decode('utf-8')
        bridge_logger.debug(f"Resultado bruto recebido (truncado): {result_str[:200]}")
        
        try:
            result = json.loads(result_str)
            bridge_logger.debug("JSON parseado com sucesso")
            if not loop.is_closed():
                loop.call_soon_threadsafe(future.set_result, result)
                bridge_logger.debug(f"Future resolvido para request_id: {request_id}")
            else:
                bridge_logger.error("Loop de evento fechado, não é possível resolver o future")
        except json.JSONDecodeError as e:
            error_msg = f"Falha ao decodificar JSON: {str(e)}"
            bridge_logger.error(error_msg)
            if not loop.is_closed():
                loop.call_soon_threadsafe(future.set_exception, e)
    except Exception:
        error_msg = f"ERRO CRÍTICO NA CALLBACK: {traceback.format_exc()}"
        bridge_logger.critical(error_msg)

_global_callback_c = CALLBACK_FUNC_TYPE(_on_query_complete_global)

class SQLBridge:
    """
    Classe principal para interação com bancos de dados através de DLL Go.
    
    A SQLBridge fornece uma interface assíncrona para operações de banco de dados,
    incluindo suporte a múltiplos drivers, transações, pooling de conexões,
    cache de queries, migrations e monitoramento de performance.
    
    Atributos:
        SUPPORTED_DRIVERS: Lista de drivers de banco suportados
        driver: Driver de banco de dados em uso
        conn_params: Parâmetros de conexão
        debug: Modo de debug ativado
        pool_id: ID do pool de conexões
    
    Exemplo:
        ```python
        # Configuração básica
        bridge = SQLBridge(
            driver="postgres",
            server="localhost",
            db_name="mydb",
            user="user",
            password="pass"
        )
        
        # Com funcionalidades avançadas
        bridge = SQLBridge(
            driver="postgres",
            server="localhost",
            db_name="mydb",
            user="user",
            password="pass",
            enable_advanced_pool=True,
            enable_query_cache=True,
            enable_profiling=True,
            enable_dashboard=True
        )
        ```
    
    Notas:
        - Sempre feche a bridge com await bridge.close() quando terminar
        - Use transações para operações que precisam ser atômicas
        - O modo debug ativa logs detalhados para troubleshooting
    """
    
    # Drivers suportados
    SUPPORTED_DRIVERS: List[DriverType] = ['postgres', 'sqlserver', 'mysql', 'sqlite3']
    
    def _validate_connection_params(
        self, 
        driver: str, 
        server: str, 
        db_name: str, 
        user: str, 
        password: str
    ) -> None:
        """Valida os parâmetros de conexão antes de tentar conectar."""
        # Validar driver
        if not driver or not isinstance(driver, str):
            raise ValidationError(
                "Driver é obrigatório e deve ser uma string",
                field_name="driver",
                field_value=driver
            )
        
        if driver.lower() not in self.SUPPORTED_DRIVERS:
            raise ValidationError(
                f"Driver '{driver}' não é suportado. Drivers suportados: {', '.join(self.SUPPORTED_DRIVERS)}",
                field_name="driver",
                field_value=driver,
                details={"supported_drivers": self.SUPPORTED_DRIVERS}
            )
        
        # Validar server (obrigatório para todos exceto sqlite3)
        if driver.lower() != 'sqlite3':
            if not server or not isinstance(server, str):
                raise ValidationError(
                    "Server é obrigatório para drivers que não sejam sqlite3",
                    field_name="server",
                    field_value=server
                )
        
        # Validar db_name (obrigatório para todos exceto sqlite3)
        if driver.lower() != 'sqlite3':
            if not db_name or not isinstance(db_name, str):
                raise ValidationError(
                    "Database name é obrigatório para drivers que não sejam sqlite3",
                    field_name="db_name",
                    field_value=db_name
                )
        
        # Validar user e password (obrigatórios para todos exceto sqlite3)
        if driver.lower() != 'sqlite3':
            if not user or not isinstance(user, str):
                raise ValidationError(
                    "User é obrigatório para drivers que não sejam sqlite3",
                    field_name="user",
                    field_value=user
                )
            
            if not password or not isinstance(password, str):
                raise ValidationError(
                    "Password é obrigatório para drivers que não sejam sqlite3",
                    field_name="password",
                    field_value="***"  # Não expor senha
                )
        
        # Validações específicas por driver
        if driver.lower() == 'sqlite3':
            if not server or not isinstance(server, str):
                raise ValidationError(
                    "Para SQLite3, server deve conter o caminho do arquivo de banco",
                    field_name="server",
                    field_value=server
                )
        
        bridge_logger.debug(f"Parâmetros de conexão validados com sucesso para driver: {driver}")
    
    def __init__(
        self, 
        driver: str, 
        server: str, 
        db_name: str, 
        user: str, 
        password: str, 
        lib_path: Optional[str] = None, 
        debug: bool = False,
        # Advanced features
        enable_advanced_pool: bool = False,
        pool_config: Optional[Dict[str, Any]] = None,
        enable_query_cache: bool = False,
        cache_config: Optional[Dict[str, Any]] = None,
        enable_migrations: bool = False,
        migrations_dir: str = "migrations",
        # Performance and monitoring
        enable_profiling: bool = False,
        enable_optimizations: bool = False,
        enable_dashboard: bool = False,
        profiling_config: Optional[Dict[str, Any]] = None,
        optimization_config: Optional[Dict[str, Any]] = None,
        dashboard_config: Optional[Dict[str, Any]] = None
    ) -> None:
        # Validar parâmetros de conexão antes de prosseguir
        self._validate_connection_params(driver, server, db_name, user, password)
        
        self.driver = driver
        self.conn_params = {"driver": driver, "server": server, "name": db_name, "user": user, "password": password}
        self.debug = debug
        
        # Configurar nível de logging baseado no debug
        if debug:
            bridge_logger.setLevel(logging.DEBUG)
        else:
            bridge_logger.setLevel(logging.INFO)
        
        self.pool_id: Optional[str] = None
        self._explicitly_closed = False  # Flag para controlar fechamento explícito
        self.lib = self._load_library(lib_path)
        self._setup_signatures()
        self._verify_library_functions()
        self.pool_id = self._create_pool_sync()
        
        # Advanced features
        self._advanced_pool: Optional[AdvancedConnectionPool] = None
        self._cache_manager: Optional[CacheManager] = None
        self._migration_manager: Optional[MigrationManager] = None
        
        # Performance and monitoring
        self._profiler: Optional[Profiler] = None
        self._optimizer: Optional[PerformanceOptimizer] = None
        self._dashboard: Optional[MetricsDashboard] = None
        
        # Initialize advanced features
        if enable_advanced_pool:
            self._init_advanced_pool(pool_config or {})
        
        if enable_query_cache:
            self._init_query_cache(cache_config or {})
        
        if enable_migrations:
            self._init_migrations(migrations_dir)
        
        # Initialize performance and monitoring
        if enable_profiling:
            self._init_profiling(profiling_config or {})
        
        if enable_optimizations:
            self._init_optimizations(optimization_config or {})
        
        if enable_dashboard:
            self._init_dashboard(dashboard_config or {})
        
        bridge_logger.info(f"SQLBridge inicializada. Pool ID: {self.pool_id}")

    def _load_library(self, lib_path: Optional[str]) -> ctypes.CDLL:
        if lib_path is None:
            lib_name = 'sqlbridge.dll' if os.name == 'nt' else 'sqlbridge.so'
            lib_path = os.path.join(PACKAGE_DIR, lib_name)
        bridge_logger.debug(f"Tentando carregar biblioteca em: {lib_path}")
        if not os.path.exists(lib_path):
            raise ConfigurationError(
                f"Biblioteca não encontrada: {lib_path}",
                config_key="lib_path",
                details={"expected_path": lib_path}
            )
        try:
            lib = ctypes.cdll.LoadLibrary(lib_path)
            bridge_logger.info(f"Biblioteca carregada com sucesso: {lib._name}")
            return lib
        except Exception as e:
            raise ConfigurationError(
                f"Falha ao carregar biblioteca: {str(e)}",
                config_key="lib_path",
                details={"library_path": lib_path, "original_error": str(e)}
            ) from e

    def _setup_signatures(self) -> None:
        self.lib.CreatePool.argtypes = [ctypes.c_char_p]; self.lib.CreatePool.restype = ctypes.c_char_p
        self.lib.ClosePool.argtypes = [ctypes.c_char_p]
        self.lib.ExecuteSQL_async.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, CALLBACK_FUNC_TYPE, ctypes.c_char_p]
        if hasattr(self.lib, 'BeginTransaction'):
            self.lib.BeginTransaction.argtypes = [ctypes.c_char_p]; self.lib.BeginTransaction.restype = ctypes.c_char_p
        if hasattr(self.lib, 'CommitTransaction'):
            self.lib.CommitTransaction.argtypes = [ctypes.c_char_p]
        if hasattr(self.lib, 'RollbackTransaction'):
            self.lib.RollbackTransaction.argtypes = [ctypes.c_char_p]
        if hasattr(self.lib, 'FreeCString'):
            self.lib.FreeCString.argtypes = [ctypes.c_char_p]

    def _verify_library_functions(self) -> None:
        required_functions = ['CreatePool', 'ClosePool', 'ExecuteSQL_async']
        missing = [func for func in required_functions if not hasattr(self.lib, func)]
        if missing:
            raise ConfigurationError(
                f"Funções essenciais faltando na DLL: {', '.join(missing)}",
                config_key="dll_functions",
                details={"missing_functions": missing, "required_functions": required_functions}
            )

    def _create_pool_sync(self) -> PoolID:
        params_json = json.dumps(self.conn_params).encode('utf-8')
        pool_id_raw = self.lib.CreatePool(params_json)
        pool_id_str = pool_id_raw.decode('utf-8')
        if pool_id_str.startswith('{'):
            raise PoolError(
                f"Falha ao criar pool: {pool_id_str}",
                pool_id=pool_id_str,
                details={"connection_params": self.conn_params}
            )
        return pool_id_str

    async def close(self) -> None:
        """Fecha o pool de conexões de forma assíncrona."""
        if self.pool_id:
            try:
                bridge_logger.info(f"Fechando pool {self.pool_id}")
                # Se a operação de fechamento for síncrona, remova o await abaixo
                self.lib.ClosePool(self.pool_id.encode('utf-8'))
                self.pool_id = None
                self._explicitly_closed = True
                bridge_logger.info("Pool fechado com sucesso")
            except Exception as e:
                error_msg = f"Erro ao fechar pool: {str(e)}"
                bridge_logger.error(error_msg)
                raise

    def __del__(self):
        # Cleanup síncrono para evitar problemas com __del__ e métodos async
        if hasattr(self, 'pool_id') and self.pool_id and not getattr(self, '_explicitly_closed', False):
            import warnings
            warnings.warn(
                f"SQLBridge não foi fechado explicitamente. Pool {self.pool_id} será fechado automaticamente. "
                "Use 'await bridge.close()' para fechamento explícito.",
                ResourceWarning,
                stacklevel=2
            )
            try:
                # Fechamento síncrono do pool
                if hasattr(self, 'lib') and self.lib:
                    self.lib.ClosePool(self.pool_id.encode('utf-8'))
                self.pool_id = None
            except Exception:
                # Ignorar erros no __del__ para evitar problemas de cleanup
                pass

    async def _execute_async(
        self, 
        req: Dict[str, Any], 
        tx_id: Optional[TransactionID] = None
    ) -> DatabaseResult:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        request_id = str(uuid.uuid4())
        
        _active_futures[request_id] = (future, self, loop)
        bridge_logger.debug(f"Future criado para request_id: {request_id}")
        
        try:
            req['driver'] = self.driver
            req_json = json.dumps(req).encode('utf-8')
            pool_id_enc = self.pool_id.encode('utf-8')
            tx_id_enc = tx_id.encode('utf-8') if tx_id else b""
            request_id_enc = request_id.encode('utf-8')
            
            bridge_logger.debug(f"Enviando requisição para DLL (req_id: {request_id}, op: {req.get('operation')})")
            self.lib.ExecuteSQL_async(pool_id_enc, req_json, tx_id_enc, _global_callback_c, request_id_enc)
            
            try:
                result = await asyncio.wait_for(future, timeout=30.0)
                bridge_logger.debug(f"Requisição concluída (req_id: {request_id})")
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f"Timeout na requisição {request_id}") from None
        finally:
            _active_futures.pop(request_id, None)
            bridge_logger.debug(f"Future removido para request_id: {request_id}")

    def _process_where(self, where: Optional[QueryCondition]) -> Dict[str, Any]:
        if where is None: return {}
        if isinstance(where, Q): return where.to_dict()
        if isinstance(where, dict): return {'connector': 'AND', 'children': [where]}
        raise TypeError(f"Argumento 'where' deve ser um dict ou objeto Q.")

    async def select(
        self, 
        table: str, 
        fields: Optional[QueryFields] = None, 
        where: Optional[QueryCondition] = None, 
        joins: Optional[QueryJoins] = None
    ) -> QueryResults:
        req = {
            "operation": "select", 
            "table": table, 
            "fields": fields or ['*'], 
            "where_q": self._process_where(where), 
            "joins": joins or []
        }
        return await self._execute_async(req)
        
    async def insert(self, table: str, data: Dict[str, Any]) -> DatabaseResult:
        req = {"operation": "insert", "table": table, "data": data}
        return await self._execute_async(req)
        
    async def update(
        self, 
        table: str, 
        data: Dict[str, Any], 
        where: Optional[QueryCondition] = None
    ) -> DatabaseResult:
        req = {
            "operation": "update", 
            "table": table, 
            "data": data, 
            "where_q": self._process_where(where)
        }
        return await self._execute_async(req)

    async def delete(
        self, 
        table: str, 
        where: Optional[QueryCondition] = None
    ) -> DatabaseResult:
        req = {
            "operation": "delete", 
            "table": table, 
            "where_q": self._process_where(where)
        }
        return await self._execute_async(req)
        
    async def exec(
        self, 
        sql: str, 
        params: Optional[List[Any]] = None, 
        expect_result: bool = False
    ) -> DatabaseResult:
        req = {
            "operation": "exec", 
            "sql": sql, 
            "params": params or [], 
            "expect_result": expect_result
        }
        return await self._execute_async(req)

    def transaction(self):
        return Transaction(self)

    def get_logger(self) -> logging.Logger:
        """Retorna o logger da bridge para configuração personalizada"""
        return bridge_logger
    
    def _init_advanced_pool(self, config: Dict[str, Any]) -> None:
        """Inicializa o pool avançado de conexões."""
        try:
            self._advanced_pool = AdvancedConnectionPool(
                min_connections=config.get('min_connections', 1),
                max_connections=config.get('max_connections', 10),
                connection_timeout=config.get('connection_timeout', 30.0),
                idle_timeout=config.get('idle_timeout', 300.0),
                max_lifetime=config.get('max_lifetime', 3600.0),
                health_check_interval=config.get('health_check_interval', 60.0),
                health_check_timeout=config.get('health_check_timeout', 5.0),
                retry_attempts=config.get('retry_attempts', 3),
                retry_delay=config.get('retry_delay', 1.0),
                logger=bridge_logger
            )
            bridge_logger.info("Pool avançado de conexões inicializado")
        except Exception as e:
            bridge_logger.error(f"Erro ao inicializar pool avançado: {e}")
            raise ConfigurationError(f"Falha ao inicializar pool avançado: {e}")
    
    def _init_query_cache(self, config: Dict[str, Any]) -> None:
        """Inicializa o sistema de cache de queries."""
        try:
            self._cache_manager = CacheManager(logger=bridge_logger)
            
            # Criar cache padrão
            default_cache = self._cache_manager.create_cache(
                name="default",
                max_size=config.get('max_size', 1000),
                default_ttl=config.get('default_ttl', 300.0),
                policy=CachePolicy(config.get('policy', 'lru')),
                set_as_default=True
            )
            
            bridge_logger.info("Sistema de cache de queries inicializado")
        except Exception as e:
            bridge_logger.error(f"Erro ao inicializar cache de queries: {e}")
            raise ConfigurationError(f"Falha ao inicializar cache de queries: {e}")
    
    def _init_migrations(self, migrations_dir: str) -> None:
        """Inicializa o sistema de migrations."""
        try:
            self._migration_manager = MigrationManager(
                migrations_dir=migrations_dir,
                logger=bridge_logger
            )
            self._migration_manager.set_bridge(self)
            bridge_logger.info(f"Sistema de migrations inicializado em: {migrations_dir}")
        except Exception as e:
            bridge_logger.error(f"Erro ao inicializar migrations: {e}")
            raise ConfigurationError(f"Falha ao inicializar migrations: {e}")
    
    def _init_profiling(self, config: Dict[str, Any]) -> None:
        """Inicializa o sistema de profiling."""
        try:
            self._profiler = Profiler(
                enable_profiling=config.get('enable_profiling', True),
                enable_metrics=config.get('enable_metrics', True),
                log_level=config.get('log_level', 'INFO'),
                logger=bridge_logger
            )
            bridge_logger.info("Sistema de profiling inicializado")
        except Exception as e:
            bridge_logger.error(f"Erro ao inicializar profiling: {e}")
            raise ConfigurationError(f"Falha ao inicializar profiling: {e}")
    
    def _init_optimizations(self, config: Dict[str, Any]) -> None:
        """Inicializa o sistema de otimizações."""
        try:
            optimization_config = OptimizationConfig(
                enable_json_optimization=config.get('enable_json_optimization', True),
                enable_lazy_loading=config.get('enable_lazy_loading', True),
                enable_caching=config.get('enable_caching', True),
                enable_compression=config.get('enable_compression', False),
                cache_size=config.get('cache_size', 1000),
                compression_level=config.get('compression_level', 6)
            )
            
            self._optimizer = PerformanceOptimizer(optimization_config)
            bridge_logger.info("Sistema de otimizações inicializado")
        except Exception as e:
            bridge_logger.error(f"Erro ao inicializar otimizações: {e}")
            raise ConfigurationError(f"Falha ao inicializar otimizações: {e}")
    
    def _init_dashboard(self, config: Dict[str, Any]) -> None:
        """Inicializa o dashboard de métricas."""
        try:
            if not self._profiler or not self._optimizer:
                raise ConfigurationError("Profiler e Optimizer devem estar habilitados para o dashboard")
            
            dashboard_config = DashboardConfig(
                enable_real_time=config.get('enable_real_time', True),
                update_interval=config.get('update_interval', 1.0),
                max_history=config.get('max_history', 1000),
                enable_export=config.get('enable_export', True),
                export_formats=config.get('export_formats', ['json', 'csv']),
                enable_alerts=config.get('enable_alerts', True),
                alert_thresholds=config.get('alert_thresholds', {
                    'slow_query': 1.0,
                    'high_error_rate': 0.1,
                    'low_cache_hit_rate': 0.7
                })
            )
            
            self._dashboard = MetricsDashboard(
                profiler=self._profiler,
                optimizer=self._optimizer,
                config=dashboard_config
            )
            bridge_logger.info("Dashboard de métricas inicializado")
        except Exception as e:
            bridge_logger.error(f"Erro ao inicializar dashboard: {e}")
            raise ConfigurationError(f"Falha ao inicializar dashboard: {e}")
    
    # Advanced Pool Methods
    async def get_advanced_pool_metrics(self) -> Optional[Dict[str, Any]]:
        """Retorna métricas do pool avançado."""
        if self._advanced_pool:
            return self._advanced_pool.get_metrics()
        return None
    
    async def get_advanced_pool_health(self) -> Optional[Dict[str, Any]]:
        """Retorna status de saúde do pool avançado."""
        if self._advanced_pool:
            return self._advanced_pool.get_health_status()
        return None
    
    # Cache Methods
    async def cache_query(
        self, 
        query: str, 
        params: Optional[List[Any]] = None,
        table: Optional[str] = None,
        operation: Optional[str] = None,
        ttl: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Any]:
        """Obtém resultado de query do cache."""
        if not self._cache_manager:
            return None
        
        cache = self._cache_manager.get_cache()
        if not cache:
            return None
        
        return await cache.get(query, params, table, operation)
    
    async def store_query_result(
        self, 
        query: str, 
        result: Any,
        params: Optional[List[Any]] = None,
        table: Optional[str] = None,
        operation: Optional[str] = None,
        ttl: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """Armazena resultado de query no cache."""
        if not self._cache_manager:
            return
        
        cache = self._cache_manager.get_cache()
        if not cache:
            return
        
        await cache.set(query, result, params, table, operation, ttl, tags)
    
    async def invalidate_cache(
        self, 
        query: Optional[str] = None,
        table: Optional[str] = None,
        operation: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Invalida entradas do cache."""
        if not self._cache_manager:
            return 0
        
        cache = self._cache_manager.get_cache()
        if not cache:
            return 0
        
        return await cache.invalidate(query, table, operation, tags)
    
    async def clear_cache(self) -> int:
        """Limpa todo o cache."""
        if not self._cache_manager:
            return 0
        
        cache = self._cache_manager.get_cache()
        if not cache:
            return 0
        
        return await cache.clear()
    
    def get_cache_metrics(self) -> Optional[Dict[str, Any]]:
        """Retorna métricas do cache."""
        if not self._cache_manager:
            return None
        
        cache = self._cache_manager.get_cache()
        if not cache:
            return None
        
        return cache.get_metrics()
    
    # Migration Methods
    async def create_migration(
        self, 
        name: str, 
        up_sql: str, 
        down_sql: str,
        dependencies: Optional[List[str]] = None
    ) -> Optional[str]:
        """Cria uma nova migration."""
        if not self._migration_manager:
            raise ConfigurationError("Sistema de migrations não inicializado")
        
        return self._migration_manager.create_migration(name, up_sql, down_sql, dependencies)
    
    async def run_migrations(self, target_version: Optional[str] = None) -> List[str]:
        """Executa migrations pendentes."""
        if not self._migration_manager:
            raise ConfigurationError("Sistema de migrations não inicializado")
        
        return await self._migration_manager.migrate(target_version)
    
    async def rollback_migrations(self, target_version: Optional[str] = None) -> List[str]:
        """Reverte migrations aplicadas."""
        if not self._migration_manager:
            raise ConfigurationError("Sistema de migrations não inicializado")
        
        return await self._migration_manager.rollback(target_version)
    
    async def get_migration_status(self, version: str) -> Optional[str]:
        """Retorna o status de uma migration."""
        if not self._migration_manager:
            return None
        
        status = await self._migration_manager.get_migration_status(version)
        return status.value if status else None
    
    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """Retorna o histórico de migrations."""
        if not self._migration_manager:
            return []
        
        history = await self._migration_manager.get_migration_history()
        return [
            {
                'version': record.version,
                'name': record.name,
                'status': record.status.value,
                'applied_at': record.applied_at,
                'rolled_back_at': record.rolled_back_at,
                'error_message': record.error_message,
                'dependencies': record.dependencies
            }
            for record in history
        ]
    
    def list_migrations(self) -> List[str]:
        """Lista todas as migrations disponíveis."""
        if not self._migration_manager:
            return []
        
        return self._migration_manager.list_migrations()
    
    def get_migration_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Retorna informações sobre uma migration específica."""
        if not self._migration_manager:
            return None
        
        migration = self._migration_manager.get_migration_info(version)
        return migration if migration else None
    
    # Profiling and Performance Methods
    def get_profiler(self) -> Optional[Profiler]:
        """Retorna a instância do profiler."""
        return self._profiler
    
    def get_optimizer(self) -> Optional[PerformanceOptimizer]:
        """Retorna a instância do otimizador."""
        return self._optimizer
    
    def get_dashboard(self) -> Optional[MetricsDashboard]:
        """Retorna a instância do dashboard."""
        return self._dashboard
    
    async def start_dashboard(self) -> None:
        """Inicia o dashboard de métricas."""
        if self._dashboard:
            await self._dashboard.start()
    
    async def stop_dashboard(self) -> None:
        """Para o dashboard de métricas."""
        if self._dashboard:
            await self._dashboard.stop()
    
    def get_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """Retorna métricas de performance."""
        if not self._profiler:
            return None
        return self._profiler.get_metrics_summary()
    
    def get_query_metrics(self) -> Optional[Dict[str, Any]]:
        """Retorna métricas de queries."""
        if not self._profiler:
            return None
        return self._profiler.get_query_metrics_summary()
    
    def get_optimization_stats(self) -> Optional[Dict[str, Any]]:
        """Retorna estatísticas de otimização."""
        if not self._optimizer:
            return None
        return self._optimizer.get_stats()
    
    def get_dashboard_summary(self) -> Optional[Dict[str, Any]]:
        """Retorna resumo do dashboard."""
        if not self._dashboard:
            return None
        return self._dashboard.get_summary()
    
    def clear_all_metrics(self) -> None:
        """Limpa todas as métricas."""
        if self._profiler:
            self._profiler.clear_metrics()
        if self._optimizer:
            self._optimizer.clear_stats()
        if self._dashboard:
            self._dashboard.clear_alerts()

class Transaction:
    def __init__(self, bridge: SQLBridge) -> None:
        self._bridge = bridge
        self.tx_id: Optional[TransactionID] = None
        self.tx_bridge: Optional['TransactionalBridge'] = None

    async def __aenter__(self) -> 'TransactionalBridge':
        if not hasattr(self._bridge.lib, 'BeginTransaction'):
            raise RuntimeError("DLL não suporta transações")
        response_raw = self._bridge.lib.BeginTransaction(self._bridge.pool_id.encode('utf-8'))
        self.tx_id = response_raw.decode('utf-8')
        if self.tx_id.startswith('{'):
            raise ConnectionError(f"Falha ao iniciar transação: {self.tx_id}")
        bridge_logger.info(f"Transação iniciada com ID: {self.tx_id}")
        self.tx_bridge = TransactionalBridge(self._bridge, self.tx_id)
        return self.tx_bridge

    async def __aexit__(
        self, 
        exc_type: Optional[type], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[Any]
    ) -> None:
        if not self.tx_id: return
        try:
            if exc_type is not None:
                bridge_logger.warning(f"Rollback da transação {self.tx_id} devido a erro")
                if hasattr(self._bridge.lib, 'RollbackTransaction'):
                    self._bridge.lib.RollbackTransaction(self.tx_id.encode('utf-8'))
            else:
                bridge_logger.info(f"Commit da transação {self.tx_id}")
                if hasattr(self._bridge.lib, 'CommitTransaction'):
                    self._bridge.lib.CommitTransaction(self.tx_id.encode('utf-8'))
        finally:
            self.tx_id = None

class TransactionalBridge:
    def __init__(self, original_bridge: SQLBridge, tx_id: TransactionID) -> None:
        self._bridge = original_bridge
        self._tx_id = tx_id
        bridge_logger.debug(f"Bridge transacional criada para tx_id: {tx_id}")

    async def select(
        self, 
        table: str, 
        fields: Optional[QueryFields] = None, 
        where: Optional[QueryCondition] = None, 
        joins: Optional[QueryJoins] = None
    ) -> QueryResults:
        return await self._bridge._execute_async({
            "operation": "select", 
            "table": table, 
            "fields": fields or ['*'], 
            "where_q": self._bridge._process_where(where), 
            "joins": joins or []
        }, self._tx_id)
    async def update(
        self, 
        table: str, 
        data: Dict[str, Any], 
        where: Optional[QueryCondition] = None
    ) -> DatabaseResult:
        return await self._bridge._execute_async({
            "operation": "update", 
            "table": table, 
            "data": data, 
            "where_q": self._bridge._process_where(where)
        }, self._tx_id)
    async def delete(
        self, 
        table: str, 
        where: Optional[QueryCondition] = None
    ) -> DatabaseResult:
        return await self._bridge._execute_async({
            "operation": "delete", 
            "table": table, 
            "where_q": self._bridge._process_where(where)
        }, self._tx_id)
    async def exec(
        self, 
        sql: str, 
        params: Optional[List[Any]] = None, 
        expect_result: bool = False
    ) -> DatabaseResult:
        return await self._bridge._execute_async({
            "operation": "exec", 
            "sql": sql, 
            "params": params or [], 
            "expect_result": expect_result
        }, self._tx_id)
