#!/usr/bin/env python3
"""
Testes reais com bancos de dados SQL Server e PostgreSQL
"""

import pytest
import asyncio
import time
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kairondb.bridge import SQLBridge
from kairondb.models import Model
from kairondb.fields import StringField, IntegerField, FloatField

class User(Model):
    """Modelo de usuário para testes"""
    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(max_length=100, required=True)
    email = StringField(max_length=100, required=True)
    age = IntegerField()

class Product(Model):
    """Modelo de produto para testes"""
    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(max_length=100, required=True)
    price = FloatField()
    category = StringField(max_length=50)

class TestRealDatabases:
    """Classe base para testes com bancos reais"""
    
    @pytest.fixture
    def postgres_bridge(self):
        """Bridge para PostgreSQL"""
        return SQLBridge(
            driver="postgres",
            server="localhost",
            db_name="kairondb_test",
            user="kairondb",
            password="KaironDB123!"
        )
    
    @pytest.fixture
    def sqlserver_bridge(self):
        """Bridge para SQL Server"""
        return SQLBridge(
            driver="sqlserver",
            server="localhost",
            db_name="kairondb_test",
            user="sa",
            password="KaironDB123!"
        )
    
    @pytest.fixture
    def mysql_bridge(self):
        """Bridge para MySQL"""
        return SQLBridge(
            driver="mysql",
            server="localhost",
            db_name="kairondb_test",
            user="kairondb",
            password="KaironDB123!"
        )

class TestPostgreSQL(TestRealDatabases):
    """Testes específicos para PostgreSQL"""
    
    @pytest.mark.asyncio
    async def test_postgres_connection(self, postgres_bridge):
        """Testa conexão com PostgreSQL"""
        await postgres_bridge.connect()
        assert postgres_bridge.is_connected()
        await postgres_bridge.close()
    
    @pytest.mark.asyncio
    async def test_postgres_crud_operations(self, postgres_bridge):
        """Testa operações CRUD no PostgreSQL"""
        await postgres_bridge.connect()
        
        # CREATE
        await postgres_bridge.create_table("test_users", {
            "id": "SERIAL PRIMARY KEY",
            "name": "VARCHAR(100) NOT NULL",
            "email": "VARCHAR(100) UNIQUE NOT NULL",
            "age": "INTEGER"
        })
        
        # INSERT
        result = await postgres_bridge.insert("test_users", {
            "name": "João Silva",
            "email": "joao@test.com",
            "age": 30
        })
        assert result is not None
        
        # SELECT
        users = await postgres_bridge.select("test_users")
        assert len(users) == 1
        assert users[0]["name"] == "João Silva"
        assert users[0]["email"] == "joao@test.com"
        assert users[0]["age"] == 30
        
        # UPDATE
        await postgres_bridge.update("test_users", 
                                   {"age": 31}, 
                                   {"email": "joao@test.com"})
        
        # Verificar UPDATE
        users = await postgres_bridge.select("test_users")
        assert users[0]["age"] == 31
        
        # DELETE
        await postgres_bridge.delete("test_users", {"email": "joao@test.com"})
        
        # Verificar DELETE
        users = await postgres_bridge.select("test_users")
        assert len(users) == 0
        
        await postgres_bridge.close()
    
    @pytest.mark.asyncio
    async def test_postgres_models(self, postgres_bridge):
        """Testa modelos no PostgreSQL"""
        await postgres_bridge.connect()
        
        # Criar usuário
        user = User(name="Maria Santos", email="maria@test.com", age=25)
        await user.save(postgres_bridge)
        
        # Consultar usuários
        users = await User.select(postgres_bridge)
        assert len(users) == 1
        assert users[0].name == "Maria Santos"
        assert users[0].email == "maria@test.com"
        assert users[0].age == 25
        
        # Atualizar usuário
        user = users[0]
        user.age = 26
        await user.update()
        
        # Verificar atualização
        users = await User.select(postgres_bridge)
        assert users[0].age == 26
        
        # Deletar usuário
        await user.delete()
        
        # Verificar deleção
        users = await User.select(postgres_bridge)
        assert len(users) == 0
        
        await postgres_bridge.close()
    
    @pytest.mark.asyncio
    async def test_postgres_performance(self, postgres_bridge):
        """Testa performance do PostgreSQL"""
        await postgres_bridge.connect()
        
        # Criar tabela
        await postgres_bridge.create_table("performance_test", {
            "id": "SERIAL PRIMARY KEY",
            "name": "VARCHAR(100)",
            "value": "INTEGER"
        })
        
        # Teste de inserção em lote
        start_time = time.time()
        for i in range(1000):
            await postgres_bridge.insert("performance_test", {
                "name": f"Item {i}",
                "value": i
            })
        insert_time = time.time() - start_time
        
        # Teste de consulta
        start_time = time.time()
        results = await postgres_bridge.select("performance_test")
        select_time = time.time() - start_time
        
        assert len(results) == 1000
        print(f"PostgreSQL - 1000 inserções: {insert_time:.2f}s")
        print(f"PostgreSQL - 1000 consultas: {select_time:.2f}s")
        
        await postgres_bridge.close()

class TestSQLServer(TestRealDatabases):
    """Testes específicos para SQL Server"""
    
    @pytest.mark.asyncio
    async def test_sqlserver_connection(self, sqlserver_bridge):
        """Testa conexão com SQL Server"""
        await sqlserver_bridge.connect()
        assert sqlserver_bridge.is_connected()
        await sqlserver_bridge.close()
    
    @pytest.mark.asyncio
    async def test_sqlserver_crud_operations(self, sqlserver_bridge):
        """Testa operações CRUD no SQL Server"""
        await sqlserver_bridge.connect()
        
        # CREATE
        await sqlserver_bridge.create_table("test_users", {
            "id": "INT IDENTITY(1,1) PRIMARY KEY",
            "name": "NVARCHAR(100) NOT NULL",
            "email": "NVARCHAR(100) UNIQUE NOT NULL",
            "age": "INT"
        })
        
        # INSERT
        result = await sqlserver_bridge.insert("test_users", {
            "name": "Pedro Costa",
            "email": "pedro@test.com",
            "age": 35
        })
        assert result is not None
        
        # SELECT
        users = await sqlserver_bridge.select("test_users")
        assert len(users) == 1
        assert users[0]["name"] == "Pedro Costa"
        assert users[0]["email"] == "pedro@test.com"
        assert users[0]["age"] == 35
        
        # UPDATE
        await sqlserver_bridge.update("test_users", 
                                    {"age": 36}, 
                                    {"email": "pedro@test.com"})
        
        # Verificar UPDATE
        users = await sqlserver_bridge.select("test_users")
        assert users[0]["age"] == 36
        
        # DELETE
        await sqlserver_bridge.delete("test_users", {"email": "pedro@test.com"})
        
        # Verificar DELETE
        users = await sqlserver_bridge.select("test_users")
        assert len(users) == 0
        
        await sqlserver_bridge.close()
    
    @pytest.mark.asyncio
    async def test_sqlserver_models(self, sqlserver_bridge):
        """Testa modelos no SQL Server"""
        await sqlserver_bridge.connect()
        
        # Criar usuário
        user = User(name="Ana Lima", email="ana@test.com", age=28)
        await user.save(sqlserver_bridge)
        
        # Consultar usuários
        users = await User.select(sqlserver_bridge)
        assert len(users) == 1
        assert users[0].name == "Ana Lima"
        assert users[0].email == "ana@test.com"
        assert users[0].age == 28
        
        # Atualizar usuário
        user = users[0]
        user.age = 29
        await user.update()
        
        # Verificar atualização
        users = await User.select(sqlserver_bridge)
        assert users[0].age == 29
        
        # Deletar usuário
        await user.delete()
        
        # Verificar deleção
        users = await User.select(sqlserver_bridge)
        assert len(users) == 0
        
        await sqlserver_bridge.close()
    
    @pytest.mark.asyncio
    async def test_sqlserver_performance(self, sqlserver_bridge):
        """Testa performance do SQL Server"""
        await sqlserver_bridge.connect()
        
        # Criar tabela
        await sqlserver_bridge.create_table("performance_test", {
            "id": "INT IDENTITY(1,1) PRIMARY KEY",
            "name": "NVARCHAR(100)",
            "value": "INT"
        })
        
        # Teste de inserção em lote
        start_time = time.time()
        for i in range(1000):
            await sqlserver_bridge.insert("performance_test", {
                "name": f"Item {i}",
                "value": i
            })
        insert_time = time.time() - start_time
        
        # Teste de consulta
        start_time = time.time()
        results = await sqlserver_bridge.select("performance_test")
        select_time = time.time() - start_time
        
        assert len(results) == 1000
        print(f"SQL Server - 1000 inserções: {insert_time:.2f}s")
        print(f"SQL Server - 1000 consultas: {select_time:.2f}s")
        
        await sqlserver_bridge.close()

class TestMySQL(TestRealDatabases):
    """Testes específicos para MySQL"""
    
    @pytest.mark.asyncio
    async def test_mysql_connection(self, mysql_bridge):
        """Testa conexão com MySQL"""
        await mysql_bridge.connect()
        assert mysql_bridge.is_connected()
        await mysql_bridge.close()
    
    @pytest.mark.asyncio
    async def test_mysql_crud_operations(self, mysql_bridge):
        """Testa operações CRUD no MySQL"""
        await mysql_bridge.connect()
        
        # CREATE
        await mysql_bridge.create_table("test_users", {
            "id": "INT AUTO_INCREMENT PRIMARY KEY",
            "name": "VARCHAR(100) NOT NULL",
            "email": "VARCHAR(100) UNIQUE NOT NULL",
            "age": "INT"
        })
        
        # INSERT
        result = await mysql_bridge.insert("test_users", {
            "name": "Carlos Oliveira",
            "email": "carlos@test.com",
            "age": 42
        })
        assert result is not None
        
        # SELECT
        users = await mysql_bridge.select("test_users")
        assert len(users) == 1
        assert users[0]["name"] == "Carlos Oliveira"
        assert users[0]["email"] == "carlos@test.com"
        assert users[0]["age"] == 42
        
        # UPDATE
        await mysql_bridge.update("test_users", 
                                {"age": 43}, 
                                {"email": "carlos@test.com"})
        
        # Verificar UPDATE
        users = await mysql_bridge.select("test_users")
        assert users[0]["age"] == 43
        
        # DELETE
        await mysql_bridge.delete("test_users", {"email": "carlos@test.com"})
        
        # Verificar DELETE
        users = await mysql_bridge.select("test_users")
        assert len(users) == 0
        
        await mysql_bridge.close()
    
    @pytest.mark.asyncio
    async def test_mysql_models(self, mysql_bridge):
        """Testa modelos no MySQL"""
        await mysql_bridge.connect()
        
        # Criar usuário
        user = User(name="Lucia Ferreira", email="lucia@test.com", age=33)
        await user.save(mysql_bridge)
        
        # Consultar usuários
        users = await User.select(mysql_bridge)
        assert len(users) == 1
        assert users[0].name == "Lucia Ferreira"
        assert users[0].email == "lucia@test.com"
        assert users[0].age == 33
        
        # Atualizar usuário
        user = users[0]
        user.age = 34
        await user.update()
        
        # Verificar atualização
        users = await User.select(mysql_bridge)
        assert users[0].age == 34
        
        # Deletar usuário
        await user.delete()
        
        # Verificar deleção
        users = await User.select(mysql_bridge)
        assert len(users) == 0
        
        await mysql_bridge.close()
    
    @pytest.mark.asyncio
    async def test_mysql_performance(self, mysql_bridge):
        """Testa performance do MySQL"""
        await mysql_bridge.connect()
        
        # Criar tabela
        await mysql_bridge.create_table("performance_test", {
            "id": "INT AUTO_INCREMENT PRIMARY KEY",
            "name": "VARCHAR(100)",
            "value": "INT"
        })
        
        # Teste de inserção em lote
        start_time = time.time()
        for i in range(1000):
            await mysql_bridge.insert("performance_test", {
                "name": f"Item {i}",
                "value": i
            })
        insert_time = time.time() - start_time
        
        # Teste de consulta
        start_time = time.time()
        results = await mysql_bridge.select("performance_test")
        select_time = time.time() - start_time
        
        assert len(results) == 1000
        print(f"MySQL - 1000 inserções: {insert_time:.2f}s")
        print(f"MySQL - 1000 consultas: {select_time:.2f}s")
        
        await mysql_bridge.close()

class TestCrossDatabase:
    """Testes comparativos entre bancos"""
    
    @pytest.mark.asyncio
    async def test_cross_database_compatibility(self):
        """Testa compatibilidade entre diferentes bancos"""
        bridges = {
            "postgres": SQLBridge("postgres", "localhost", "kairondb_test", "kairondb", "KaironDB123!"),
            "sqlserver": SQLBridge("sqlserver", "localhost", "kairondb_test", "sa", "KaironDB123!"),
            "mysql": SQLBridge("mysql", "localhost", "kairondb_test", "kairondb", "KaironDB123!")
        }
        
        results = {}
        
        for db_name, bridge in bridges.items():
            try:
                await bridge.connect()
                
                # Teste básico
                start_time = time.time()
                result = await bridge.exec("SELECT 1 as test", expect_result=True)
                end_time = time.time()
                
                results[db_name] = {
                    "connected": True,
                    "query_time": end_time - start_time,
                    "result": result
                }
                
                await bridge.close()
            except Exception as e:
                results[db_name] = {
                    "connected": False,
                    "error": str(e)
                }
        
        # Verificar resultados
        for db_name, result in results.items():
            if result["connected"]:
                assert result["result"] == [{"test": 1}]
                print(f"{db_name}: {result['query_time']:.4f}s")
            else:
                print(f"{db_name}: ERRO - {result['error']}")
        
        return results
