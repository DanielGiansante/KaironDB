"""
Dashboard de Métricas para KaironDB
"""

import time
import json
import asyncio
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from .profiling import Profiler, PerformanceMetrics, QueryMetrics
from .optimizations import PerformanceOptimizer
from .exceptions import ConfigurationError


@dataclass
class DashboardConfig:
    """Configuração do dashboard."""
    enable_real_time: bool = True
    update_interval: float = 1.0  # segundos
    max_history: int = 1000
    enable_export: bool = True
    export_formats: List[str] = field(default_factory=lambda: ['json', 'csv'])
    enable_alerts: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'slow_query': 1.0,  # 1 segundo
        'high_error_rate': 0.1,  # 10%
        'low_cache_hit_rate': 0.7  # 70%
    })


@dataclass
class Alert:
    """Alerta do sistema."""
    id: str
    type: str
    severity: str  # info, warning, error, critical
    message: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardData:
    """Dados do dashboard."""
    timestamp: float
    performance_metrics: Dict[str, Any]
    query_metrics: Dict[str, Any]
    optimization_stats: Dict[str, Any]
    system_health: Dict[str, Any]
    alerts: List[Alert]


class MetricsDashboard:
    """Dashboard de métricas em tempo real."""
    
    def __init__(
        self,
        profiler: Profiler,
        optimizer: PerformanceOptimizer,
        config: DashboardConfig = None
    ):
        self.profiler = profiler
        self.optimizer = optimizer
        self.config = config or DashboardConfig()
        self.logger = logging.getLogger('kairondb.dashboard')
        
        # Estado do dashboard
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
        
        # Histórico de dados
        self._history: List[DashboardData] = []
        self._alerts: List[Alert] = []
        
        # Callbacks
        self._on_alert: Optional[Callable[[Alert], None]] = None
        self._on_data_update: Optional[Callable[[DashboardData], None]] = None
    
    def set_callbacks(
        self,
        on_alert: Optional[Callable[[Alert], None]] = None,
        on_data_update: Optional[Callable[[DashboardData], None]] = None
    ) -> None:
        """Define callbacks para eventos do dashboard."""
        self._on_alert = on_alert
        self._on_data_update = on_data_update
    
    async def start(self) -> None:
        """Inicia o dashboard."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._update_loop())
        self.logger.info("Dashboard iniciado")
    
    async def stop(self) -> None:
        """Para o dashboard."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Dashboard parado")
    
    async def _update_loop(self) -> None:
        """Loop principal de atualização do dashboard."""
        while self._running:
            try:
                await self._update_data()
                await asyncio.sleep(self.config.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de atualização: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_data(self) -> None:
        """Atualiza os dados do dashboard."""
        # Coletar métricas
        performance_metrics = self.profiler.get_metrics_summary()
        query_metrics = self.profiler.get_query_metrics_summary()
        optimization_stats = self.optimizer.get_stats()
        
        # Calcular saúde do sistema
        system_health = self._calculate_system_health(
            performance_metrics, query_metrics, optimization_stats
        )
        
        # Verificar alertas
        await self._check_alerts(performance_metrics, query_metrics, system_health)
        
        # Criar dados do dashboard
        data = DashboardData(
            timestamp=time.time(),
            performance_metrics=performance_metrics,
            query_metrics=query_metrics,
            optimization_stats=optimization_stats,
            system_health=system_health,
            alerts=self._alerts.copy()
        )
        
        # Armazenar no histórico
        with self._lock:
            self._history.append(data)
            if len(self._history) > self.config.max_history:
                self._history = self._history[-self.config.max_history:]
        
        # Callback de atualização
        if self._on_data_update:
            self._on_data_update(data)
    
    def _calculate_system_health(
        self,
        performance_metrics: Dict[str, Any],
        query_metrics: Dict[str, Any],
        optimization_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcula a saúde do sistema."""
        health = {
            'status': 'healthy',
            'score': 100,
            'checks': {}
        }
        
        # Verificar performance
        avg_duration = performance_metrics.get('average_duration', 0)
        if avg_duration > 1.0:
            health['checks']['performance'] = 'warning'
            health['score'] -= 20
        else:
            health['checks']['performance'] = 'ok'
        
        # Verificar queries
        total_queries = query_metrics.get('total_queries', 0)
        if total_queries > 0:
            avg_query_time = query_metrics.get('average_execution_time', 0)
            if avg_query_time > 0.5:
                health['checks']['queries'] = 'warning'
                health['score'] -= 15
            else:
                health['checks']['queries'] = 'ok'
        else:
            health['checks']['queries'] = 'ok'
        
        # Verificar cache
        cache_hits = optimization_stats.get('cache_hits', 0)
        cache_misses = optimization_stats.get('cache_misses', 0)
        if cache_hits + cache_misses > 0:
            hit_rate = cache_hits / (cache_hits + cache_misses)
            if hit_rate < 0.7:
                health['checks']['cache'] = 'warning'
                health['score'] -= 10
            else:
                health['checks']['cache'] = 'ok'
        else:
            health['checks']['cache'] = 'ok'
        
        # Determinar status geral
        if health['score'] < 50:
            health['status'] = 'critical'
        elif health['score'] < 80:
            health['status'] = 'warning'
        
        return health
    
    async def _check_alerts(
        self,
        performance_metrics: Dict[str, Any],
        query_metrics: Dict[str, Any],
        system_health: Dict[str, Any]
    ) -> None:
        """Verifica e gera alertas."""
        if not self.config.enable_alerts:
            return
        
        # Verificar queries lentas
        avg_query_time = query_metrics.get('average_execution_time', 0)
        if avg_query_time > self.config.alert_thresholds['slow_query']:
            await self._create_alert(
                'slow_query',
                'warning',
                f"Queries lentas detectadas: {avg_query_time:.2f}s"
            )
        
        # Verificar taxa de erro
        total_queries = query_metrics.get('total_queries', 0)
        if total_queries > 0:
            error_count = sum(
                op.get('errors', 0) for op in query_metrics.get('operations', {}).values()
            )
            error_rate = error_count / total_queries
            if error_rate > self.config.alert_thresholds['high_error_rate']:
                await self._create_alert(
                    'high_error_rate',
                    'error',
                    f"Alta taxa de erro: {error_rate:.2%}"
                )
        
        # Verificar taxa de cache
        cache_hits = self.optimizer.get_stats().get('cache_hits', 0)
        cache_misses = self.optimizer.get_stats().get('cache_misses', 0)
        if cache_hits + cache_misses > 0:
            hit_rate = cache_hits / (cache_hits + cache_misses)
            if hit_rate < self.config.alert_thresholds['low_cache_hit_rate']:
                await self._create_alert(
                    'low_cache_hit_rate',
                    'warning',
                    f"Baixa taxa de cache hit: {hit_rate:.2%}"
                )
    
    async def _create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Cria um novo alerta."""
        alert = Alert(
            id=f"{alert_type}_{int(time.time())}",
            type=alert_type,
            severity=severity,
            message=message,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self._alerts.append(alert)
            # Manter apenas os últimos 100 alertas
            if len(self._alerts) > 100:
                self._alerts = self._alerts[-100:]
        
        # Callback de alerta
        if self._on_alert:
            self._on_alert(alert)
        
        self.logger.warning(f"Alerta {severity}: {message}")
    
    def get_current_data(self) -> Optional[DashboardData]:
        """Retorna os dados atuais do dashboard."""
        with self._lock:
            return self._history[-1] if self._history else None
    
    def get_history(self, minutes: int = 60) -> List[DashboardData]:
        """Retorna o histórico dos últimos N minutos."""
        cutoff_time = time.time() - (minutes * 60)
        
        with self._lock:
            return [
                data for data in self._history
                if data.timestamp >= cutoff_time
            ]
    
    def get_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Retorna alertas, opcionalmente filtrados por severidade."""
        with self._lock:
            if severity:
                return [alert for alert in self._alerts if alert.severity == severity]
            return self._alerts.copy()
    
    def clear_alerts(self) -> None:
        """Limpa todos os alertas."""
        with self._lock:
            self._alerts.clear()
    
    def export_data(self, format: str = "json", minutes: int = 60) -> Union[Dict[str, Any], str]:
        """Exporta dados do dashboard."""
        history = self.get_history(minutes)
        alerts = self.get_alerts()
        
        data = {
            'exported_at': time.time(),
            'period_minutes': minutes,
            'history': [
                {
                    'timestamp': data.timestamp,
                    'performance_metrics': data.performance_metrics,
                    'query_metrics': data.query_metrics,
                    'optimization_stats': data.optimization_stats,
                    'system_health': data.system_health
                }
                for data in history
            ],
            'alerts': [
                {
                    'id': alert.id,
                    'type': alert.type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp,
                    'metadata': alert.metadata
                }
                for alert in alerts
            ]
        }
        
        if format == "json":
            return data
        elif format == "csv":
            # Implementar exportação CSV se necessário
            return str(data)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna um resumo do dashboard."""
        current_data = self.get_current_data()
        if not current_data:
            return {'status': 'no_data'}
        
        return {
            'status': current_data.system_health['status'],
            'score': current_data.system_health['score'],
            'total_queries': current_data.query_metrics.get('total_queries', 0),
            'average_query_time': current_data.query_metrics.get('average_execution_time', 0),
            'total_operations': current_data.performance_metrics.get('total_metrics', 0),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'active_alerts': len([a for a in self._alerts if a.severity in ['warning', 'error', 'critical']]),
            'uptime': time.time() - (self._history[0].timestamp if self._history else time.time())
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calcula a taxa de cache hit."""
        stats = self.optimizer.get_stats()
        hits = stats.get('cache_hits', 0)
        misses = stats.get('cache_misses', 0)
        
        if hits + misses == 0:
            return 0.0
        
        return hits / (hits + misses)
