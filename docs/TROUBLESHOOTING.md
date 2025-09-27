# Guia de Troubleshooting - KaironDB

## Índice

- [Problemas Comuns](#problemas-comuns)
- [Problemas de Conexão](#problemas-de-conexão)
- [Problemas de Performance](#problemas-de-performance)
- [Problemas de Modelos](#problemas-de-modelos)
- [Problemas de Instalação](#problemas-de-instalação)
- [Logs e Debugging](#logs-e-debugging)

## Problemas Comuns

### Erro: "DLL not found" ou "Library not found"

**Sintomas**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'sqlbridge.dll'
```

**Causa**: A biblioteca Go não foi encontrada.

**Solução**:
```python
# Verificar localização da DLL
import os
from kairondb import SQLBridge

# Verificar se a DLL existe
dll_path = os.path.join(os.path.dirname(__file__), 'sqlbridge.dll')
print(f"DLL path: {dll_path}")
print(f"Exists: {os.path.exists(dll_path)}")

# Especificar caminho manualmente
bridge = SQLBridge("sqlite3", "test.db", lib_path="caminho/para/sqlbridge.dll")
```

### Erro: "Module not found"

**Sintomas**:
```
ModuleNotFoundError: No module named 'kairondb'
```

**Causa**: KaironDB não está instalado ou não está no PATH.

**Solução**:
```bash
# Verificar instalação
pip list | grep kairondb

# Reinstalar
pip uninstall kairondb
pip install kairondb

# Verificar PATH do Python
python -c "import sys; print(sys.path)"
```

### Erro: "Version mismatch"

**Sintomas**:
```
TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
```

**Causa**: Incompatibilidade entre versões.

**Solução**:
```bash
# Verificar versão
python -c "import kairondb; print(kairondb.__version__)"

# Atualizar para versão mais recente
pip install --upgrade kairondb
```

## Problemas de Conexão

### Erro: "Connection failed"

**Sintomas**:
```
PoolError: Falha ao criar pool: {"error":"falha ao conectar ao banco de dados"}
```

**Causa**: Parâmetros de conexão incorretos ou banco inacessível.

**Solução**:
```python
# Verificar parâmetros
bridge = SQLBridge("postgres", "localhost", "meudb", "usuario", "senha", debug=True)
await bridge.connect()

# Verificar se o banco está rodando
# PostgreSQL
psql -h localhost -U usuario -d meudb

# MySQL
mysql -h localhost -u usuario -p meudb
```

### Erro: "SSL is not enabled"

**Sintomas**:
```
PoolError: SSL is not enabled on the server
```

**Causa**: Configuração SSL do PostgreSQL.

**Solução**:
```python
# Desabilitar SSL (apenas para desenvolvimento)
bridge = SQLBridge("postgres", "localhost", "meudb", "usuario", "senha")
# Adicionar parâmetros SSL se necessário
```

### Erro: "Authentication failed"

**Sintomas**:
```
PoolError: authentication failed for user "usuario"
```

**Causa**: Credenciais incorretas.

**Solução**:
```python
# Verificar credenciais
bridge = SQLBridge("postgres", "localhost", "meudb", "usuario_correto", "senha_correta")
await bridge.connect()
```

### Erro: "Database does not exist"

**Sintomas**:
```
PoolError: database "meudb" does not exist
```

**Causa**: Banco de dados não existe.

**Solução**:
```bash
# Criar banco de dados
# PostgreSQL
createdb meudb

# MySQL
mysql -u root -p
CREATE DATABASE meudb;
```

## Problemas de Performance

### Operações Lentas

**Sintomas**: Inserções ou consultas muito lentas.

**Causa**: Configuração inadequada do pool de conexões.

**Solução**:
```python
# Configurar pool otimizado
bridge = SQLBridge(
    "postgres",
    "localhost",
    "meudb",
    "usuario",
    "senha",
    enable_advanced_pool=True,
    pool_config={
        "max_connections": 20,
        "min_connections": 5,
        "connection_timeout": 30,
        "idle_timeout": 300
    }
)
```

### Alto Uso de Memória

**Sintomas**: Consumo excessivo de memória.

**Causa**: Pool de conexões muito grande ou cache desnecessário.

**Solução**:
```python
# Reduzir tamanho do pool
bridge = SQLBridge(
    "postgres",
    "localhost",
    "meudb",
    "usuario",
    "senha",
    enable_advanced_pool=True,
    pool_config={
        "max_connections": 5,
        "min_connections": 1
    }
)

# Desabilitar cache se não necessário
bridge = SQLBridge("sqlite3", "test.db", enable_query_cache=False)
```

### Timeout em Operações

**Sintomas**: Operações falham com timeout.

**Causa**: Timeout muito baixo ou operações muito complexas.

**Solução**:
```python
# Aumentar timeout
bridge = SQLBridge(
    "postgres",
    "localhost",
    "meudb",
    "usuario",
    "senha",
    enable_advanced_pool=True,
    pool_config={
        "connection_timeout": 60,
        "query_timeout": 300
    }
)
```

## Problemas de Modelos

### Erro: "Table does not exist"

**Sintomas**:
```
{'error': 'no such table: usuarios'}
```

**Causa**: Tabela não foi criada.

**Solução**:
```python
# Criar tabela manualmente
await bridge.create_table("usuarios", {
    "id": "INTEGER PRIMARY KEY",
    "nome": "TEXT NOT NULL",
    "email": "TEXT UNIQUE"
})

# Ou usar modelo com auto-criação
class Usuario(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(required=True)
    email = StringField(required=True)

usuario = Usuario(nome="João", email="joao@exemplo.com")
await usuario.save(bridge)  # Cria tabela automaticamente
```

### Erro: "Field validation failed"

**Sintomas**:
```
ValidationError: O campo 'nome' é obrigatório
```

**Causa**: Validação de campo falhou.

**Solução**:
```python
# Verificar dados antes de salvar
usuario = Usuario(nome="João", email="joao@exemplo.com")
if usuario.nome and usuario.email:
    await usuario.save(bridge)
else:
    print("Dados inválidos")
```

### Erro: "Primary key not found"

**Sintomas**:
```
Exception: Não é possível atualizar sem chave primária
```

**Causa**: Modelo não tem chave primária definida.

**Solução**:
```python
# Definir chave primária
class Usuario(Model):
    id = IntegerField(primary_key=True)  # Adicionar esta linha
    nome = StringField(required=True)
    email = StringField(required=True)
```

## Problemas de Instalação

### Erro: "Permission denied"

**Sintomas**:
```
PermissionError: [Errno 13] Permission denied
```

**Causa**: Sem permissão para instalar ou acessar arquivos.

**Solução**:
```bash
# Instalar para usuário atual
pip install --user kairondb

# Ou usar sudo (Linux/macOS)
sudo pip install kairondb

# Verificar permissões
ls -la /usr/local/lib/python3.x/site-packages/
```

### Erro: "No module named 'ctypes'"

**Sintomas**:
```
ModuleNotFoundError: No module named 'ctypes'
```

**Causa**: Python instalado incorretamente ou versão muito antiga.

**Solução**:
```bash
# Verificar versão do Python
python --version

# Atualizar Python
# Windows: Baixar do python.org
# Linux: sudo apt-get install python3.8
# macOS: brew install python3.8
```

### Erro: "Compiler not found"

**Sintomas**:
```
error: Microsoft Visual C++ 14.0 is required
```

**Causa**: Compilador C++ não encontrado (Windows).

**Solução**:
```bash
# Instalar Visual Studio Build Tools
# Ou usar versão pré-compilada
pip install kairondb --only-binary=all
```

## Logs e Debugging

### Habilitar Logs Detalhados

```python
import logging
from kairondb import SQLBridge

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('kairondb')

# Usar debug=True
bridge = SQLBridge("sqlite3", "test.db", debug=True)
await bridge.connect()
```

### Verificar Estado da Conexão

```python
# Verificar se está conectado
if bridge.is_connected():
    print("Conectado")
else:
    print("Desconectado")

# Verificar pool de conexões
print(f"Pool ID: {bridge.pool_id}")
```

### Monitorar Performance

```python
import time

# Medir tempo de operações
start = time.time()
result = await bridge.select("usuarios")
end = time.time()
print(f"SELECT levou {end - start:.3f}s")

# Usar profiling
bridge = SQLBridge(
    "sqlite3",
    "test.db",
    enable_profiling=True,
    profiling_config={
        "enabled": True,
        "sample_rate": 1.0
    }
)
```

### Verificar Dados

```python
# Verificar estrutura da tabela
result = await bridge.exec("PRAGMA table_info(usuarios)", expect_result=True)
print("Estrutura da tabela:", result)

# Verificar índices
result = await bridge.exec("PRAGMA index_list(usuarios)", expect_result=True)
print("Índices:", result)
```

### Teste de Conectividade

```python
async def teste_conectividade():
    try:
        bridge = SQLBridge("sqlite3", "test.db")
        await bridge.connect()
        
        # Teste básico
        await bridge.create_table("teste", {"id": "INTEGER PRIMARY KEY"})
        await bridge.insert("teste", {"id": 1})
        result = await bridge.select("teste")
        
        print("✅ Conectividade OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
        return False
    finally:
        if 'bridge' in locals():
            await bridge.close()

# Executar teste
asyncio.run(teste_conectividade())
```

### Coletar Informações do Sistema

```python
import sys
import platform
import kairondb

def info_sistema():
    print("=== Informações do Sistema ===")
    print(f"Python: {sys.version}")
    print(f"Plataforma: {platform.platform()}")
    print(f"Arquitetura: {platform.architecture()}")
    print(f"KaironDB: {kairondb.__version__}")
    
    # Verificar dependências
    try:
        import ctypes
        print("✅ ctypes disponível")
    except ImportError:
        print("❌ ctypes não disponível")
    
    try:
        import asyncio
        print("✅ asyncio disponível")
    except ImportError:
        print("❌ asyncio não disponível")

info_sistema()
```

---

Para mais informações sobre troubleshooting, consulte a [documentação completa](README.md).