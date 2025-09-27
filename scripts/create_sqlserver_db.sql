-- Script para criar o banco de dados kairondb_test no SQL Server
CREATE DATABASE kairondb_test;
GO

USE kairondb_test;
GO

-- Criar tabelas de teste
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
GO
