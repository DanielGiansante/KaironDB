# Referência da API - KaironDB

## Índice

- [SQLBridge](#sqlbridge)
- [Model](#model)
- [Campos](#campos)
- [Exceções](#exceções)
- [Configurações Avançadas](#configurações-avançadas)

## SQLBridge

A classe principal para conexão e operações com bancos de dados.

### Construtor

```python
SQLBridge(
    driver: str,
    server: Optional[str] = None,
    db_name: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    lib_path: Optional[str] = None,
    debug: bool = False,
    # Configurações avançadas
    enable_advanced_pool: bool = False,
    pool_config: Optional[Dict[str, Any]] = None,
    enable_query_cache: bool = False,
    cache_config: Optional[Dict[str, Any]] = None,
    enable_migrations: bool = False,
    migrations_dir: str = "migrations",
    enable_profiling: bool = False,
    enable_optimizations: bool = False,
    enable_dashboard: bool = False,
    profiling_config: Optional[Dict[str, Any]] = None,
    optimization_config: Optional[Dict[str, Any]] = None,
    dashboard_config: Optional[Dict[str, Any]] = None
)
```

#### Parâmetros

- **driver** (str): Driver do banco de dados (`sqlite3`, `postgres`, `mysql`, `sqlserver`)
- **server** (str, opcional): Servidor do banco (padrão: `:memory:` para SQLite)
- **db_name** (str, opcional): Nome do banco de dados
- **user** (str, opcional): Usuário do banco
- **password** (str, opcional): Senha do banco
- **lib_path** (str, opcional): Caminho para a biblioteca Go
- **debug** (bool): Habilitar logs de debug (padrão: `False`)

### Métodos de Conexão

#### `async connect() -> None`
Conecta ao banco de dados.

```python
await bridge.connect()
```

#### `is_connected() -> bool`
Verifica se está conectado.

```python
if bridge.is_connected():
    print("Conectado!")
```

#### `async close() -> None`
Fecha a conexão.

```python
await bridge.close()
```

### Métodos CRUD

#### `async create_table(table_name: str, columns: Dict[str, str]) -> None`
Cria uma tabela.

```python
await bridge.create_table("usuarios", {
    "id": "INTEGER PRIMARY KEY",
    "nome": "TEXT NOT NULL",
    "email": "TEXT UNIQUE"
})
```

#### `async insert(table_name: str, data: Dict[str, Any]) -> Any`
Insere dados em uma tabela.

```python
result = await bridge.insert("usuarios", {
    "nome": "João Silva",
    "email": "joao@exemplo.com"
})
```

#### `async select(table_name: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`
Seleciona dados de uma tabela.

```python
# Todos os registros
usuarios = await bridge.select("usuarios")

# Com filtro
usuarios = await bridge.select("usuarios", {"idade": 30})
```

#### `async update(table_name: str, data: Dict[str, Any], where: Dict[str, Any]) -> Any`
Atualiza dados em uma tabela.

```python
await bridge.update("usuarios", {"idade": 31}, {"email": "joao@exemplo.com"})
```

#### `async delete(table_name: str, where: Dict[str, Any]) -> Any`
Deleta dados de uma tabela.

```python
await bridge.delete("usuarios", {"email": "joao@exemplo.com"})
```

### Métodos de Conveniência

#### `async get(table_name: str, where: Dict[str, Any]) -> Optional[Dict[str, Any]]`
Obtém um único registro.

```python
usuario = await bridge.get("usuarios", {"email": "joao@exemplo.com"})
if usuario:
    print(f"Encontrado: {usuario['nome']}")
```

#### `async get_or_create(table_name: str, where: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]`
Obtém um registro ou cria se não existir.

```python
usuario = await bridge.get_or_create(
    "usuarios",
    {"email": "joao@exemplo.com"},
    {"nome": "João Silva", "idade": 30}
)
```

#### `async count(table_name: str, where: Optional[Dict[str, Any]] = None) -> int`
Conta registros em uma tabela.

```python
# Total de registros
total = await bridge.count("usuarios")

# Com filtro
jovens = await bridge.count("usuarios", {"idade": 30})
```

#### `async exists(table_name: str, where: Dict[str, Any]) -> bool`
Verifica se um registro existe.

```python
existe = await bridge.exists("usuarios", {"email": "joao@exemplo.com"})
```

### Métodos Avançados

#### `async exec(sql: str, params: Optional[List[Any]] = None, expect_result: bool = True) -> Any`
Executa SQL personalizado.

```python
# SELECT
resultado = await bridge.exec("SELECT * FROM usuarios WHERE idade > ?", [25], expect_result=True)

# INSERT/UPDATE/DELETE
resultado = await bridge.exec("INSERT INTO usuarios (nome, email) VALUES (?, ?)", ["João", "joao@exemplo.com"], expect_result=False)
```

## Model

Classe base para modelos ORM.

### Definindo um Modelo

```python
class Usuario(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=100, required=True)
    email = EmailField(required=True)
    idade = IntegerField(min_value=0, max_value=120)
    ativo = BooleanField(default=True)
```

### Métodos de Instância

#### `async save(bridge=None) -> Any`
Salva o modelo no banco.

```python
usuario = Usuario(nome="João", email="joao@exemplo.com", idade=30)
await usuario.save(bridge)
```

#### `async update(bridge=None) -> Any`
Atualiza o modelo no banco.

```python
usuario.idade = 31
await usuario.update()
```

#### `async delete(bridge=None) -> Any`
Deleta o modelo do banco.

```python
await usuario.delete()
```

#### `to_dict() -> Dict[str, Any]`
Converte o modelo para dicionário.

```python
dados = usuario.to_dict()
```

### Métodos de Classe

#### `async select(bridge=None, fields=None, where=None, joins=None) -> List[Model]`
Seleciona registros do modelo.

```python
# Todos os registros
usuarios = await Usuario.select(bridge)

# Com filtro
jovens = await Usuario.select(bridge, where={"idade": 30})
```

#### `async get(where: Dict[str, Any], bridge=None) -> Optional[Model]`
Obtém um único registro.

```python
usuario = await Usuario.get({"email": "joao@exemplo.com"}, bridge)
```

#### `async get_or_create(where: Dict[str, Any], defaults: Dict[str, Any] = None, bridge=None) -> Model`
Obtém um registro ou cria se não existir.

```python
usuario = await Usuario.get_or_create(
    {"email": "joao@exemplo.com"},
    {"nome": "João Silva", "idade": 30},
    bridge
)
```

#### `async count(where: Dict[str, Any] = None, bridge=None) -> int`
Conta registros do modelo.

```python
total = await Usuario.count(bridge=bridge)
jovens = await Usuario.count({"idade": 30}, bridge)
```

#### `async exists(where: Dict[str, Any], bridge=None) -> bool`
Verifica se um registro existe.

```python
existe = await Usuario.exists({"email": "joao@exemplo.com"}, bridge)
```

#### `from_dict(data: Dict[str, Any]) -> Model`
Cria instância do modelo a partir de dicionário.

```python
usuario = Usuario.from_dict({"nome": "João", "email": "joao@exemplo.com"})
```

## Campos

### StringField

Campo de texto.

```python
StringField(
    max_length: Optional[int] = None,
    required: bool = False,
    default: Optional[str] = None
)
```

### IntegerField

Campo de número inteiro.

```python
IntegerField(
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    required: bool = False,
    default: Optional[int] = None,
    primary_key: bool = False
)
```

### BooleanField

Campo booleano.

```python
BooleanField(
    required: bool = False,
    default: Optional[bool] = None
)
```

### DateTimeField

Campo de data e hora.

```python
DateTimeField(
    auto_now: bool = False,
    auto_now_add: bool = False,
    required: bool = False,
    default: Optional[datetime] = None
)
```

### EmailField

Campo de email com validação.

```python
EmailField(
    required: bool = False,
    default: Optional[str] = None
)
```

## Exceções

### ValidationError

Erro de validação de dados.

```python
from kairondb.exceptions import ValidationError

try:
    usuario = Usuario(idade=-5)  # Idade inválida
except ValidationError as e:
    print(f"Erro de validação: {e}")
```

### ConnectionError

Erro de conexão com o banco.

```python
from kairondb.exceptions import ConnectionError

try:
    bridge = SQLBridge("postgres", "servidor_inexistente", "db", "user", "pass")
    await bridge.connect()
except ConnectionError as e:
    print(f"Erro de conexão: {e}")
```

### PoolError

Erro no pool de conexões.

```python
from kairondb.exceptions import PoolError

try:
    # Operação que falha
    pass
except PoolError as e:
    print(f"Erro no pool: {e}")
```

## Configurações Avançadas

### Pool de Conexões Avançado

```python
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
        "idle_timeout": 300,
        "max_lifetime": 3600
    }
)
```

### Cache de Consultas

```python
bridge = SQLBridge(
    "sqlite3",
    "banco.db",
    enable_query_cache=True,
    cache_config={
        "max_size": 1000,
        "ttl": 300,  # 5 minutos
        "cleanup_interval": 60
    }
)
```

### Migrações

```python
bridge = SQLBridge(
    "postgres",
    "localhost",
    "meudb",
    "usuario",
    "senha",
    enable_migrations=True,
    migrations_dir="migrations"
)
```

### Profiling

```python
bridge = SQLBridge(
    "sqlite3",
    "banco.db",
    enable_profiling=True,
    profiling_config={
        "enabled": True,
        "sample_rate": 0.1,
        "output_file": "profile.json"
    }
)
```

### Otimizações

```python
bridge = SQLBridge(
    "sqlite3",
    "banco.db",
    enable_optimizations=True,
    optimization_config={
        "enable_query_optimization": True,
        "enable_connection_pooling": True,
        "enable_caching": True
    }
)
```

### Dashboard

```python
bridge = SQLBridge(
    "sqlite3",
    "banco.db",
    enable_dashboard=True,
    dashboard_config={
        "host": "localhost",
        "port": 8080,
        "enable_metrics": True,
        "enable_logs": True
    }
)
```

## Exemplos de Uso

### Sistema de Blog

```python
import asyncio
from kairondb import SQLBridge, Model, StringField, IntegerField, DateTimeField

class Post(Model):
    id = IntegerField(primary_key=True)
    titulo = StringField(max_length=200, required=True)
    conteudo = StringField(required=True)
    autor_id = IntegerField(required=True)
    criado_em = DateTimeField(auto_now=True)

class Comentario(Model):
    id = IntegerField(primary_key=True)
    post_id = IntegerField(required=True)
    autor = StringField(max_length=100, required=True)
    texto = StringField(required=True)
    criado_em = DateTimeField(auto_now=True)

async def main():
    bridge = SQLBridge("sqlite3", "blog.db")
    await bridge.connect()
    
    # Criar post
    post = Post(
        titulo="Meu Primeiro Post",
        conteudo="Este é o conteúdo do post...",
        autor_id=1
    )
    await post.save(bridge)
    
    # Adicionar comentário
    comentario = Comentario(
        post_id=post.id,
        autor="João",
        texto="Ótimo post!"
    )
    await comentario.save(bridge)
    
    # Buscar posts com comentários
    posts = await Post.select(bridge)
    for post in posts:
        comentarios = await Comentario.select(bridge, where={"post_id": post.id})
        print(f"Post: {post.titulo} ({len(comentarios)} comentários)")
    
    await bridge.close()

asyncio.run(main())
```

### Sistema de E-commerce

```python
import asyncio
from kairondb import SQLBridge, Model, StringField, IntegerField, BooleanField

class Produto(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=200, required=True)
    preco = IntegerField(min_value=0, required=True)
    estoque = IntegerField(min_value=0, default=0)
    ativo = BooleanField(default=True)

class Pedido(Model):
    id = IntegerField(primary_key=True)
    cliente_email = StringField(required=True)
    total = IntegerField(min_value=0, required=True)
    status = StringField(default="pendente")

async def main():
    bridge = SQLBridge("sqlite3", "ecommerce.db")
    await bridge.connect()
    
    # Criar produtos
    produtos = [
        Produto(nome="Notebook", preco=250000, estoque=10),
        Produto(nome="Mouse", preco=5000, estoque=50),
        Produto(nome="Teclado", preco=15000, estoque=30)
    ]
    
    for produto in produtos:
        await produto.save(bridge)
    
    # Buscar produtos disponíveis
    produtos_ativos = await Produto.select(bridge, where={"ativo": True})
    print(f"Produtos disponíveis: {len(produtos_ativos)}")
    
    # Criar pedido
    pedido = Pedido(
        cliente_email="cliente@exemplo.com",
        total=270000
    )
    await pedido.save(bridge)
    
    print(f"Pedido {pedido.id} criado com total R$ {pedido.total/100:.2f}")
    
    await bridge.close()

asyncio.run(main())
```

---

Para mais exemplos e tutoriais, consulte a [documentação completa](README.md).

