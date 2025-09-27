# Exemplos Práticos - KaironDB

## Índice

- [Sistema de Blog](#sistema-de-blog)
- [E-commerce](#e-commerce)
- [Sistema de Usuários](#sistema-de-usuários)
- [API REST](#api-rest)
- [Sistema de Notificações](#sistema-de-notificações)

## Sistema de Blog

### Modelos

```python
import asyncio
from datetime import datetime
from kairondb import SQLBridge, Model, StringField, IntegerField, DateTimeField, BooleanField

class Usuario(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=100, required=True)
    email = StringField(required=True)
    ativo = BooleanField(default=True)
    criado_em = DateTimeField(auto_now=True)

class Post(Model):
    id = IntegerField(primary_key=True)
    titulo = StringField(max_length=200, required=True)
    conteudo = StringField(required=True)
    autor_id = IntegerField(required=True)
    publicado = BooleanField(default=False)
    criado_em = DateTimeField(auto_now=True)
    atualizado_em = DateTimeField(auto_now=True)

class Comentario(Model):
    id = IntegerField(primary_key=True)
    post_id = IntegerField(required=True)
    autor_nome = StringField(max_length=100, required=True)
    autor_email = StringField(required=True)
    texto = StringField(required=True)
    aprovado = BooleanField(default=False)
    criado_em = DateTimeField(auto_now=True)
```

### Implementação

```python
async def sistema_blog():
    bridge = SQLBridge("sqlite3", "blog.db")
    await bridge.connect()
    
    # Criar usuário
    autor = Usuario(nome="João Silva", email="joao@exemplo.com")
    await autor.save(bridge)
    
    # Criar post
    post = Post(
        titulo="Introdução ao KaironDB",
        conteudo="KaironDB é um framework Python simples e rápido...",
        autor_id=autor.id,
        publicado=True
    )
    await post.save(bridge)
    
    # Adicionar comentários
    comentarios = [
        Comentario(
            post_id=post.id,
            autor_nome="Maria",
            autor_email="maria@exemplo.com",
            texto="Ótimo post! Muito útil.",
            aprovado=True
        ),
        Comentario(
            post_id=post.id,
            autor_nome="Pedro",
            autor_email="pedro@exemplo.com",
            texto="Quando terá mais tutoriais?",
            aprovado=True
        )
    ]
    
    for comentario in comentarios:
        await comentario.save(bridge)
    
    # Buscar posts publicados
    posts = await Post.select(bridge, where={"publicado": True})
    print(f"Posts publicados: {len(posts)}")
    
    # Buscar comentários aprovados de um post
    comentarios_aprovados = await Comentario.select(
        bridge, 
        where={"post_id": post.id, "aprovado": True}
    )
    print(f"Comentários aprovados: {len(comentarios_aprovados)}")
    
    await bridge.close()

asyncio.run(sistema_blog())
```

## E-commerce

### Modelos

```python
class Produto(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=200, required=True)
    descricao = StringField()
    preco = IntegerField(min_value=0, required=True)  # Em centavos
    estoque = IntegerField(min_value=0, default=0)
    categoria = StringField(max_length=100)
    ativo = BooleanField(default=True)
    criado_em = DateTimeField(auto_now=True)

class Cliente(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=100, required=True)
    email = StringField(required=True)
    telefone = StringField(max_length=20)
    endereco = StringField()
    ativo = BooleanField(default=True)
    criado_em = DateTimeField(auto_now=True)

class Pedido(Model):
    id = IntegerField(primary_key=True)
    cliente_id = IntegerField(required=True)
    total = IntegerField(min_value=0, required=True)
    status = StringField(default="pendente")
    data_pedido = DateTimeField(auto_now=True)
    data_entrega = DateTimeField()

class ItemPedido(Model):
    id = IntegerField(primary_key=True)
    pedido_id = IntegerField(required=True)
    produto_id = IntegerField(required=True)
    quantidade = IntegerField(min_value=1, required=True)
    preco_unitario = IntegerField(min_value=0, required=True)
```

### Implementação

```python
async def sistema_ecommerce():
    bridge = SQLBridge("sqlite3", "ecommerce.db")
    await bridge.connect()
    
    # Criar produtos
    produtos = [
        Produto(nome="Notebook Dell", descricao="Notebook para trabalho", preco=250000, estoque=10, categoria="Informática"),
        Produto(nome="Mouse Logitech", descricao="Mouse sem fio", preco=5000, estoque=50, categoria="Acessórios"),
        Produto(nome="Teclado Mecânico", descricao="Teclado RGB", preco=15000, estoque=30, categoria="Acessórios")
    ]
    
    for produto in produtos:
        await produto.save(bridge)
    
    # Criar cliente
    cliente = Cliente(
        nome="Maria Santos",
        email="maria@exemplo.com",
        telefone="(11) 99999-9999",
        endereco="Rua das Flores, 123"
    )
    await cliente.save(bridge)
    
    # Criar pedido
    pedido = Pedido(
        cliente_id=cliente.id,
        total=270000,  # R$ 2.700,00
        status="pendente"
    )
    await pedido.save(bridge)
    
    # Adicionar itens ao pedido
    itens = [
        ItemPedido(pedido_id=pedido.id, produto_id=1, quantidade=1, preco_unitario=250000),
        ItemPedido(pedido_id=pedido.id, produto_id=2, quantidade=2, preco_unitario=5000),
        ItemPedido(pedido_id=pedido.id, produto_id=3, quantidade=1, preco_unitario=15000)
    ]
    
    for item in itens:
        await item.save(bridge)
    
    # Buscar pedidos de um cliente
    pedidos_cliente = await Pedido.select(bridge, where={"cliente_id": cliente.id})
    print(f"Pedidos do cliente: {len(pedidos_cliente)}")
    
    # Buscar produtos por categoria
    produtos_acessorios = await Produto.select(bridge, where={"categoria": "Acessórios"})
    print(f"Produtos de acessórios: {len(produtos_acessorios)}")
    
    await bridge.close()

asyncio.run(sistema_ecommerce())
```

## Sistema de Usuários

### Modelos

```python
class Usuario(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=100, required=True)
    email = StringField(required=True)
    senha_hash = StringField(required=True)
    ativo = BooleanField(default=True)
    admin = BooleanField(default=False)
    criado_em = DateTimeField(auto_now=True)
    ultimo_login = DateTimeField()

class Perfil(Model):
    id = IntegerField(primary_key=True)
    usuario_id = IntegerField(required=True)
    bio = StringField()
    avatar_url = StringField()
    telefone = StringField(max_length=20)
    endereco = StringField()
    data_nascimento = DateTimeField()

class Sessao(Model):
    id = IntegerField(primary_key=True)
    usuario_id = IntegerField(required=True)
    token = StringField(required=True)
    expira_em = DateTimeField(required=True)
    ativa = BooleanField(default=True)
    criada_em = DateTimeField(auto_now=True)
```

### Implementação

```python
import hashlib
from datetime import datetime, timedelta

async def sistema_usuarios():
    bridge = SQLBridge("sqlite3", "usuarios.db")
    await bridge.connect()
    
    # Criar usuário
    senha_hash = hashlib.sha256("minhasenha123".encode()).hexdigest()
    usuario = Usuario(
        nome="João Silva",
        email="joao@exemplo.com",
        senha_hash=senha_hash,
        admin=True
    )
    await usuario.save(bridge)
    
    # Criar perfil
    perfil = Perfil(
        usuario_id=usuario.id,
        bio="Desenvolvedor Python",
        telefone="(11) 99999-9999",
        endereco="São Paulo, SP"
    )
    await perfil.save(bridge)
    
    # Criar sessão
    token = hashlib.sha256(f"{usuario.id}{datetime.now()}".encode()).hexdigest()
    sessao = Sessao(
        usuario_id=usuario.id,
        token=token,
        expira_em=datetime.now() + timedelta(hours=24)
    )
    await sessao.save(bridge)
    
    # Buscar usuário com perfil
    usuario_completo = await Usuario.get({"email": "joao@exemplo.com"}, bridge)
    perfil_usuario = await Perfil.get({"usuario_id": usuario_completo.id}, bridge)
    
    print(f"Usuário: {usuario_completo.nome}")
    print(f"Bio: {perfil_usuario.bio}")
    
    # Verificar sessão ativa
    sessao_ativa = await Sessao.get({"token": token, "ativa": True}, bridge)
    if sessao_ativa:
        print("Sessão ativa encontrada")
    
    await bridge.close()

asyncio.run(sistema_usuarios())
```

## API REST

### FastAPI + KaironDB

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from kairondb import SQLBridge, Model, StringField, IntegerField, BooleanField

# Modelos
class Usuario(Model):
    id = IntegerField(primary_key=True)
    nome = StringField(max_length=100, required=True)
    email = StringField(required=True)
    ativo = BooleanField(default=True)

# Schemas Pydantic
class UsuarioCreate(BaseModel):
    nome: str
    email: str

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    ativo: bool

# Configuração
app = FastAPI()
bridge = None

@app.on_event("startup")
async def startup():
    global bridge
    bridge = SQLBridge("sqlite3", "api.db")
    await bridge.connect()

@app.on_event("shutdown")
async def shutdown():
    global bridge
    if bridge:
        await bridge.close()

# Endpoints
@app.post("/usuarios", response_model=UsuarioResponse)
async def criar_usuario(usuario_data: UsuarioCreate):
    usuario = Usuario(nome=usuario_data.nome, email=usuario_data.email)
    await usuario.save(bridge)
    return UsuarioResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        ativo=usuario.ativo
    )

@app.get("/usuarios", response_model=List[UsuarioResponse])
async def listar_usuarios():
    usuarios = await Usuario.select(bridge)
    return [
        UsuarioResponse(
            id=u.id,
            nome=u.nome,
            email=u.email,
            ativo=u.ativo
        ) for u in usuarios
    ]

@app.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(usuario_id: int):
    usuario = await Usuario.get({"id": usuario_id}, bridge)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return UsuarioResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        ativo=usuario.ativo
    )

@app.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def atualizar_usuario(usuario_id: int, usuario_data: UsuarioCreate):
    usuario = await Usuario.get({"id": usuario_id}, bridge)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    usuario.nome = usuario_data.nome
    usuario.email = usuario_data.email
    await usuario.update()
    
    return UsuarioResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        ativo=usuario.ativo
    )

@app.delete("/usuarios/{usuario_id}")
async def deletar_usuario(usuario_id: int):
    usuario = await Usuario.get({"id": usuario_id}, bridge)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await usuario.delete()
    return {"message": "Usuário deletado com sucesso"}

# Executar
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Sistema de Notificações

### Modelos

```python
class Notificacao(Model):
    id = IntegerField(primary_key=True)
    usuario_id = IntegerField(required=True)
    titulo = StringField(max_length=200, required=True)
    mensagem = StringField(required=True)
    tipo = StringField(max_length=50, required=True)  # info, warning, error, success
    lida = BooleanField(default=False)
    criada_em = DateTimeField(auto_now=True)

class ConfiguracaoNotificacao(Model):
    id = IntegerField(primary_key=True)
    usuario_id = IntegerField(required=True)
    tipo = StringField(max_length=50, required=True)
    habilitada = BooleanField(default=True)
    email = BooleanField(default=True)
    push = BooleanField(default=True)
```

### Implementação

```python
async def sistema_notificacoes():
    bridge = SQLBridge("sqlite3", "notificacoes.db")
    await bridge.connect()
    
    # Criar configurações de notificação
    config = ConfiguracaoNotificacao(
        usuario_id=1,
        tipo="info",
        habilitada=True,
        email=True,
        push=True
    )
    await config.save(bridge)
    
    # Criar notificações
    notificacoes = [
        Notificacao(
            usuario_id=1,
            titulo="Bem-vindo!",
            mensagem="Seja bem-vindo ao nosso sistema!",
            tipo="info"
        ),
        Notificacao(
            usuario_id=1,
            titulo="Atualização disponível",
            mensagem="Uma nova versão está disponível para download.",
            tipo="warning"
        ),
        Notificacao(
            usuario_id=1,
            titulo="Pagamento confirmado",
            mensagem="Seu pagamento foi processado com sucesso.",
            tipo="success"
        )
    ]
    
    for notif in notificacoes:
        await notif.save(bridge)
    
    # Buscar notificações não lidas
    notificacoes_nao_lidas = await Notificacao.select(
        bridge, 
        where={"usuario_id": 1, "lida": False}
    )
    print(f"Notificações não lidas: {len(notificacoes_nao_lidas)}")
    
    # Marcar como lida
    if notificacoes_nao_lidas:
        notif = notificacoes_nao_lidas[0]
        notif.lida = True
        await notif.update()
        print("Notificação marcada como lida")
    
    # Buscar por tipo
    notificacoes_info = await Notificacao.select(
        bridge, 
        where={"usuario_id": 1, "tipo": "info"}
    )
    print(f"Notificações de info: {len(notificacoes_info)}")
    
    await bridge.close()

asyncio.run(sistema_notificacoes())
```

---

Para mais exemplos e tutoriais, consulte a [documentação completa](README.md).

