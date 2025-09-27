#!/usr/bin/env python3
"""
Script para configurar bancos de dados de teste
"""

import time
import subprocess
import sys
import os

def run_command(command, description):
    """Executa um comando e retorna o resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso")
            return True
        else:
            print(f"❌ {description} - Erro: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exceção: {e}")
        return False

def wait_for_database(host, port, database_type, max_attempts=30):
    """Aguarda o banco de dados ficar disponível"""
    print(f"⏳ Aguardando {database_type} em {host}:{port}...")
    
    for attempt in range(max_attempts):
        try:
            if database_type == "postgres":
                cmd = f"pg_isready -h {host} -p {port} -U kairondb"
            elif database_type == "sqlserver":
                cmd = f"nc -z {host} {port}"
            elif database_type == "mysql":
                cmd = f"nc -z {host} {port}"
            else:
                return False
                
            result = subprocess.run(cmd, shell=True, capture_output=True)
            if result.returncode == 0:
                print(f"✅ {database_type} está disponível!")
                return True
        except:
            pass
        
        print(f"   Tentativa {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print(f"❌ {database_type} não ficou disponível em {max_attempts} tentativas")
    return False

def setup_databases():
    """Configura todos os bancos de dados"""
    print("🚀 CONFIGURAÇÃO DOS BANCOS DE DADOS DE TESTE")
    print("=" * 60)
    
    # 1. Iniciar containers Docker
    print("\n📦 INICIANDO CONTAINERS DOCKER")
    print("-" * 40)
    
    if not run_command("docker-compose up -d", "Iniciando containers Docker"):
        return False
    
    # 2. Aguardar bancos ficarem disponíveis
    print("\n⏳ AGUARDANDO BANCOS FICAREM DISPONÍVEIS")
    print("-" * 40)
    
    databases = [
        ("localhost", "5432", "postgres"),
        ("localhost", "1433", "sqlserver"),
        ("localhost", "3306", "mysql")
    ]
    
    for host, port, db_type in databases:
        if not wait_for_database(host, port, db_type):
            print(f"⚠️  {db_type} não ficou disponível, mas continuando...")
    
    # 3. Criar tabelas de teste
    print("\n📋 CRIANDO TABELAS DE TESTE")
    print("-" * 40)
    
    # PostgreSQL
    postgres_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10,2),
        category VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL Server
    sqlserver_sql = """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
    CREATE TABLE users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        email NVARCHAR(100) UNIQUE NOT NULL,
        age INT,
        created_at DATETIME2 DEFAULT GETDATE()
    );
    
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='products' AND xtype='U')
    CREATE TABLE products (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        price DECIMAL(10,2),
        category NVARCHAR(50),
        created_at DATETIME2 DEFAULT GETDATE()
    );
    """
    
    # MySQL
    mysql_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        age INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10,2),
        category VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Executar SQL nos bancos
    print("✅ Tabelas serão criadas automaticamente pelos testes")
    
    print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print("📊 Bancos disponíveis:")
    print("   • PostgreSQL: localhost:5432 (kairondb/kairondb_test)")
    print("   • SQL Server: localhost:1433 (sa/KaironDB123!)")
    print("   • MySQL: localhost:3306 (kairondb/kairondb_test)")
    print("\n🚀 Execute os testes com: python -m pytest tests/ -v")

if __name__ == "__main__":
    setup_databases()
