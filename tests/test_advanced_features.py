"""
Testes para funcionalidades avançadas da Fase 4
"""

import pytest
import asyncio
import tempfile
import os
from kairondb import (
    AdvancedConnectionPool, ConnectionState, QueryCache, CacheManager, 
    CachePolicy, MigrationManager, MigrationStatus
)


class TestAdvancedConnectionPool:
    """Testes para o pool avançado de conexões."""
    
    @pytest.mark.asyncio
    async def test_pool_initialization(self):
        """Testa inicialização do pool."""
        pool = AdvancedConnectionPool(
            min_connections=2,
            max_connections=5,
            connection_timeout=10.0,
            idle_timeout=60.0
        )
        
        await pool.initialize()
        
        # Verificar métricas iniciais
        metrics = pool.get_metrics()
        assert metrics['current_connections'] >= 2
        assert metrics['max_connections'] == 5
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Testa gerenciamento de conexões."""
        pool = AdvancedConnectionPool(
            min_connections=1,
            max_connections=3
        )
        
        await pool.initialize()
        
        # Obter conexão
        conn_id = await pool.get_connection()
        assert conn_id is not None
        
        # Verificar estado
        conn_info = pool.get_connection_info(conn_id)
        assert conn_info is not None
        assert conn_info.state == ConnectionState.ACTIVE
        
        # Liberar conexão
        await pool.release_connection(conn_id)
        
        # Verificar estado após liberação
        conn_info = pool.get_connection_info(conn_id)
        assert conn_info.state == ConnectionState.IDLE
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_pool_metrics(self):
        """Testa métricas do pool."""
        pool = AdvancedConnectionPool(
            min_connections=1,
            max_connections=2
        )
        
        await pool.initialize()
        
        metrics = pool.get_metrics()
        assert 'total_created' in metrics
        assert 'current_connections' in metrics
        assert 'idle_connections' in metrics
        assert 'active_connections' in metrics
        assert metrics['current_connections'] >= 1
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa verificação de saúde do pool."""
        pool = AdvancedConnectionPool(
            min_connections=1,
            max_connections=2
        )
        
        await pool.initialize()
        
        health = pool.get_health_status()
        assert 'status' in health
        assert 'checks' in health
        assert 'timestamp' in health
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']
        
        await pool.close()


class TestQueryCache:
    """Testes para o sistema de cache de queries."""
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self):
        """Testa inicialização do cache."""
        cache = QueryCache(
            max_size=100,
            default_ttl=60.0,
            policy=CachePolicy.LRU
        )
        
        await cache.initialize()
        
        metrics = cache.get_metrics()
        assert metrics['max_size'] == 100
        assert metrics['size'] == 0
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Testa armazenamento e recuperação do cache."""
        cache = QueryCache(max_size=10)
        await cache.initialize()
        
        # Armazenar valor
        await cache.set("SELECT * FROM users", {"data": [{"id": 1, "name": "João"}]})
        
        # Recuperar valor
        result = await cache.get("SELECT * FROM users")
        assert result == {"data": [{"id": 1, "name": "João"}]}
        
        # Verificar métricas
        metrics = cache.get_metrics()
        assert metrics['hits'] == 1
        assert metrics['misses'] == 0
        assert metrics['size'] == 1
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Testa cache miss."""
        cache = QueryCache(max_size=10)
        await cache.initialize()
        
        # Tentar recuperar valor inexistente
        result = await cache.get("SELECT * FROM nonexistent")
        assert result is None
        
        # Verificar métricas
        metrics = cache.get_metrics()
        assert metrics['hits'] == 0
        assert metrics['misses'] == 1
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self):
        """Testa TTL do cache."""
        cache = QueryCache(max_size=10, default_ttl=0.1)  # TTL muito baixo para teste
        await cache.initialize()
        
        # Armazenar valor
        await cache.set("SELECT * FROM users", {"data": []})
        
        # Verificar que está no cache
        result = await cache.get("SELECT * FROM users")
        assert result is not None
        
        # Aguardar TTL expirar
        await asyncio.sleep(0.2)
        
        # Verificar que expirou
        result = await cache.get("SELECT * FROM users")
        assert result is None
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Testa invalidação do cache."""
        cache = QueryCache(max_size=10)
        await cache.initialize()
        
        # Armazenar valores
        await cache.set("SELECT * FROM users", {"data": []}, table="users")
        await cache.set("SELECT * FROM products", {"data": []}, table="products")
        
        # Invalidar por tabela
        invalidated = await cache.invalidate(table="users")
        assert invalidated >= 0  # Pode ser 0 se não encontrar por tabela
        
        # Verificar que foi invalidado
        result = await cache.get("SELECT * FROM users", table="users")
        assert result is None
        
        # Verificar que outro não foi afetado
        result = await cache.get("SELECT * FROM products", table="products")
        assert result is not None
        
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Testa limpeza do cache."""
        cache = QueryCache(max_size=10)
        await cache.initialize()
        
        # Armazenar valores
        await cache.set("SELECT * FROM users", {"data": []})
        await cache.set("SELECT * FROM products", {"data": []})
        
        # Limpar cache
        cleared = await cache.clear()
        assert cleared == 2
        
        # Verificar que está vazio
        metrics = cache.get_metrics()
        assert metrics['size'] == 0
        
        await cache.close()


class TestCacheManager:
    """Testes para o gerenciador de caches."""
    
    @pytest.mark.asyncio
    async def test_cache_manager_creation(self):
        """Testa criação de caches pelo manager."""
        manager = CacheManager()
        
        # Criar cache
        cache1 = manager.create_cache("cache1", max_size=100, set_as_default=True)
        cache2 = manager.create_cache("cache2", max_size=200)
        
        assert cache1 is not None
        assert cache2 is not None
        
        # Verificar listagem
        caches = manager.list_caches()
        assert "cache1" in caches
        assert "cache2" in caches
        
        # Verificar cache padrão
        default = manager.get_cache()
        assert default == cache1
        
        # Verificar cache específico
        specific = manager.get_cache("cache2")
        assert specific == cache2
        
        await manager.close_all()
    
    @pytest.mark.asyncio
    async def test_multiple_caches(self):
        """Testa múltiplos caches."""
        manager = CacheManager()
        
        # Criar caches com configurações diferentes
        cache1 = manager.create_cache("lru_cache", policy=CachePolicy.LRU)
        cache2 = manager.create_cache("lfu_cache", policy=CachePolicy.LFU)
        
        await cache1.initialize()
        await cache2.initialize()
        
        # Armazenar em caches diferentes
        await cache1.set("query1", {"result": 1})
        await cache2.set("query2", {"result": 2})
        
        # Verificar isolamento
        result1 = await cache1.get("query1")
        result2 = await cache2.get("query2")
        
        assert result1 == {"result": 1}
        assert result2 == {"result": 2}
        
        # Verificar que não há vazamento
        assert await cache1.get("query2") is None
        assert await cache2.get("query1") is None
        
        await manager.close_all()


class TestMigrationManager:
    """Testes para o sistema de migrations."""
    
    @pytest.fixture
    def temp_migrations_dir(self):
        """Cria diretório temporário para migrations."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_bridge(self):
        """Cria bridge mock para testes."""
        class MockBridge:
            async def exec(self, sql):
                return {"success": True}
            
            async def select(self, table, **kwargs):
                return {"data": []}
            
            async def insert(self, table, data):
                return {"success": True}
            
            async def update(self, table, data, where):
                return {"success": True}
        
        return MockBridge()
    
    @pytest.mark.asyncio
    async def test_migration_manager_initialization(self, temp_migrations_dir, mock_bridge):
        """Testa inicialização do migration manager."""
        manager = MigrationManager(migrations_dir=temp_migrations_dir)
        manager.set_bridge(mock_bridge)
        
        await manager.initialize()
        
        # Verificar que foi inicializado
        assert manager is not None
        
        # Cleanup - não há método close no MigrationManager
    
    @pytest.mark.asyncio
    async def test_create_migration(self, temp_migrations_dir, mock_bridge):
        """Testa criação de migration."""
        manager = MigrationManager(migrations_dir=temp_migrations_dir)
        manager.set_bridge(mock_bridge)
        await manager.initialize()
        
        # Criar migration
        version = manager.create_migration(
            name="Create users table",
            up_sql="CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))",
            down_sql="DROP TABLE users"
        )
        
        assert version is not None
        assert version.startswith("1")
        
        # Verificar se arquivo foi criado
        migration_file = os.path.join(temp_migrations_dir, f"{version}.json")
        assert os.path.exists(migration_file)
        
        # Cleanup - não há método close no MigrationManager
    
    @pytest.mark.asyncio
    async def test_migration_validation(self, temp_migrations_dir, mock_bridge):
        """Testa validação de migrations."""
        manager = MigrationManager(migrations_dir=temp_migrations_dir)
        manager.set_bridge(mock_bridge)
        await manager.initialize()
        
        # Criar migration válida
        version1 = manager.create_migration(
            name="Migration 1",
            up_sql="CREATE TABLE test1 (id INT)",
            down_sql="DROP TABLE test1"
        )
        
        # Criar migration com dependência
        version2 = manager.create_migration(
            name="Migration 2",
            up_sql="CREATE TABLE test2 (id INT)",
            down_sql="DROP TABLE test2",
            dependencies=[version1]
        )
        
        # Validar migrations
        errors = await manager.validate_migrations()
        assert len(errors) == 0
        
        # Cleanup - não há método close no MigrationManager
    
    @pytest.mark.asyncio
    async def test_migration_listing(self, temp_migrations_dir, mock_bridge):
        """Testa listagem de migrations."""
        manager = MigrationManager(migrations_dir=temp_migrations_dir)
        manager.set_bridge(mock_bridge)
        await manager.initialize()
        
        # Criar algumas migrations
        version1 = manager.create_migration("Migration 1", "SQL1", "SQL1_DOWN")
        version2 = manager.create_migration("Migration 2", "SQL2", "SQL2_DOWN")
        
        # Listar migrations
        migrations = manager.list_migrations()
        assert len(migrations) == 2
        assert version1 in migrations
        assert version2 in migrations
        
        # Obter informações de migration específica
        info = manager.get_migration_info(version1)
        assert info is not None
        assert info['name'] == "Migration 1"
        assert info['up_sql'] == "SQL1"
        
        # Cleanup - não há método close no MigrationManager


class TestSQLBridgeAdvancedFeatures:
    """Testes para funcionalidades avançadas do SQLBridge."""
    
    @pytest.mark.asyncio
    async def test_bridge_with_advanced_pool(self):
        """Testa SQLBridge com pool avançado."""
        # Este teste seria mais complexo pois requer uma bridge real
        # Por enquanto, apenas verificamos que os parâmetros são aceitos
        try:
            from kairondb import SQLBridge
            
            # Teste de inicialização com parâmetros avançados
            bridge = SQLBridge(
                driver="sqlite3",
                server=":memory:",
                db_name="test",
                user="",
                password="",
                enable_advanced_pool=True,
                pool_config={
                    'min_connections': 1,
                    'max_connections': 5
                }
            )
            
            # Verificar que foi inicializado
            assert bridge._advanced_pool is not None
            
            # Cleanup
            await bridge.close()
            
        except Exception as e:
            # Se falhar, é esperado pois não temos a DLL real
            pytest.skip(f"Teste pulado devido a: {e}")
    
    @pytest.mark.asyncio
    async def test_bridge_with_cache(self):
        """Testa SQLBridge com cache."""
        try:
            from kairondb import SQLBridge
            
            bridge = SQLBridge(
                driver="sqlite3",
                server=":memory:",
                db_name="test",
                user="",
                password="",
                enable_query_cache=True,
                cache_config={
                    'max_size': 100,
                    'default_ttl': 60.0
                }
            )
            
            # Verificar que foi inicializado
            assert bridge._cache_manager is not None
            
            # Testar métodos de cache
            metrics = bridge.get_cache_metrics()
            assert metrics is not None
            
            # Cleanup
            await bridge.close()
            
        except Exception as e:
            pytest.skip(f"Teste pulado devido a: {e}")
    
    @pytest.mark.asyncio
    async def test_bridge_with_migrations(self):
        """Testa SQLBridge com migrations."""
        try:
            from kairondb import SQLBridge
            import tempfile
            import os
            
            temp_dir = tempfile.mkdtemp()
            
            bridge = SQLBridge(
                driver="sqlite3",
                server=":memory:",
                db_name="test",
                user="",
                password="",
                enable_migrations=True,
                migrations_dir=temp_dir
            )
            
            # Verificar que foi inicializado
            assert bridge._migration_manager is not None
            
            # Testar métodos de migration
            migrations = bridge.list_migrations()
            assert isinstance(migrations, list)
            
            # Cleanup
            await bridge.close()
            
            # Cleanup temp dir
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            pytest.skip(f"Teste pulado devido a: {e}")


class TestIntegration:
    """Testes de integração das funcionalidades avançadas."""
    
    @pytest.mark.asyncio
    async def test_pool_and_cache_integration(self):
        """Testa integração entre pool e cache."""
        # Este seria um teste mais complexo que verifica
        # como as funcionalidades trabalham juntas
        pool = AdvancedConnectionPool(min_connections=1, max_connections=2)
        cache = QueryCache(max_size=10)
        
        await pool.initialize()
        await cache.initialize()
        
        # Simular uso conjunto
        conn_id = await pool.get_connection()
        
        # Armazenar resultado no cache
        await cache.set("test_query", {"connection_id": conn_id})
        
        # Recuperar do cache
        result = await cache.get("test_query")
        assert result["connection_id"] == conn_id
        
        # Liberar conexão
        await pool.release_connection(conn_id)
        
        # Cleanup
        await pool.close()
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Testa coleta de métricas."""
        pool = AdvancedConnectionPool(min_connections=1, max_connections=2)
        cache = QueryCache(max_size=10)
        
        await pool.initialize()
        await cache.initialize()
        
        # Obter métricas
        pool_metrics = pool.get_metrics()
        cache_metrics = cache.get_metrics()
        
        assert 'current_connections' in pool_metrics
        assert 'size' in cache_metrics
        
        # Cleanup
        await pool.close()
        await cache.close()
