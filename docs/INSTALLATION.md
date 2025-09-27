# Guia de Instalação - KaironDB

## Índice

- [Requisitos](#requisitos)
- [Instalação Básica](#instalação-básica)
- [Instalação com Drivers Específicos](#instalação-com-drivers-específicos)
- [Instalação para Desenvolvimento](#instalação-para-desenvolvimento)
- [Verificação da Instalação](#verificação-da-instalação)
- [Solução de Problemas](#solução-de-problemas)

## Requisitos

### Sistema Operacional
- **Windows**: 10 ou superior
- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 9+
- **macOS**: 10.14 ou superior

### Python
- **Python**: 3.8 ou superior
- **pip**: 20.0 ou superior

### Dependências do Sistema

#### Windows
- Visual C++ Redistributable (já incluído na maioria das instalações)

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential libssl-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install openssl-devel
```

#### macOS
```bash
# Instalar Xcode Command Line Tools
xcode-select --install

# Instalar Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Instalação Básica

### 1. Instalar via pip

```bash
pip install kairondb
```

### 2. Verificar instalação

```python
import kairondb
print(f"KaironDB versão: {kairondb.__version__}")
```

### 3. Teste básico

```python
import asyncio
from kairondb import SQLBridge

async def teste_basico():
    bridge = SQLBridge("sqlite3", "teste.db")
    await bridge.connect()
    print("✅ Conexão estabelecida!")
        await bridge.close()
        
asyncio.run(teste_basico())
```

## Instalação com Drivers Específicos

### SQLite (Padrão)
```bash
# SQLite já está incluído
pip install kairondb
```

### PostgreSQL
```bash
# Instalar driver PostgreSQL
pip install kairondb[postgres]

# Ou instalar psycopg2 separadamente
pip install psycopg2-binary
```

### MySQL
```bash
# Instalar driver MySQL
pip install kairondb[mysql]

# Ou instalar PyMySQL separadamente
pip install PyMySQL
```

### SQL Server
```bash
# Instalar driver SQL Server
pip install kairondb[sqlserver]

# Ou instalar pyodbc separadamente
pip install pyodbc
```

### Todos os Drivers
```bash
# Instalar todos os drivers
pip install kairondb[all]
```

## Instalação para Desenvolvimento

### 1. Clonar repositório

```bash
git clone https://github.com/kairondb/kairondb.git
cd kairondb
```

### 2. Criar ambiente virtual

```bash
# Python 3.8+
python -m venv venv

# Ativar ambiente virtual
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Instalar dependências

```bash
# Instalar dependências de desenvolvimento
pip install -e .[dev]

# Ou instalar manualmente
pip install -e .
pip install pytest pytest-asyncio black flake8 mypy
```

### 4. Executar testes

```bash
# Executar todos os testes
pytest

# Executar testes com cobertura
pytest --cov=kairondb

# Executar testes específicos
pytest tests/test_bridge.py
```

## Verificação da Instalação

### 1. Teste de Importação

```python
# Teste básico
import kairondb
from kairondb import SQLBridge, Model, StringField, IntegerField

print("✅ Importação bem-sucedida!")
```

### 2. Teste de Conexão

```python
import asyncio
from kairondb import SQLBridge

async def teste_conexao():
    try:
        bridge = SQLBridge("sqlite3", "teste.db")
        await bridge.connect()
        print("✅ Conexão SQLite funcionando!")
        await bridge.close()
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

asyncio.run(teste_conexao())
```

### 3. Teste de Operações

```python
import asyncio
from kairondb import SQLBridge, Model, StringField, IntegerField

class Teste(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(required=True)

async def teste_operacoes():
    try:
        bridge = SQLBridge("sqlite3", "teste.db")
        await bridge.connect()
        
        # Criar tabela
        await bridge.create_table("teste", {
            "id": "INTEGER PRIMARY KEY",
            "nome": "TEXT NOT NULL"
        })
        
        # Inserir dados
        await bridge.insert("teste", {"nome": "Teste"})
        
        # Consultar dados
        dados = await bridge.select("teste")
        print(f"✅ Operações funcionando! Dados: {dados}")
        
        await bridge.close()
    except Exception as e:
        print(f"❌ Erro nas operações: {e}")

asyncio.run(teste_operacoes())
```

### 4. Teste de Performance

```python
import asyncio
import time
from kairondb import SQLBridge

async def teste_performance():
    bridge = SQLBridge("sqlite3", "teste_perf.db")
    await bridge.connect()
    
    # Criar tabela
    await bridge.create_table("perf", {
        "id": "INTEGER PRIMARY KEY",
        "dados": "TEXT"
    })
    
    # Teste de inserção
    start = time.time()
    for i in range(100):
        await bridge.insert("perf", {"dados": f"Dados {i}"})
    end = time.time()
    
    print(f"✅ 100 inserções em {end - start:.3f}s")
    
    await bridge.close()

asyncio.run(teste_performance())
```

## Solução de Problemas

### Erro: "DLL not found"

**Problema**: Erro ao carregar a biblioteca Go.

**Solução**:
```bash
# Verificar se a DLL está no local correto
ls src/kairondb/sqlbridge.dll

# Reinstalar o pacote
pip uninstall kairondb
pip install kairondb
```

### Erro: "Module not found"

**Problema**: Módulo não encontrado.

**Solução**:
```bash
# Verificar instalação
pip list | grep kairondb

# Reinstalar
pip install --force-reinstall kairondb
```

### Erro: "Connection failed"

**Problema**: Falha na conexão com o banco.

**Solução**:
```python
# Verificar parâmetros de conexão
bridge = SQLBridge("sqlite3", "teste.db", debug=True)
await bridge.connect()
```

### Erro: "Permission denied"

**Problema**: Sem permissão para criar arquivos.

**Solução**:
```bash
# Verificar permissões do diretório
ls -la

# Executar com permissões adequadas
sudo python script.py
```

### Erro: "Version mismatch"

**Problema**: Incompatibilidade de versão.

**Solução**:
```bash
# Verificar versão do Python
python --version

# Atualizar Python se necessário
# Instalar versão compatível do KaironDB
pip install kairondb==1.0.1
```

### Erro: "Driver not found"

**Problema**: Driver do banco não encontrado.

**Solução**:
```bash
# Instalar driver específico
pip install kairondb[postgres]
pip install kairondb[mysql]
pip install kairondb[sqlserver]
```

### Erro: "Memory error"

**Problema**: Erro de memória.

**Solução**:
```python
# Usar configurações de pool menores
bridge = SQLBridge(
    "postgres",
    "localhost",
    "db",
    "user",
    "pass",
    enable_advanced_pool=True,
    pool_config={
        "max_connections": 5,
        "min_connections": 1
    }
)
```

### Erro: "Timeout"

**Problema**: Timeout na conexão.

**Solução**:
```python
# Aumentar timeout
bridge = SQLBridge(
    "postgres",
    "localhost",
    "db",
    "user",
    "pass",
    enable_advanced_pool=True,
    pool_config={
        "connection_timeout": 60
    }
)
```

## Verificação Final

### Script de Verificação Completa

```python
import asyncio
import sys
from kairondb import SQLBridge, Model, StringField, IntegerField

async def verificacao_completa():
    print("🔍 Verificação completa do KaironDB")
    print("=" * 50)
    
    # 1. Verificar importação
    try:
        import kairondb
        print(f"✅ Versão: {kairondb.__version__}")
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    
    # 2. Verificar conexão
    try:
        bridge = SQLBridge("sqlite3", "verificacao.db")
        await bridge.connect()
        print("✅ Conexão estabelecida")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # 3. Verificar operações CRUD
    try:
        await bridge.create_table("verificacao", {
            "id": "INTEGER PRIMARY KEY",
            "nome": "TEXT NOT NULL"
        })
        print("✅ Criação de tabela")
        
        await bridge.insert("verificacao", {"nome": "Teste"})
        print("✅ Inserção")
        
        dados = await bridge.select("verificacao")
        print(f"✅ Consulta: {len(dados)} registros")
        
        await bridge.update("verificacao", {"nome": "Teste Atualizado"}, {"id": 1})
        print("✅ Atualização")
        
        await bridge.delete("verificacao", {"id": 1})
        print("✅ Exclusão")
        
    except Exception as e:
        print(f"❌ Erro nas operações: {e}")
        return False
    
    # 4. Verificar modelos
    try:
        class TesteModel(Model):
            id = IntegerField(primary_key=True)
            nome = StringField(required=True)
        
        modelo = TesteModel(nome="Teste Model")
        await modelo.save(bridge)
        print("✅ Modelo criado")
        
        modelos = await TesteModel.select(bridge)
        print(f"✅ Consulta de modelo: {len(modelos)} registros")
        
    except Exception as e:
        print(f"❌ Erro nos modelos: {e}")
        return False
    
    # 5. Limpeza
    try:
    await bridge.close()
        print("✅ Conexão fechada")
    except Exception as e:
        print(f"❌ Erro ao fechar: {e}")
        return False
    
    print("\n🎉 Verificação completa bem-sucedida!")
    return True

if __name__ == "__main__":
    sucesso = asyncio.run(verificacao_completa())
    sys.exit(0 if sucesso else 1)
```

### Executar Verificação

```bash
python verificacao.py
```

---

Para mais informações sobre instalação, consulte a [documentação completa](README.md).