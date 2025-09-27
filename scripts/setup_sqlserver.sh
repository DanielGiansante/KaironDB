#!/bin/bash
# Script para configurar o banco de dados SQL Server

echo "🔧 Configurando banco de dados SQL Server..."

# Aguardar o SQL Server ficar disponível
echo "⏳ Aguardando SQL Server ficar disponível..."
sleep 30

# Criar banco de dados
echo "📦 Criando banco de dados kairondb_test..."
docker exec -i kairondb_sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "KaironDB123!" -Q "CREATE DATABASE kairondb_test;"

# Criar tabelas
echo "📋 Criando tabelas..."
docker exec -i kairondb_sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "KaironDB123!" -d kairondb_test -Q "
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(100) UNIQUE NOT NULL,
    age INT,
    created_at DATETIME2 DEFAULT GETDATE()
);

CREATE TABLE products (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    price DECIMAL(10,2),
    category NVARCHAR(50),
    created_at DATETIME2 DEFAULT GETDATE()
);
"

echo "✅ Banco de dados SQL Server configurado com sucesso!"
