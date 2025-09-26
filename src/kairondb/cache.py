"""
Sistema de Cache de Queries para KaironDB
"""

import time
import hashlib
import json
import asyncio
import logging
from typing import Dict, Any, Optional, Union, Callable, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from .typing import CacheKey, CacheValue, CacheTTL, QueryResults, DatabaseResult
from .exceptions import ConfigurationError


class CachePolicy(Enum):
    """Políticas de cache."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    MANUAL = "manual"  # Controle manual


@dataclass
class CacheEntry:
    """Entrada no cache."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueryCache:
    """Sistema de cache para queries com TTL e invalidação."""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 300.0,  # 5 minutos
        policy: CachePolicy = CachePolicy.LRU,
        enable_compression: bool = False,
        enable_serialization: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.policy = policy
        self.enable_compression = enable_compression
        self.enable_serialization = enable_serialization
        self.logger = logger or logging.getLogger('kairondb.cache')
        
        # Estado do cache
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # Para LRU
        self._access_counts: Dict[str, int] = {}  # Para LFU
        self._tags: Dict[str, List[str]] = {}  # Mapeamento tag -> keys
        
        # Métricas
        self._metrics = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'invalidations': 0,
            'size': 0,
            'max_size': max_size,
            'hit_rate': 0.0
        }
        
        # Controle
        self._lock = asyncio.Lock()
        self._closed = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._on_cache_hit: Optional[Callable[[str], None]] = None
        self._on_cache_miss: Optional[Callable[[str], None]] = None
        self._on_cache_eviction: Optional[Callable[[str], None]] = None
        self._on_cache_invalidation: Optional[Callable[[str], None]] = None
    
    def set_callbacks(
        self,
        on_cache_hit: Optional[Callable[[str], None]] = None,
        on_cache_miss: Optional[Callable[[str], None]] = None,
        on_cache_eviction: Optional[Callable[[str], None]] = None,
        on_cache_invalidation: Optional[Callable[[str], None]] = None
    ) -> None:
        """Define callbacks para eventos do cache."""
        self._on_cache_hit = on_cache_hit
        self._on_cache_miss = on_cache_miss
        self._on_cache_eviction = on_cache_eviction
        self._on_cache_invalidation = on_cache_invalidation
    
    async def initialize(self) -> None:
        """Inicializa o cache."""
        if self._closed:
            raise ConfigurationError("Cache já foi fechado")
        
        self.logger.info(f"Cache inicializado com tamanho máximo {self.max_size}")
        
        # Iniciar task de limpeza
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def _generate_key(
        self, 
        query: str, 
        params: Optional[List[Any]] = None,
        table: Optional[str] = None,
        operation: Optional[str] = None
    ) -> str:
        """Gera uma chave única para a query."""
        key_data = {
            'query': query,
            'params': params or [],
            'table': table,
            'operation': operation
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(
        self, 
        query: str, 
        params: Optional[List[Any]] = None,
        table: Optional[str] = None,
        operation: Optional[str] = None
    ) -> Optional[Any]:
        """Obtém um valor do cache."""
        if self._closed:
            return None
        
        key = self._generate_key(query, params, table, operation)
        
        async with self._lock:
            if key not in self._cache:
                self._metrics['misses'] += 1
                self._update_hit_rate()
                
                if self._on_cache_miss:
                    self._on_cache_miss(key)
                
                return None
            
            entry = self._cache[key]
            
            # Verificar TTL
            if entry.ttl and time.time() - entry.created_at > entry.ttl:
                await self._remove_entry(key, "TTL expirado")
                self._metrics['misses'] += 1
                self._update_hit_rate()
                
                if self._on_cache_miss:
                    self._on_cache_miss(key)
                
                return None
            
            # Atualizar estatísticas de acesso
            entry.last_accessed = time.time()
            entry.access_count += 1
            self._metrics['hits'] += 1
            self._update_hit_rate()
            
            # Atualizar ordem de acesso para LRU
            if self.policy == CachePolicy.LRU:
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
            
            # Atualizar contadores para LFU
            if self.policy == CachePolicy.LFU:
                self._access_counts[key] = entry.access_count
            
            if self._on_cache_hit:
                self._on_cache_hit(key)
            
            return entry.value
    
    async def set(
        self, 
        query: str, 
        value: Any,
        params: Optional[List[Any]] = None,
        table: Optional[str] = None,
        operation: Optional[str] = None,
        ttl: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """Armazena um valor no cache."""
        if self._closed:
            return
        
        key = self._generate_key(query, params, table, operation)
        ttl = ttl or self.default_ttl
        tags = tags or []
        
        async with self._lock:
            # Verificar se precisa evictar
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_entry()
            
            # Criar entrada
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl=ttl,
                tags=tags,
                metadata={
                    'table': table,
                    'operation': operation,
                    'query': query,
                    'params': params
                }
            )
            
            # Armazenar
            self._cache[key] = entry
            
            # Atualizar índices
            if self.policy == CachePolicy.LRU:
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
            
            if self.policy == CachePolicy.LFU:
                self._access_counts[key] = 0
            
            # Atualizar tags
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = []
                if key not in self._tags[tag]:
                    self._tags[tag].append(key)
            
            self._metrics['size'] = len(self._cache)
    
    async def invalidate(
        self, 
        query: Optional[str] = None,
        table: Optional[str] = None,
        operation: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Invalida entradas do cache baseado em critérios."""
        if self._closed:
            return 0
        
        async with self._lock:
            keys_to_remove = set()
            
            if query:
                # Invalidar por query específica
                key = self._generate_key(query, table=table, operation=operation)
                if key in self._cache:
                    keys_to_remove.add(key)
            
            if table:
                # Invalidar por tabela
                for key, entry in self._cache.items():
                    if entry.metadata.get('table') == table:
                        keys_to_remove.add(key)
            
            if operation:
                # Invalidar por operação
                for key, entry in self._cache.items():
                    if entry.metadata.get('operation') == operation:
                        keys_to_remove.add(key)
            
            if tags:
                # Invalidar por tags
                for tag in tags:
                    if tag in self._tags:
                        keys_to_remove.update(self._tags[tag])
            
            # Remover entradas
            for key in keys_to_remove:
                await self._remove_entry(key, "Invalidação manual")
            
            self._metrics['invalidations'] += len(keys_to_remove)
            
            if self._on_cache_invalidation:
                for key in keys_to_remove:
                    self._on_cache_invalidation(key)
            
            return len(keys_to_remove)
    
    async def clear(self) -> int:
        """Limpa todo o cache."""
        if self._closed:
            return 0
        
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._access_order.clear()
            self._access_counts.clear()
            self._tags.clear()
            self._metrics['size'] = 0
            self._metrics['invalidations'] += count
            
            if self._on_cache_invalidation:
                for _ in range(count):
                    self._on_cache_invalidation("clear")
            
            return count
    
    async def _evict_entry(self) -> None:
        """Remove uma entrada baseado na política de eviction."""
        if not self._cache:
            return
        
        key_to_remove = None
        
        if self.policy == CachePolicy.LRU:
            # Remove o menos recentemente usado
            if self._access_order:
                key_to_remove = self._access_order[0]
        
        elif self.policy == CachePolicy.LFU:
            # Remove o menos frequentemente usado
            if self._access_counts:
                key_to_remove = min(self._access_counts.keys(), key=lambda k: self._access_counts[k])
        
        elif self.policy == CachePolicy.TTL:
            # Remove o mais antigo
            key_to_remove = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        
        else:
            # Política manual - remove aleatoriamente
            key_to_remove = next(iter(self._cache.keys()))
        
        if key_to_remove:
            await self._remove_entry(key_to_remove, "Eviction por política")
    
    async def _remove_entry(self, key: str, reason: str) -> None:
        """Remove uma entrada do cache."""
        if key not in self._cache:
            return
        
        entry = self._cache[key]
        
        # Remover de índices
        if key in self._access_order:
            self._access_order.remove(key)
        
        if key in self._access_counts:
            del self._access_counts[key]
        
        # Remover de tags
        for tag in entry.tags:
            if tag in self._tags and key in self._tags[tag]:
                self._tags[tag].remove(key)
                if not self._tags[tag]:
                    del self._tags[tag]
        
        # Remover entrada
        del self._cache[key]
        self._metrics['size'] = len(self._cache)
        self._metrics['evictions'] += 1
        
        if self._on_cache_eviction:
            self._on_cache_eviction(key)
        
        self.logger.debug(f"Entrada removida do cache: {key} - {reason}")
    
    async def _cleanup_loop(self) -> None:
        """Loop de limpeza de entradas expiradas."""
        while not self._closed:
            try:
                await asyncio.sleep(60)  # Limpeza a cada minuto
                await self._cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no cleanup loop: {e}")
    
    async def _cleanup_expired_entries(self) -> None:
        """Remove entradas expiradas do cache."""
        async with self._lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.ttl and now - entry.created_at > entry.ttl
            ]
        
        for key in expired_keys:
            await self._remove_entry(key, "TTL expirado no cleanup")
    
    def _update_hit_rate(self) -> None:
        """Atualiza a taxa de acerto do cache."""
        total = self._metrics['hits'] + self._metrics['misses']
        if total > 0:
            self._metrics['hit_rate'] = self._metrics['hits'] / total
        else:
            self._metrics['hit_rate'] = 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna as métricas atuais do cache."""
        return self._metrics.copy()
    
    def get_size(self) -> int:
        """Retorna o tamanho atual do cache."""
        return len(self._cache)
    
    def get_entries_by_tag(self, tag: str) -> List[str]:
        """Retorna as chaves de entradas com uma tag específica."""
        return self._tags.get(tag, []).copy()
    
    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Retorna informações sobre uma entrada específica."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        return {
            'key': entry.key,
            'created_at': entry.created_at,
            'last_accessed': entry.last_accessed,
            'access_count': entry.access_count,
            'ttl': entry.ttl,
            'tags': entry.tags.copy(),
            'metadata': entry.metadata.copy()
        }
    
    async def close(self) -> None:
        """Fecha o cache."""
        if self._closed:
            return
        
        self.logger.info("Fechando cache")
        self._closed = True
        
        # Cancelar task de limpeza
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Limpar cache
        await self.clear()
        
        self.logger.info("Cache fechado com sucesso")
    
    def __del__(self):
        """Cleanup final."""
        if not self._closed:
            self.logger.warning("Cache não foi fechado explicitamente")
            self._closed = True


class CacheManager:
    """Gerenciador de múltiplos caches."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('kairondb.cache_manager')
        self._caches: Dict[str, QueryCache] = {}
        self._default_cache: Optional[QueryCache] = None
    
    def create_cache(
        self, 
        name: str, 
        max_size: int = 1000,
        default_ttl: float = 300.0,
        policy: CachePolicy = CachePolicy.LRU,
        set_as_default: bool = False
    ) -> QueryCache:
        """Cria um novo cache."""
        if name in self._caches:
            raise ConfigurationError(f"Cache '{name}' já existe")
        
        cache = QueryCache(
            max_size=max_size,
            default_ttl=default_ttl,
            policy=policy,
            logger=self.logger
        )
        
        self._caches[name] = cache
        
        if set_as_default or self._default_cache is None:
            self._default_cache = cache
        
        return cache
    
    def get_cache(self, name: Optional[str] = None) -> Optional[QueryCache]:
        """Obtém um cache específico ou o padrão."""
        if name is None:
            return self._default_cache
        
        return self._caches.get(name)
    
    def list_caches(self) -> List[str]:
        """Lista todos os caches."""
        return list(self._caches.keys())
    
    async def close_all(self) -> None:
        """Fecha todos os caches."""
        for cache in self._caches.values():
            await cache.close()
        
        self._caches.clear()
        self._default_cache = None
