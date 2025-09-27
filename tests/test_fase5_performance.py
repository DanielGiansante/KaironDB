"""
Testes para Fase 5: Otimizações e Performance
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch
from kairondb import (
    Profiler, PerformanceOptimizer, OptimizationConfig, 
    MetricsDashboard, DashboardConfig, LazyLoader
)


class TestProfiler:
    """Testes para o sistema de profiling."""
    
    @pytest.mark.asyncio
    async def test_profiler_initialization(self):
        """Testa inicialização do profiler."""
        profiler = Profiler(enable_profiling=True, enable_metrics=True)
        
        assert profiler.enable_profiling is True
        assert profiler.enable_metrics is True
        assert profiler._profiler is None
        assert len(profiler._metrics) == 0
    
    @pytest.mark.asyncio
    async def test_profiler_metrics_collection(self):
        """Testa coleta de métricas."""
        profiler = Profiler(enable_profiling=True, enable_metrics=True)
        
        # Simular operação
        start_time = time.time()
        await asyncio.sleep(0.01)
        end_time = time.time()
        
        metric = profiler.collect_metric("test_operation", start_time, end_time)
        
        assert metric is not None
        assert metric.operation == "test_operation"
        assert metric.duration > 0
        assert len(profiler._metrics) == 1
    
    @pytest.mark.asyncio
    async def test_profiler_query_metrics(self):
        """Testa métricas de queries."""
        profiler = Profiler(enable_profiling=True, enable_metrics=True)
        
        query_metric = profiler.collect_query_metric(
            query="SELECT * FROM users",
            table="users",
            operation="select",
            execution_time=0.1,
            rows_returned=10,
            cache_hit=True
        )
        
        assert query_metric is not None
        assert query_metric.query == "SELECT * FROM users"
        assert query_metric.table == "users"
        assert query_metric.operation == "select"
        assert query_metric.execution_time == 0.1
        assert query_metric.rows_returned == 10
        assert query_metric.cache_hit is True
        assert len(profiler._query_metrics) == 1
    
    @pytest.mark.asyncio
    async def test_profiler_counters(self):
        """Testa contadores do profiler."""
        profiler = Profiler(enable_profiling=True, enable_metrics=True)
        
        profiler.increment_counter("total_queries", 5)
        profiler.increment_counter("cache_hits", 3)
        
        assert profiler._counters["total_queries"] == 5
        assert profiler._counters["cache_hits"] == 3
    
    @pytest.mark.asyncio
    async def test_profiler_metrics_summary(self):
        """Testa resumo de métricas."""
        profiler = Profiler(enable_profiling=True, enable_metrics=True)
        
        # Adicionar algumas métricas
        profiler.collect_metric("op1", time.time(), time.time() + 0.1)
        profiler.collect_metric("op2", time.time(), time.time() + 0.2)
        profiler.increment_counter("total_operations", 2)
        
        summary = profiler.get_metrics_summary()
        
        assert summary["total_metrics"] == 2
        assert summary["counters"]["total_operations"] == 2
        assert "operations" in summary
        assert "op1" in summary["operations"]
        assert "op2" in summary["operations"]
    
    @pytest.mark.asyncio
    async def test_profiler_clear_metrics(self):
        """Testa limpeza de métricas."""
        profiler = Profiler(enable_profiling=True, enable_metrics=True)
        
        # Adicionar métricas
        profiler.collect_metric("test", time.time(), time.time() + 0.1)
        profiler.increment_counter("test_counter", 1)
        
        assert len(profiler._metrics) == 1
        assert profiler._counters["test_counter"] == 1
        
        # Limpar
        profiler.clear_metrics()
        
        assert len(profiler._metrics) == 0
        # Verificar que o contador foi resetado para 0
        assert profiler._counters.get("test_counter", 0) == 0


class TestPerformanceOptimizer:
    """Testes para o sistema de otimizações."""
    
    def test_optimizer_initialization(self):
        """Testa inicialização do otimizador."""
        config = OptimizationConfig(
            enable_json_optimization=True,
            enable_lazy_loading=True,
            cache_size=500
        )
        
        optimizer = PerformanceOptimizer(config)
        
        assert optimizer.config.enable_json_optimization is True
        assert optimizer.config.enable_lazy_loading is True
        assert optimizer.config.cache_size == 500
        assert optimizer.serializer is not None
        assert optimizer.query_optimizer is not None
    
    def test_json_serialization_optimization(self):
        """Testa otimização de serialização JSON."""
        config = OptimizationConfig(enable_json_optimization=True)
        optimizer = PerformanceOptimizer(config)
        
        data = {"name": "test", "value": 123, "nested": {"key": "value"}}
        
        # Serializar
        json_str = optimizer.optimize_json_serialization(data)
        assert isinstance(json_str, str)
        
        # Deserializar
        result = optimizer.optimize_json_deserialization(json_str)
        assert result == data
    
    def test_query_optimization(self):
        """Testa otimização de queries."""
        optimizer = PerformanceOptimizer(OptimizationConfig())
        
        query = "SELECT * FROM users WHERE id = ?"
        optimized = optimizer.optimize_query(query, [1])
        
        assert isinstance(optimized, str)
        assert "SELECT" in optimized.upper()
    
    def test_optimizer_stats(self):
        """Testa estatísticas do otimizador."""
        optimizer = PerformanceOptimizer(OptimizationConfig())
        
        # Executar algumas operações
        optimizer.optimize_json_serialization({"test": "data"})
        optimizer.optimize_query("SELECT * FROM test")
        
        stats = optimizer.get_stats()
        
        assert stats["json_serializations"] == 1
        assert stats["query_optimizations"] == 1
    
    def test_optimizer_clear_stats(self):
        """Testa limpeza de estatísticas."""
        optimizer = PerformanceOptimizer(OptimizationConfig())
        
        # Adicionar estatísticas
        optimizer.optimize_json_serialization({"test": "data"})
        
        assert optimizer.get_stats()["json_serializations"] == 1
        
        # Limpar
        optimizer.clear_stats()
        
        assert optimizer.get_stats()["json_serializations"] == 0


class TestLazyLoader:
    """Testes para o sistema de lazy loading."""
    
    def test_lazy_loader_initialization(self):
        """Testa inicialização do lazy loader."""
        def loader():
            return "loaded_value"
        
        lazy_loader = LazyLoader(loader, cache_result=True)
        
        assert lazy_loader._loaded is False
        assert lazy_loader._cached_value is None
    
    def test_lazy_loader_get(self):
        """Testa obtenção de valor com lazy loading."""
        call_count = 0
        
        def loader():
            nonlocal call_count
            call_count += 1
            return f"loaded_value_{call_count}"
        
        lazy_loader = LazyLoader(loader, cache_result=True)
        
        # Primeira chamada deve executar o loader
        result1 = lazy_loader.get()
        assert result1 == "loaded_value_1"
        assert call_count == 1
        assert lazy_loader._loaded is True
        
        # Segunda chamada deve usar cache
        result2 = lazy_loader.get()
        assert result2 == "loaded_value_1"
        assert call_count == 1
    
    def test_lazy_loader_reload(self):
        """Testa recarregamento forçado."""
        call_count = 0
        
        def loader():
            nonlocal call_count
            call_count += 1
            return f"loaded_value_{call_count}"
        
        lazy_loader = LazyLoader(loader, cache_result=True)
        
        # Carregar inicial
        result1 = lazy_loader.get()
        assert result1 == "loaded_value_1"
        
        # Recarregar
        result2 = lazy_loader.reload()
        assert result2 == "loaded_value_2"
        assert call_count == 2
    
    def test_lazy_loader_clear_cache(self):
        """Testa limpeza de cache."""
        call_count = 0
        
        def loader():
            nonlocal call_count
            call_count += 1
            return f"loaded_value_{call_count}"
        
        lazy_loader = LazyLoader(loader, cache_result=True)
        
        # Carregar
        result1 = lazy_loader.get()
        assert lazy_loader._loaded is True
        
        # Limpar cache
        lazy_loader.clear_cache()
        assert lazy_loader._loaded is False
        assert lazy_loader._cached_value is None
        
        # Carregar novamente
        result2 = lazy_loader.get()
        assert result2 == "loaded_value_2"


class TestMetricsDashboard:
    """Testes para o dashboard de métricas."""
    
    @pytest.fixture
    def mock_profiler(self):
        """Mock do profiler para testes."""
        profiler = Mock()
        profiler.get_metrics_summary.return_value = {
            'total_metrics': 10,
            'average_duration': 0.1,
            'counters': {'total_queries': 5}
        }
        profiler.get_query_metrics_summary.return_value = {
            'total_queries': 5,
            'average_execution_time': 0.05,
            'tables': {'users': {'count': 3}},
            'operations': {'select': {'count': 3}}
        }
        return profiler
    
    @pytest.fixture
    def mock_optimizer(self):
        """Mock do otimizador para testes."""
        optimizer = Mock()
        optimizer.get_stats.return_value = {
            'cache_hits': 3,
            'cache_misses': 2,
            'json_serializations': 5
        }
        return optimizer
    
    @pytest.mark.asyncio
    async def test_dashboard_initialization(self, mock_profiler, mock_optimizer):
        """Testa inicialização do dashboard."""
        config = DashboardConfig(enable_real_time=True, update_interval=0.1)
        
        dashboard = MetricsDashboard(mock_profiler, mock_optimizer, config)
        
        assert dashboard.profiler == mock_profiler
        assert dashboard.optimizer == mock_optimizer
        assert dashboard.config.enable_real_time is True
        assert dashboard._running is False
    
    @pytest.mark.asyncio
    async def test_dashboard_start_stop(self, mock_profiler, mock_optimizer):
        """Testa início e parada do dashboard."""
        config = DashboardConfig(enable_real_time=True, update_interval=0.1)
        dashboard = MetricsDashboard(mock_profiler, mock_optimizer, config)
        
        # Iniciar
        await dashboard.start()
        assert dashboard._running is True
        
        # Aguardar um pouco
        await asyncio.sleep(0.2)
        
        # Parar
        await dashboard.stop()
        assert dashboard._running is False
    
    @pytest.mark.asyncio
    async def test_dashboard_data_update(self, mock_profiler, mock_optimizer):
        """Testa atualização de dados do dashboard."""
        config = DashboardConfig(enable_real_time=False)  # Desabilitar para teste manual
        dashboard = MetricsDashboard(mock_profiler, mock_optimizer, config)
        
        # Atualizar dados manualmente
        await dashboard._update_data()
        
        # Verificar se os dados foram coletados
        current_data = dashboard.get_current_data()
        assert current_data is not None
        assert current_data.performance_metrics is not None
        assert current_data.query_metrics is not None
        assert current_data.optimization_stats is not None
        assert current_data.system_health is not None
    
    def test_dashboard_system_health_calculation(self, mock_profiler, mock_optimizer):
        """Testa cálculo de saúde do sistema."""
        config = DashboardConfig()
        dashboard = MetricsDashboard(mock_profiler, mock_optimizer, config)
        
        performance_metrics = {
            'average_duration': 0.5,
            'total_metrics': 10
        }
        query_metrics = {
            'total_queries': 5,
            'average_execution_time': 0.1
        }
        optimization_stats = {
            'cache_hits': 3,
            'cache_misses': 1
        }
        
        health = dashboard._calculate_system_health(
            performance_metrics, query_metrics, optimization_stats
        )
        
        assert 'status' in health
        assert 'score' in health
        assert 'checks' in health
        assert health['score'] > 0
    
    def test_dashboard_export_data(self, mock_profiler, mock_optimizer):
        """Testa exportação de dados."""
        config = DashboardConfig()
        dashboard = MetricsDashboard(mock_profiler, mock_optimizer, config)
        
        # Adicionar alguns dados de teste
        dashboard._history.append(Mock(timestamp=time.time()))
        dashboard._alerts.append(Mock(
            id="test_alert",
            type="test",
            severity="warning",
            message="Test alert",
            timestamp=time.time(),
            metadata={}
        ))
        
        # Exportar
        data = dashboard.export_data("json", minutes=60)
        
        assert 'exported_at' in data
        assert 'history' in data
        assert 'alerts' in data
        assert len(data['history']) == 1
        assert len(data['alerts']) == 1
    
    def test_dashboard_summary(self, mock_profiler, mock_optimizer):
        """Testa resumo do dashboard."""
        config = DashboardConfig()
        dashboard = MetricsDashboard(mock_profiler, mock_optimizer, config)
        
        # Adicionar dados de teste com estrutura correta
        from kairondb.dashboard import DashboardData
        mock_data = Mock(spec=DashboardData)
        mock_data.timestamp = time.time()
        mock_data.system_health = {'status': 'healthy', 'score': 100}
        mock_data.query_metrics = {'total_queries': 5, 'average_execution_time': 0.1}
        mock_data.performance_metrics = {'total_metrics': 10}
        
        dashboard._history.append(mock_data)
        
        summary = dashboard.get_summary()
        
        assert 'status' in summary
        assert 'score' in summary
        assert 'total_queries' in summary
        assert 'average_query_time' in summary


class TestIntegration:
    """Testes de integração para Fase 5."""
    
    @pytest.mark.asyncio
    async def test_profiler_and_optimizer_integration(self):
        """Testa integração entre profiler e otimizador."""
        profiler = Profiler(enable_profiling=True, enable_metrics=True)
        optimizer = PerformanceOptimizer(OptimizationConfig())
        
        # Simular operação com profiling
        start_time = time.time()
        
        # Otimizar serialização
        data = {"test": "data"}
        json_str = optimizer.optimize_json_serialization(data)
        
        end_time = time.time()
        
        # Coletar métrica
        profiler.collect_metric("json_serialization", start_time, end_time)
        
        # Verificar métricas
        metrics = profiler.get_metrics_summary()
        stats = optimizer.get_stats()
        
        assert metrics["total_metrics"] == 1
        assert stats["json_serializations"] == 1
    
    @pytest.mark.asyncio
    async def test_dashboard_with_real_data(self):
        """Testa dashboard com dados reais."""
        profiler = Profiler(enable_profiling=True, enable_metrics=True)
        optimizer = PerformanceOptimizer(OptimizationConfig())
        config = DashboardConfig(enable_real_time=False)
        
        dashboard = MetricsDashboard(profiler, optimizer, config)
        
        # Simular algumas operações
        profiler.collect_metric("test_op", time.time(), time.time() + 0.1)
        profiler.collect_query_metric("SELECT * FROM test", "test", "select", 0.05)
        optimizer.optimize_json_serialization({"test": "data"})
        
        # Atualizar dashboard
        await dashboard._update_data()
        
        # Verificar dados
        current_data = dashboard.get_current_data()
        assert current_data is not None
        
        summary = dashboard.get_summary()
        assert summary["total_queries"] == 1
        assert summary["total_operations"] == 1
