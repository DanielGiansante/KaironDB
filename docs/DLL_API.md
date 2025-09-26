# KaironDB DLL API Documentation

## Visão Geral

A KaironDB utiliza uma DLL (Dynamic Link Library) escrita em Go para realizar as operações de banco de dados. Esta DLL fornece uma interface C compatível que permite integração com Python através da biblioteca `ctypes`.

## Arquivos da DLL

- **Windows**: `sqlbridge.dll`
- **Linux/macOS**: `sqlbridge.so`

## Funções Disponíveis

### 1. CreatePool

**Assinatura C:**
```c
char* CreatePool(char* connection_params_json);
```

**Descrição:**
Cria um novo pool de conexões com o banco de dados.

**Parâmetros:**
- `connection_params_json`: String JSON contendo os parâmetros de conexão

**Retorno:**
- **Sucesso**: String contendo o ID do pool criado
- **Erro**: String JSON contendo informações do erro

**Exemplo de Parâmetros JSON:**
```json
{
    "driver": "postgres",
    "server": "localhost:5432",
    "name": "mydatabase",
    "user": "username",
    "password": "password"
}
```

**Drivers Suportados:**
- `postgres`: PostgreSQL
- `sqlserver`: Microsoft SQL Server
- `mysql`: MySQL
- `sqlite3`: SQLite

### 2. ClosePool

**Assinatura C:**
```c
void ClosePool(char* pool_id);
```

**Descrição:**
Fecha um pool de conexões e libera todos os recursos associados.

**Parâmetros:**
- `pool_id`: ID do pool a ser fechado

**Retorno:**
- Nenhum (void)

### 3. ExecuteSQL_async

**Assinatura C:**
```c
void ExecuteSQL_async(
    char* pool_id,
    char* request_json,
    char* transaction_id,
    CallbackFunction callback,
    char* request_id
);
```

**Descrição:**
Executa uma operação SQL de forma assíncrona.

**Parâmetros:**
- `pool_id`: ID do pool de conexões
- `request_json`: String JSON contendo a requisição SQL
- `transaction_id`: ID da transação (opcional, pode ser vazio)
- `callback`: Função de callback para retornar o resultado
- `request_id`: ID único da requisição

**Estrutura da Requisição JSON:**
```json
{
    "operation": "select|insert|update|delete|exec",
    "table": "nome_da_tabela",
    "fields": ["campo1", "campo2"],
    "where_q": {
        "connector": "AND|OR",
        "children": [...]
    },
    "joins": [...],
    "data": {...},
    "sql": "SELECT * FROM tabela",
    "params": [...],
    "expect_result": true
}
```

### 4. BeginTransaction (Opcional)

**Assinatura C:**
```c
char* BeginTransaction(char* pool_id);
```

**Descrição:**
Inicia uma nova transação no pool especificado.

**Parâmetros:**
- `pool_id`: ID do pool de conexões

**Retorno:**
- **Sucesso**: ID da transação criada
- **Erro**: String JSON contendo informações do erro

### 5. CommitTransaction (Opcional)

**Assinatura C:**
```c
void CommitTransaction(char* transaction_id);
```

**Descrição:**
Confirma uma transação.

**Parâmetros:**
- `transaction_id`: ID da transação a ser confirmada

### 6. RollbackTransaction (Opcional)

**Assinatura C:**
```c
void RollbackTransaction(char* transaction_id);
```

**Descrição:**
Desfaz uma transação.

**Parâmetros:**
- `transaction_id`: ID da transação a ser desfeita

### 7. FreeCString (Opcional)

**Assinatura C:**
```c
void FreeCString(char* cstring);
```

**Descrição:**
Libera memória alocada para strings C retornadas pela DLL.

**Parâmetros:**
- `cstring`: Ponteiro para a string a ser liberada

## Tipos de Dados

### CallbackFunction

**Assinatura C:**
```c
typedef void (*CallbackFunction)(char* result, char* request_id);
```

**Descrição:**
Tipo de função para callbacks assíncronos.

**Parâmetros:**
- `result`: Resultado da operação em formato JSON
- `request_id`: ID da requisição que gerou o resultado

## Códigos de Erro

A DLL retorna erros em formato JSON com a seguinte estrutura:

```json
{
    "error": "Descrição do erro",
    "code": "CÓDIGO_DO_ERRO",
    "details": {
        "field": "campo_específico",
        "value": "valor_problemático"
    }
}
```

### Códigos de Erro Comuns

- `CONNECTION_FAILED`: Falha na conexão com o banco
- `INVALID_DRIVER`: Driver de banco não suportado
- `INVALID_PARAMS`: Parâmetros de conexão inválidos
- `POOL_CREATION_FAILED`: Falha ao criar pool de conexões
- `QUERY_EXECUTION_FAILED`: Falha na execução da query
- `TRANSACTION_FAILED`: Falha na operação de transação

## Exemplo de Uso com ctypes

```python
import ctypes
import json

# Carregar a DLL
dll = ctypes.cdll.LoadLibrary("sqlbridge.dll")

# Definir tipos de função
dll.CreatePool.argtypes = [ctypes.c_char_p]
dll.CreatePool.restype = ctypes.c_char_p

dll.ClosePool.argtypes = [ctypes.c_char_p]

# Definir callback
CALLBACK_FUNC_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)

def callback(result, request_id):
    print(f"Resultado: {result.decode('utf-8')}")

# Criar pool
params = {
    "driver": "postgres",
    "server": "localhost:5432",
    "name": "mydb",
    "user": "user",
    "password": "pass"
}

params_json = json.dumps(params).encode('utf-8')
pool_id = dll.CreatePool(params_json)
print(f"Pool criado: {pool_id.decode('utf-8')}")

# Fechar pool
dll.ClosePool(pool_id)
```

## Requisitos do Sistema

### Windows
- Visual C++ Redistributable 2015 ou superior
- .NET Framework 4.7.2 ou superior (para SQL Server)

### Linux
- glibc 2.17 ou superior
- libc6-dev

### macOS
- macOS 10.12 ou superior

## Troubleshooting

### Erro: "DLL not found"
- Verifique se o arquivo `sqlbridge.dll` (Windows) ou `sqlbridge.so` (Linux/macOS) está no diretório correto
- Verifique se o arquivo tem permissões de execução

### Erro: "Invalid driver"
- Verifique se o driver especificado está na lista de drivers suportados
- Para SQLite, certifique-se de que o arquivo de banco existe

### Erro: "Connection failed"
- Verifique se o servidor de banco está rodando
- Verifique se os parâmetros de conexão estão corretos
- Verifique se há conectividade de rede

### Erro: "Pool creation failed"
- Verifique se há recursos suficientes no sistema
- Verifique se não há muitos pools abertos simultaneamente

## Performance

### Recomendações
- Use pools de conexões para melhor performance
- Feche pools quando não precisar mais deles
- Use transações para operações que precisam ser atômicas
- Evite criar muitos pools simultâneos

### Limites
- Máximo de 100 pools por processo
- Máximo de 1000 conexões por pool
- Timeout padrão de 30 segundos para operações

## Segurança

### Considerações
- Nunca hardcode credenciais no código
- Use variáveis de ambiente para senhas
- Valide todos os inputs antes de enviar para a DLL
- Use prepared statements quando possível

### Exemplo Seguro
```python
import os
from kairondb import SQLBridge

# Usar variáveis de ambiente
bridge = SQLBridge(
    driver="postgres",
    server=os.getenv("DB_HOST", "localhost"),
    db_name=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
```
