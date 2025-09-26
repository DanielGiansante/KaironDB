"""
Sistema de Profiling e Métricas para KaironDB
"""

import time
import cProfile
import pstats
import io
import asyncio
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
import logging
from .typing import Metrics, LogLevel
from .exceptions import ConfigurationError


@dataclass
class PerformanceMetrics:
    """Métricas de performance de uma operação."""
    operation: str
    start_time: float
    end_time: float
    duration: float
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    query_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryMetrics:
    """Métricas específicas de queries."""
    query: str
    table: str
    operation: str
    execution_time: float
    rows_affected: int = 0
    rows_returned: int = 0
    cache_hit: bool = False
    error: Optional[str] = None
    params: Optional[List[Any]] = None


class Profiler:
    """Sistema de profiling para KaironDB."""
    
    def __init__(
        self,
        enable_profiling: bool = True,
        enable_metrics: bool = True,
        log_level: LogLevel = "INFO",
        logger: Optional[logging.Logger] = None
    ):
        self.enable_profiling = enable_profiling
        self.enable_metrics = enable_metrics
        self.logger = logger or logging.getLogger('kairondb.profiling')
        
        # Profiling data
        self._profiler: Optional[cProfile.Profile] = None
        self._profile_data: Dict[str, Any] = {}
        
        # Metrics data
        self._metrics: List[PerformanceMetrics] = []
        self._query_metrics: List[QueryMetrics] = []
        self._counters: Dict[str, int] = {
            'total_queries': 0,
            'total_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'connections_created': 0,
            'connections_closed': 0
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_metric_collected: Optional[Callable[[PerformanceMetrics], None]] = None
        self._on_query_metric_collected: Optional[Callable[[QueryMetrics], None]] = None
    
    def set_callbacks(
        self,
        on_metric_collected: Optional[Callable[[PerformanceMetrics], None]] = None,
        on_query_metric_collected: Optional[Callable[[QueryMetrics], None]] = None
    ) -> None:
        """Define callbacks para coleta de métricas."""
        self._on_metric_collected = on_metric_collected
        self._on_query_metric_collected = on_query_metric_collected
    
    def start_profiling(self, operation: str = "default") -> None:
        """Inicia o profiling de uma operação."""
        if not self.enable_profiling:
            return
        
        with self._lock:
            self._profiler = cProfile.Profile()
            self._profiler.enable()
            self._profile_data[operation] = {
                'start_time': time.time(),
                'profiler': self._profiler
            }
    
    def stop_profiling(self, operation: str = "default") -> Dict[str, Any]:
        """Para o profiling e retorna os dados."""
        if not self.enable_profiling or not self._profiler:
            return {}
        
        with self._lock:
            if operation not in self._profile_data:
                return {}
            
            self._profiler.disable()
            profile_data = self._profile_data[operation]
            profile_data['end_time'] = time.time()
            profile_data['duration'] = profile_data['end_time'] - profile_data['start_time']
            
            # Capturar estatísticas
            s = io.StringIO()
            ps = pstats.Stats(self._profiler, stream=s).sort_stats('cumulative')
            ps.print_stats()
            
            profile_data['stats'] = s.getvalue()
            profile_data['profiler_stats'] = ps.stats
            
            # Limpar
            del self._profile_data[operation]
            self._profiler = None
            
            return profile_data
    
    def collect_metric(
        self,
        operation: str,
        start_time: float,
        end_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetrics:
        """Coleta uma métrica de performance."""
        if not self.enable_metrics:
            return None
        
        duration = end_time - start_time
        metric = PerformanceMetrics(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics.append(metric)
            
            # Manter apenas as últimas 1000 métricas
            if len(self._metrics) > 1000:
                self._metrics = self._metrics[-1000:]
        
        if self._on_metric_collected:
            self._on_metric_collected(metric)
        
        return metric
    
    def collect_query_metric(
        self,
        query: str,
        table: str,
        operation: str,
        execution_time: float,
        rows_affected: int = 0,
        rows_returned: int = 0,
        cache_hit: bool = False,
        error: Optional[str] = None,
        params: Optional[List[Any]] = None
    ) -> QueryMetrics:
        """Coleta uma métrica específica de query."""
        if not self.enable_metrics:
            return None
        
        metric = QueryMetrics(
            query=query,
            table=table,
            operation=operation,
            execution_time=execution_time,
            rows_affected=rows_affected,
            rows_returned=rows_returned,
            cache_hit=cache_hit,
            error=error,
            params=params
        )
        
        with self._lock:
            self._query_metrics.append(metric)
            
            # Manter apenas as últimas 1000 métricas
            if len(self._query_metrics) > 1000:
                self._query_metrics = self._query_metrics[-1000:]
        
        if self._on_query_metric_collected:
            self._on_query_metric_collected(metric)
        
        return metric
    
    def increment_counter(self, counter_name: str, value: int = 1) -> None:
        """Incrementa um contador."""
        with self._lock:
            if counter_name in self._counters:
                self._counters[counter_name] += value
            else:
                self._counters[counter_name] = value
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das métricas coletadas."""
        with self._lock:
            if not self._metrics:
                return {
                    'total_metrics': 0,
                    'counters': self._counters.copy(),
                    'average_duration': 0,
                    'total_duration': 0
                }
            
            total_duration = sum(m.duration for m in self._metrics)
            average_duration = total_duration / len(self._metrics)
            
            # Agrupar por operação
            operations = {}
            for metric in self._metrics:
                op = metric.operation
                if op not in operations:
                    operations[op] = {
                        'count': 0,
                        'total_duration': 0,
                        'average_duration': 0,
                        'min_duration': float('inf'),
                        'max_duration': 0
                    }
                
                ops = operations[op]
                ops['count'] += 1
                ops['total_duration'] += metric.duration
                ops['min_duration'] = min(ops['min_duration'], metric.duration)
                ops['max_duration'] = max(ops['max_duration'], metric.duration)
            
            # Calcular médias
            for op_data in operations.values():
                op_data['average_duration'] = op_data['total_duration'] / op_data['count']
                if op_data['min_duration'] == float('inf'):
                    op_data['min_duration'] = 0
            
            return {
                'total_metrics': len(self._metrics),
                'counters': self._counters.copy(),
                'average_duration': average_duration,
                'total_duration': total_duration,
                'operations': operations,
                'query_metrics_count': len(self._query_metrics)
            }
    
    def get_query_metrics_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das métricas de queries."""
        with self._lock:
            if not self._query_metrics:
                return {
                    'total_queries': 0,
                    'average_execution_time': 0,
                    'tables': {},
                    'operations': {}
                }
            
            total_execution_time = sum(m.execution_time for m in self._query_metrics)
            average_execution_time = total_execution_time / len(self._query_metrics)
            
            # Agrupar por tabela
            tables = {}
            for metric in self._query_metrics:
                table = metric.table
                if table not in tables:
                    tables[table] = {
                        'count': 0,
                        'total_time': 0,
                        'cache_hits': 0,
                        'errors': 0
                    }
                
                tables[table]['count'] += 1
                tables[table]['total_time'] += metric.execution_time
                if metric.cache_hit:
                    tables[table]['cache_hits'] += 1
                if metric.error:
                    tables[table]['errors'] += 1
            
            # Agrupar por operação
            operations = {}
            for metric in self._query_metrics:
                op = metric.operation
                if op not in operations:
                    operations[op] = {
                        'count': 0,
                        'total_time': 0,
                        'cache_hits': 0,
                        'errors': 0
                    }
                
                operations[op]['count'] += 1
                operations[op]['total_time'] += metric.execution_time
                if metric.cache_hit:
                    operations[op]['cache_hits'] += 1
                if metric.error:
                    operations[op]['errors'] += 1
            
            return {
                'total_queries': len(self._query_metrics),
                'average_execution_time': average_execution_time,
                'tables': tables,
                'operations': operations
            }
    
    def clear_metrics(self) -> None:
        """Limpa todas as métricas coletadas."""
        with self._lock:
            self._metrics.clear()
            self._query_metrics.clear()
            self._counters = {
                'total_queries': 0,
                'total_operations': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'errors': 0,
                'connections_created': 0,
                'connections_closed': 0
            }
    
    def export_metrics(self, format: str = "json") -> Union[Dict[str, Any], str]:
        """Exporta métricas em diferentes formatos."""
        summary = self.get_metrics_summary()
        query_summary = self.get_query_metrics_summary()
        
        data = {
            'performance_metrics': summary,
            'query_metrics': query_summary,
            'exported_at': time.time()
        }
        
        if format == "json":
            return data
        elif format == "csv":
            # Implementar exportação CSV se necessário
            return str(data)
        else:
            raise ValueError(f"Formato não suportado: {format}")


def profile_operation(operation_name: str = None):
    """Decorator para profiling de operações."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Encontrar instância do profiler nos args
            profiler = None
            for arg in args:
                if hasattr(arg, '_profiler'):
                    profiler = arg._profiler
                    break
            
            if not profiler:
                return await func(*args, **kwargs)
            
            op_name = operation_name or func.__name__
            profiler.start_profiling(op_name)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                profiler.stop_profiling(op_name)
                profiler.collect_metric(op_name, start_time, end_time)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Encontrar instância do profiler nos args
            profiler = None
            for arg in args:
                if hasattr(arg, '_profiler'):
                    profiler = arg._profiler
                    break
            
            if not profiler:
                return func(*args, **kwargs)
            
            op_name = operation_name or func.__name__
            profiler.start_profiling(op_name)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                profiler.stop_profiling(op_name)
                profiler.collect_metric(op_name, start_time, end_time)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def profile_context(profiler: Profiler, operation: str):
    """Context manager para profiling assíncrono."""
    profiler.start_profiling(operation)
    start_time = time.time()
    
    try:
        yield
    finally:
        end_time = time.time()
        profiler.stop_profiling(operation)
        profiler.collect_metric(operation, start_time, end_time)


@contextmanager
def profile_sync_context(profiler: Profiler, operation: str):
    """Context manager para profiling síncrono."""
    profiler.start_profiling(operation)
    start_time = time.time()
    
    try:
        yield
    finally:
        end_time = time.time()
        profiler.stop_profiling(operation)
        profiler.collect_metric(operation, start_time, end_time)
