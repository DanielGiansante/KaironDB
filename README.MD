# KaironDB

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/kairondb.svg)](https://pypi.org/project/kairondb/)
[![Downloads](https://img.shields.io/pypi/dm/kairondb.svg)](https://pypi.org/project/kairondb/)

**KaironDB** é um framework Python **simples**, **veloz** e **assíncrono** para conexão com bancos de dados SQL. Projetado para ser fácil de usar, mas com funcionalidades avançadas opcionais.

## ✨ Características Principais

- 🚀 **Simples e Intuitivo** - API limpa e fácil de aprender
- ⚡ **Alta Performance** - Backend em Go para máxima velocidade
- 🔄 **Assíncrono** - Suporte completo a `async/await`
- 🗄️ **Multi-Driver** - SQLite, PostgreSQL, MySQL, SQL Server
- 🏗️ **ORM Declarativo** - Modelos Python para mapeamento de dados
- 🔧 **Flexível** - Funcionalidades avançadas opcionais
- 🛡️ **Confiável** - Tratamento robusto de erros e edge cases

## 🚀 Instalação

```bash
pip install kairondb
```

## 📖 Guia Rápido

### Conexão Simples

```python
import asyncio
from kairondb import SQLBridge

async def main():
    # SQLite (mais simples)
    bridge = SQLBridge("sqlite3", "meu_banco.db")
    await bridge.connect()
    
    # PostgreSQL
    bridge = SQLBridge("postgres", "localhost", "meudb", "usuario", "senha")
    await bridge.connect()
    
    # Fechar conexão
    await bridge.close()

asyncio.run(main())
```

### Operações Básicas

```python
import asyncio
from kairondb import SQLBridge

async def main():
    bridge = SQLBridge("sqlite3", "exemplo.db")
    await bridge.connect()
    
    # Criar tabela
    await bridge.create_table("usuarios", {
        "id": "INTEGER PRIMARY KEY",
        "nome": "TEXT NOT NULL",
        "email": "TEXT UNIQUE",
        "idade": "INTEGER"
    })
    
    # Inserir dados
    await bridge.insert("usuarios", {
        "nome": "João Silva",
        "email": "joao@exemplo.com",
        "idade": 30
    })
    
    # Consultar dados
    usuarios = await bridge.select("usuarios")
    print(f"Encontrados {len(usuarios)} usuários")
    
    # Buscar específico
    usuario = await bridge.get("usuarios", {"email": "joao@exemplo.com"})
    print(f"Usuário: {usuario['nome']}")
    
    # Atualizar
    await bridge.update("usuarios", {"idade": 31}, {"email": "joao@exemplo.com"})
    
    # Deletar
    await bridge.delete("usuarios", {"email": "joao@exemplo.com"})
    
    # Contar registros
    total = await bridge.count("usuarios")
    print(f"Total: {total} usuários")
    
    await bridge.close()

asyncio.run(main())
```

### Usando Modelos (ORM)

```python
import asyncio
from kairondb import SQLBridge, Model, StringField, IntegerField, EmailField

# Definir modelo
class Usuario(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=100, required=True)
    email = EmailField(required=True)
    idade = IntegerField(min_value=0, max_value=120)

async def main():
    bridge = SQLBridge("sqlite3", "exemplo_orm.db")
    await bridge.connect()
    
    # Criar usuário
    usuario = Usuario(nome="Maria Santos", email="maria@exemplo.com", idade=25)
    await usuario.save(bridge)
    
    # Consultar todos
    usuarios = await Usuario.select(bridge)
    print(f"Encontrados {len(usuarios)} usuários")
    
    # Buscar específico
    usuario = await Usuario.get({"email": "maria@exemplo.com"}, bridge)
    print(f"Usuário: {usuario.nome}")
    
    # Atualizar
    usuario.idade = 26
    await usuario.update()
    
    # Deletar
    await usuario.delete()
    
    await bridge.close()

asyncio.run(main())
```

## 🔧 API de Conveniência

### Métodos Úteis

```python
# Verificar se existe
existe = await bridge.exists("usuarios", {"email": "joao@exemplo.com"})

# Obter ou criar
usuario = await bridge.get_or_create(
    "usuarios", 
    {"email": "joao@exemplo.com"}, 
    {"nome": "João Silva", "idade": 30}
)

# Contar com filtro
jovens = await bridge.count("usuarios", {"idade": 30})
```

### Métodos de Modelo

```python
# Verificar se existe
existe = await Usuario.exists({"email": "joao@exemplo.com"}, bridge)

# Obter ou criar
usuario = await Usuario.get_or_create(
    {"email": "joao@exemplo.com"}, 
    {"nome": "João Silva", "idade": 30}, 
    bridge
)

# Contar com filtro
jovens = await Usuario.count({"idade": 30}, bridge)
```

## 🗄️ Drivers Suportados

### SQLite
```python
# Arquivo
bridge = SQLBridge("sqlite3", "banco.db")

# Memória
bridge = SQLBridge("sqlite3", ":memory:")
```

### PostgreSQL
```python
bridge = SQLBridge("postgres", "localhost", "meudb", "usuario", "senha")
```

### MySQL
```python
bridge = SQLBridge("mysql", "localhost", "meudb", "usuario", "senha")
```

### SQL Server
```python
bridge = SQLBridge("sqlserver", "localhost", "meudb", "usuario", "senha")
```

## 🏗️ Tipos de Campo

```python
from kairondb import StringField, IntegerField, BooleanField, DateTimeField, EmailField

class Produto(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=200, required=True)
    preco = IntegerField(min_value=0)
    ativo = BooleanField(default=True)
    email = EmailField(required=True)
    criado_em = DateTimeField(auto_now=True)
```

## ⚡ Performance

KaironDB é otimizado para alta performance:

- **INSERT**: ~7ms por operação
- **SELECT**: ~1ms por operação
- **COUNT**: ~0.2ms por operação
- **GET**: ~0.3ms por operação

## 🔄 Operações Concorrentes

```python
import asyncio

async def operacao_concorrente(id_usuario):
    bridge = SQLBridge("sqlite3", "concorrente.db")
    await bridge.connect()
    
    await bridge.insert("usuarios", {
        "id": id_usuario,
        "nome": f"Usuário {id_usuario}",
        "email": f"user{id_usuario}@exemplo.com"
    })
    
    await bridge.close()

# Executar 10 operações concorrentes
async def main():
    tasks = [operacao_concorrente(i) for i in range(10)]
    await asyncio.gather(*tasks)

asyncio.run(main())
```

## 🛡️ Tratamento de Erros

```python
try:
    bridge = SQLBridge("postgres", "servidor_inexistente", "db", "user", "pass")
    await bridge.connect()
except Exception as e:
    print(f"Erro de conexão: {e}")

# Operações retornam dicionários de erro em caso de falha
resultado = await bridge.select("tabela_inexistente")
if isinstance(resultado, dict) and "error" in resultado:
    print(f"Erro: {resultado['error']}")
```

## 📚 Exemplos Avançados

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

async def sistema_blog():
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

asyncio.run(sistema_blog())
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

async def sistema_ecommerce():
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

asyncio.run(sistema_ecommerce())
```

## 🔧 Configuração Avançada

### Pool de Conexões

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
        "connection_timeout": 30
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
        "ttl": 300  # 5 minutos
    }
)
```

## 📖 Documentação Completa

- [Guia de Instalação](docs/installation.md)
- [Referência da API](docs/api-reference.md)
- [Exemplos Práticos](docs/examples.md)
- [Guia de Migração](docs/migration.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja nosso [Guia de Contribuição](CONTRIBUTING.md).

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## 🆘 Suporte

- 📧 Email: suporte@kairondb.com
- 🐛 Issues: [GitHub Issues](https://github.com/kairondb/kairondb/issues)
- 📖 Docs: [Documentação Completa](https://docs.kairondb.com)

---

**KaironDB** - Simples, Rápido e Assíncrono! 🚀