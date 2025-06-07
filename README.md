
# 📦 KaironDB                                      


**KaironDB** é uma biblioteca Python que atua como uma ponte (_bridge_) para executar operações SQL em múltiplos bancos de dados (_SQL Server, MySQL, PostgreSQL_) de forma **simples** e **performática**.

---

## ✨ Principais Funcionalidades

- ✅ **Interface Pythonica Simples**  
  Interaja com o banco usando classes e métodos intuitivos.

- 🔌 **Suporte a Múltiplos Bancos**  
  Compatível com **SQL Server**, **MySQL** e **PostgreSQL**.

- 🛠️ **Métodos de Alto Nível (ORM-like)**  
  Use `.select()`, `.insert()`, `.update()`, `.delete()` para tarefas comuns.

- 🧪 **Execução de SQL Bruto**  
  Use `.exec()` para executar qualquer query SQL personalizada.

- ⚙️ **Configuração Direta**  
  Configure sem variáveis de ambiente — apenas argumentos Python.

---

## ⚙️ Pré-requisitos

- Python **3.7+**

---

## 🚀 Instalação

Instale via `pip` usando o arquivo `.whl` fornecido:

```bash
pip install kairondb-0.1.0-py3-none-any.whl
```

> (O nome do arquivo pode variar conforme a versão.)

---

## 🔌 Configuração da Conexão

A conexão é configurada ao instanciar a classe `SQLBridge`:

```python
from kairondb import SQLBridge

bridge = SQLBridge(
    driver="sqlserver",      # "mysql" ou "postgres"
    server="192.168.0.100",
    db_name="meu_banco",
    user="meu_usuario",
    password="minha_senha_super_secreta"
)
```

---

## ⚡ Guia de Uso Rápido

```python
from kairondb import SQLBridge, Model

# 1. Instanciando a conexão
bridge = SQLBridge(
    driver="sqlserver",
    server="SEU_SERVIDOR",
    db_name="SEU_BANCO",
    user="SEU_USUARIO",
    password="SUA_SENHA"
)

# 2. Criando modelos de tabelas
user_model = Model(bridge, "Usuarios")
products_model = Model(bridge, "Produtos")

# 3. Operações SQL de alto nível

# SELECT * FROM Usuarios
print("Buscando todos os usuários:")
todos_usuarios = user_model.select()
if isinstance(todos_usuarios, list):
    print(todos_usuarios)

# SELECT id, nome FROM Usuarios WHERE id = 1
print("\nBuscando usuário com id=1:")
usuario_1 = user_model.select(fields=["id", "nome"], where={"id": 1})
print(usuario_1)

# INSERT INTO Usuarios ...
print("\nInserindo novo usuário:")
resultado_insert = user_model.insert({"nome": "novo_usuario", "email": "novo@email.com"})
print(resultado_insert)  # {'rows_affected': 1}

# UPDATE Usuarios ...
print("\nAtualizando usuário:")
resultado_update = user_model.update(data={"status": "ativo"}, where={"id": 1})
print(resultado_update)

# 4. Executando SQL bruto
print("\nExecutando SQL bruto:")
contagem = bridge.exec("SELECT COUNT(*) as total FROM Produtos", expect_result=True)
print(contagem)  # [{'total': 150}]
```

---

## 📘 Referência da API

### 🔧 `SQLBridge`

Classe principal de conexão.

```python
SQLBridge(driver, server, db_name, user, password)
```

#### Métodos:

- `.exec(sql, params=None, expect_result=False)`
  - `sql`: string SQL com `?` como placeholders.
  - `params`: lista de valores para os `?`.
  - `expect_result`: `True` para SELECT, `False` para INSERT/UPDATE/DELETE.

---

### 📦 `Model`

Classe para interação com uma tabela específica.

```python
Model(bridge, table_name)
```

#### Métodos:

- `.select(fields=None, where=None, joins=None)`  
  Executa um SELECT.  
  - `fields`: lista de colunas (ex: `['id', 'nome']`), padrão: `['*']`  
  - `where`: dicionário de condições (ex: `{'id': 1}`)  
  - `joins`: não implementado (futuro)

- `.insert(data)`  
  Executa um INSERT.  
  - `data`: dicionário com os dados (ex: `{'nome': 'João'}`)

- `.update(data, where)`  
  Executa um UPDATE.  
  - `data`: novos valores  
  - `where`: condições para localizar os registros

- `.delete(where)`  
  Executa um DELETE.  
  - `where`: condições para localizar os registros

---

## 🚨 Tratamento de Erros

Se ocorrer um erro, o método retorna um dicionário com a chave `error`:

```python
resultado = user_model.insert({"id": 1, "nome": "usuario_duplicado"})

if isinstance(resultado, dict) and "error" in resultado:
    print(f"Erro de banco: {resultado['error']}")
else:
    print("Operação realizada com sucesso!")
```

---

## 📄 Licença

Distribuído sob a **Licença MIT**.



