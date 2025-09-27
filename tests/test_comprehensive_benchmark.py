#!/usr/bin/env python3
"""
Testes comparativos abrangentes com todas as bibliotecas
"""

import pytest
import asyncio
import time
import sys
import os
import statistics
from typing import Dict, List, Any

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kairondb.bridge import SQLBridge

# Tentar importar outras bibliotecas para comparação
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

try:
    import aiosqlite
    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False

try:
    import aiomysql
    HAS_AIOMYSQL = True
except ImportError:
    HAS_AIOMYSQL = False

try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False

try:
    import sqlalchemy
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    import pymysql
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

class BenchmarkResult:
    """Classe para armazenar resultados de benchmark"""
    
    def __init__(self, library_name: str, operation: str, times: List[float], success: bool = True, error: str = None):
        self.library_name = library_name
        self.operation = operation
        self.times = times
        self.success = success
        self.error = error
        self.mean_time = statistics.mean(times) if times else 0
        self.median_time = statistics.median(times) if times else 0
        self.min_time = min(times) if times else 0
        self.max_time = max(times) if times else 0
        self.std_dev = statistics.stdev(times) if len(times) > 1 else 0

class DatabaseBenchmark:
    """Classe base para benchmarks de banco de dados"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    async def benchmark_operation(self, operation_func, operation_name: str, iterations: int = 10) -> BenchmarkResult:
        """Executa um benchmark de uma operação"""
        times = []
        success = True
        error = None
        
        for i in range(iterations):
            try:
                start_time = time.time()
                await operation_func()
                end_time = time.time()
                times.append(end_time - start_time)
            except Exception as e:
                success = False
                error = str(e)
                break
        
        return BenchmarkResult(operation_name, operation_name, times, success, error)
    
    def add_result(self, result: BenchmarkResult):
        """Adiciona um resultado ao benchmark"""
        self.results.append(result)
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna um resumo dos resultados"""
        summary = {}
        for result in self.results:
            if result.success:
                summary[result.library_name] = {
                    "mean": result.mean_time,
                    "median": result.median_time,
                    "min": result.min_time,
                    "max": result.max_time,
                    "std_dev": result.std_dev,
                    "iterations": len(result.times)
                }
            else:
                summary[result.library_name] = {
                    "error": result.error
                }
        return summary

class TestKaironDBBenchmark:
    """Benchmarks do KaironDB"""
    
    @pytest.fixture
    def kairondb_mysql(self):
        """Bridge do KaironDB para MySQL"""
        return SQLBridge(
            driver="mysql",
            server="localhost",
            db_name="kairondb_test",
            user="kairondb",
            password="KaironDB123!"
        )
    
    @pytest.fixture
    def kairondb_postgres(self):
        """Bridge do KaironDB para PostgreSQL"""
        return SQLBridge(
            driver="postgres",
            server="localhost",
            db_name="kairondb_test",
            user="kairondb",
            password="KaironDB123!"
        )
    
    @pytest.fixture
    def kairondb_sqlserver(self):
        """Bridge do KaironDB para SQL Server"""
        return SQLBridge(
            driver="sqlserver",
            server="localhost",
            db_name="kairondb_test",
            user="sa",
            password="KaironDB123!"
        )
    
    @pytest.mark.asyncio
    async def test_kairondb_mysql_performance(self, kairondb_mysql):
        """Testa performance do KaironDB com MySQL"""
        await kairondb_mysql.connect()
        
        # Criar tabela
        await kairondb_mysql.create_table("benchmark_test", {
            "id": "INT AUTO_INCREMENT PRIMARY KEY",
            "name": "VARCHAR(100)",
            "value": "INT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        })
        
        benchmark = DatabaseBenchmark()
        
        # Benchmark de inserção única
        async def single_insert():
            await kairondb_mysql.insert("benchmark_test", {
                "name": f"Test {time.time()}",
                "value": int(time.time())
            })
        
        result = await benchmark.benchmark_operation(single_insert, "KaironDB MySQL Single Insert", 100)
        benchmark.add_result(result)
        
        # Benchmark de consulta
        async def select_query():
            await kairondb_mysql.select("benchmark_test")
        
        result = await benchmark.benchmark_operation(select_query, "KaironDB MySQL Select", 100)
        benchmark.add_result(result)
        
        await kairondb_mysql.close()
        
        summary = benchmark.get_summary()
        print("\n📊 KAIRONDB MYSQL BENCHMARK:")
        for operation, stats in summary.items():
            if "error" not in stats:
                print(f"{operation}: {stats['mean']:.4f}s (médio)")
        
        return summary

class TestPyODBCBenchmark:
    """Benchmarks do PyODBC"""
    
    @pytest.mark.skipif(not HAS_PYODBC, reason="PyODBC não está instalado")
    @pytest.mark.asyncio
    async def test_pyodbc_sqlserver_performance(self):
        """Testa performance do PyODBC com SQL Server"""
        conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=kairondb_test;UID=sa;PWD=KaironDB123!"
        
        def run_benchmark():
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Criar tabela
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pyodbc_benchmark' AND xtype='U')
                CREATE TABLE pyodbc_benchmark (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(100),
                    value INT,
                    created_at DATETIME2 DEFAULT GETDATE()
                )
            """)
            conn.commit()
            
            benchmark = DatabaseBenchmark()
            
            # Benchmark de inserção única
            def single_insert():
                cursor.execute("INSERT INTO pyodbc_benchmark (name, value) VALUES (?, ?)", 
                             f"Test {time.time()}", int(time.time()))
                conn.commit()
            
            # Executar benchmark síncrono
            times = []
            for i in range(100):
                start_time = time.time()
                single_insert()
                end_time = time.time()
                times.append(end_time - start_time)
            
            result = BenchmarkResult("PyODBC SQL Server Single Insert", "PyODBC SQL Server Single Insert", times)
            benchmark.add_result(result)
            
            # Benchmark de consulta
            def select_query():
                cursor.execute("SELECT * FROM pyodbc_benchmark")
                cursor.fetchall()
            
            times = []
            for i in range(100):
                start_time = time.time()
                select_query()
                end_time = time.time()
                times.append(end_time - start_time)
            
            result = BenchmarkResult("PyODBC SQL Server Select", "PyODBC SQL Server Select", times)
            benchmark.add_result(result)
            
            conn.close()
            return benchmark.get_summary()
        
        # Executar em thread separada para não bloquear
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(None, run_benchmark)
        
        print("\n📊 PYODBC SQL SERVER BENCHMARK:")
        for operation, stats in summary.items():
            if "error" not in stats:
                print(f"{operation}: {stats['mean']:.4f}s (médio)")
        
        return summary

class TestSQLAlchemyBenchmark:
    """Benchmarks do SQLAlchemy"""
    
    @pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy não está instalado")
    @pytest.mark.asyncio
    async def test_sqlalchemy_mysql_performance(self):
        """Testa performance do SQLAlchemy com MySQL"""
        engine = create_engine("mysql+pymysql://kairondb:KaironDB123!@localhost/kairondb_test")
        Session = sessionmaker(bind=engine)
        
        def run_benchmark():
            session = Session()
            
            # Criar tabela
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS sqlalchemy_benchmark (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    value INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
            
            benchmark = DatabaseBenchmark()
            
            # Benchmark de inserção única
            def single_insert():
                session.execute(text("INSERT INTO sqlalchemy_benchmark (name, value) VALUES (:name, :value)"),
                              {"name": f"Test {time.time()}", "value": int(time.time())})
                session.commit()
            
            # Executar benchmark síncrono
            times = []
            for i in range(100):
                start_time = time.time()
                single_insert()
                end_time = time.time()
                times.append(end_time - start_time)
            
            result = BenchmarkResult("SQLAlchemy MySQL Single Insert", "SQLAlchemy MySQL Single Insert", times)
            benchmark.add_result(result)
            
            # Benchmark de consulta
            def select_query():
                result = session.execute(text("SELECT * FROM sqlalchemy_benchmark"))
                result.fetchall()
            
            times = []
            for i in range(100):
                start_time = time.time()
                select_query()
                end_time = time.time()
                times.append(end_time - start_time)
            
            result = BenchmarkResult("SQLAlchemy MySQL Select", "SQLAlchemy MySQL Select", times)
            benchmark.add_result(result)
            
            session.close()
            return benchmark.get_summary()
        
        # Executar em thread separada para não bloquear
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(None, run_benchmark)
        
        print("\n📊 SQLALCHEMY MYSQL BENCHMARK:")
        for operation, stats in summary.items():
            if "error" not in stats:
                print(f"{operation}: {stats['mean']:.4f}s (médio)")
        
        return summary

class TestAsyncPGBenchmark:
    """Benchmarks do AsyncPG"""
    
    @pytest.mark.skipif(not HAS_ASYNCPG, reason="AsyncPG não está instalado")
    @pytest.mark.asyncio
    async def test_asyncpg_performance(self):
        """Testa performance do AsyncPG"""
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="kairondb",
            password="KaironDB123!",
            database="kairondb_test"
        )
        
        # Criar tabela
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS asyncpg_benchmark (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        benchmark = DatabaseBenchmark()
        
        # Benchmark de inserção única
        async def single_insert():
            await conn.execute(
                "INSERT INTO asyncpg_benchmark (name, value) VALUES ($1, $2)",
                f"Test {time.time()}", int(time.time())
            )
        
        result = await benchmark.benchmark_operation(single_insert, "AsyncPG Single Insert", 100)
        benchmark.add_result(result)
        
        # Benchmark de consulta
        async def select_query():
            await conn.fetch("SELECT * FROM asyncpg_benchmark")
        
        result = await benchmark.benchmark_operation(select_query, "AsyncPG Select", 100)
        benchmark.add_result(result)
        
        await conn.close()
        
        summary = benchmark.get_summary()
        print("\n📊 ASYNCPG BENCHMARK:")
        for operation, stats in summary.items():
            if "error" not in stats:
                print(f"{operation}: {stats['mean']:.4f}s (médio)")
        
        return summary

class TestComprehensiveComparison:
    """Testes comparativos abrangentes"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_benchmark(self):
        """Executa benchmark abrangente comparando todas as bibliotecas"""
        print("\n🚀 INICIANDO BENCHMARK ABRANGENTE")
        print("=" * 60)
        
        results = {}
        
        # KaironDB MySQL
        try:
            kairondb_mysql = SQLBridge(
                driver="mysql",
                server="localhost",
                db_name="kairondb_test",
                user="kairondb",
                password="KaironDB123!"
            )
            await kairondb_mysql.connect()
            
            # Criar tabela
            await kairondb_mysql.create_table("benchmark_test", {
                "id": "INT AUTO_INCREMENT PRIMARY KEY",
                "name": "VARCHAR(100)",
                "value": "INT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            })
            
            benchmark = DatabaseBenchmark()
            
            # Benchmark de inserção única
            async def single_insert():
                await kairondb_mysql.insert("benchmark_test", {
                    "name": f"Test {time.time()}",
                    "value": int(time.time())
                })
            
            result = await benchmark.benchmark_operation(single_insert, "KaironDB MySQL Single Insert", 100)
            benchmark.add_result(result)
            
            # Benchmark de consulta
            async def select_query():
                await kairondb_mysql.select("benchmark_test")
            
            result = await benchmark.benchmark_operation(select_query, "KaironDB MySQL Select", 100)
            benchmark.add_result(result)
            
            await kairondb_mysql.close()
            results["KaironDB MySQL"] = benchmark.get_summary()
        except Exception as e:
            results["KaironDB MySQL"] = {"error": str(e)}
        
        # PyODBC SQL Server
        if HAS_PYODBC:
            try:
                conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=kairondb_test;UID=sa;PWD=KaironDB123!"
                
                def run_pyodbc_benchmark():
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()
                    
                    # Criar tabela
                    cursor.execute("""
                        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pyodbc_benchmark' AND xtype='U')
                        CREATE TABLE pyodbc_benchmark (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            name NVARCHAR(100),
                            value INT,
                            created_at DATETIME2 DEFAULT GETDATE()
                        )
                    """)
                    conn.commit()
                    
                    benchmark = DatabaseBenchmark()
                    
                    # Benchmark de inserção única
                    def single_insert():
                        cursor.execute("INSERT INTO pyodbc_benchmark (name, value) VALUES (?, ?)", 
                                     f"Test {time.time()}", int(time.time()))
                        conn.commit()
                    
                    # Executar benchmark síncrono
                    times = []
                    for i in range(100):
                        start_time = time.time()
                        single_insert()
                        end_time = time.time()
                        times.append(end_time - start_time)
                    
                    result = BenchmarkResult("PyODBC SQL Server Single Insert", "PyODBC SQL Server Single Insert", times)
                    benchmark.add_result(result)
                    
                    # Benchmark de consulta
                    def select_query():
                        cursor.execute("SELECT * FROM pyodbc_benchmark")
                        cursor.fetchall()
                    
                    times = []
                    for i in range(100):
                        start_time = time.time()
                        select_query()
                        end_time = time.time()
                        times.append(end_time - start_time)
                    
                    result = BenchmarkResult("PyODBC SQL Server Select", "PyODBC SQL Server Select", times)
                    benchmark.add_result(result)
                    
                    conn.close()
                    return benchmark.get_summary()
                
                # Executar em thread separada para não bloquear
                loop = asyncio.get_event_loop()
                results["PyODBC SQL Server"] = await loop.run_in_executor(None, run_pyodbc_benchmark)
            except Exception as e:
                results["PyODBC SQL Server"] = {"error": str(e)}
        else:
            results["PyODBC SQL Server"] = {"error": "PyODBC não instalado"}
        
        # SQLAlchemy MySQL
        if HAS_SQLALCHEMY:
            try:
                engine = create_engine("mysql+pymysql://kairondb:KaironDB123!@localhost/kairondb_test")
                Session = sessionmaker(bind=engine)
                
                def run_sqlalchemy_benchmark():
                    session = Session()
                    
                    # Criar tabela
                    session.execute(text("""
                        CREATE TABLE IF NOT EXISTS sqlalchemy_benchmark (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(100),
                            value INT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    session.commit()
                    
                    benchmark = DatabaseBenchmark()
                    
                    # Benchmark de inserção única
                    def single_insert():
                        session.execute(text("INSERT INTO sqlalchemy_benchmark (name, value) VALUES (:name, :value)"),
                                      {"name": f"Test {time.time()}", "value": int(time.time())})
                        session.commit()
                    
                    # Executar benchmark síncrono
                    times = []
                    for i in range(100):
                        start_time = time.time()
                        single_insert()
                        end_time = time.time()
                        times.append(end_time - start_time)
                    
                    result = BenchmarkResult("SQLAlchemy MySQL Single Insert", "SQLAlchemy MySQL Single Insert", times)
                    benchmark.add_result(result)
                    
                    # Benchmark de consulta
                    def select_query():
                        result = session.execute(text("SELECT * FROM sqlalchemy_benchmark"))
                        result.fetchall()
                    
                    times = []
                    for i in range(100):
                        start_time = time.time()
                        select_query()
                        end_time = time.time()
                        times.append(end_time - start_time)
                    
                    result = BenchmarkResult("SQLAlchemy MySQL Select", "SQLAlchemy MySQL Select", times)
                    benchmark.add_result(result)
                    
                    session.close()
                    return benchmark.get_summary()
                
                # Executar em thread separada para não bloquear
                loop = asyncio.get_event_loop()
                results["SQLAlchemy MySQL"] = await loop.run_in_executor(None, run_sqlalchemy_benchmark)
            except Exception as e:
                results["SQLAlchemy MySQL"] = {"error": str(e)}
        else:
            results["SQLAlchemy MySQL"] = {"error": "SQLAlchemy não instalado"}
        
        # AsyncPG PostgreSQL
        if HAS_ASYNCPG:
            try:
                conn = await asyncpg.connect(
                    host="localhost",
                    port=5432,
                    user="kairondb",
                    password="KaironDB123!",
                    database="kairondb_test"
                )
                
                # Criar tabela
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS asyncpg_benchmark (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        value INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                benchmark = DatabaseBenchmark()
                
                # Benchmark de inserção única
                async def single_insert():
                    await conn.execute(
                        "INSERT INTO asyncpg_benchmark (name, value) VALUES ($1, $2)",
                        f"Test {time.time()}", int(time.time())
                    )
                
                result = await benchmark.benchmark_operation(single_insert, "AsyncPG Single Insert", 100)
                benchmark.add_result(result)
                
                # Benchmark de consulta
                async def select_query():
                    await conn.fetch("SELECT * FROM asyncpg_benchmark")
                
                result = await benchmark.benchmark_operation(select_query, "AsyncPG Select", 100)
                benchmark.add_result(result)
                
                await conn.close()
                results["AsyncPG PostgreSQL"] = benchmark.get_summary()
            except Exception as e:
                results["AsyncPG PostgreSQL"] = {"error": str(e)}
        else:
            results["AsyncPG PostgreSQL"] = {"error": "AsyncPG não instalado"}
        
        # Análise comparativa
        print("\n📈 ANÁLISE COMPARATIVA FINAL:")
        print("=" * 60)
        
        operations = ["Single Insert", "Select"]
        
        for operation in operations:
            print(f"\n🔍 {operation}:")
            print("-" * 30)
            
            operation_results = {}
            for library, library_results in results.items():
                for op_name, op_stats in library_results.items():
                    if operation in op_name and "error" not in op_stats:
                        operation_results[library] = op_stats["mean"]
            
            # Ordenar por performance (menor tempo = melhor)
            sorted_results = sorted(
                [(lib, time) for lib, time in operation_results.items() if time is not None],
                key=lambda x: x[1]
            )
            
            if sorted_results:
                best_library, best_time = sorted_results[0]
                print(f"🏆 Melhor: {best_library} ({best_time:.4f}s)")
                
                for i, (library, time) in enumerate(sorted_results[1:], 2):
                    slowdown = (time / best_time - 1) * 100
                    print(f"   {i}º: {library} ({time:.4f}s, +{slowdown:.1f}%)")
            else:
                print("❌ Nenhum resultado válido encontrado")
        
        return results
