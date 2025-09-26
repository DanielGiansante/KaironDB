"""
Tipos customizados para KaironDB
"""

from typing import (
    Any, Dict, List, Optional, Union, Callable, Type, TypeVar, Generic,
    Protocol, TypedDict, Literal, Tuple, Set, FrozenSet, Iterator, AsyncIterator
)
from datetime import datetime
import ctypes

# Type aliases básicos
DriverType = Literal["postgres", "sqlserver", "mysql", "sqlite3"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
FieldType = Literal["string", "integer", "datetime", "boolean", "float"]

# Tipos para parâmetros de conexão
class ConnectionParams(TypedDict, total=False):
    """Parâmetros de conexão com banco de dados."""
    driver: str
    server: str
    name: str
    user: str
    password: str
    port: Optional[int]
    sslmode: Optional[str]
    charset: Optional[str]
    instance: Optional[str]

# Tipos para metadados de modelo
class ModelMeta(TypedDict):
    """Metadados de um modelo."""
    fields: Dict[str, 'Field']
    table_name: str

# Tipos para campos
FieldValue = Union[str, int, float, bool, datetime, None]
FieldDefault = Union[FieldValue, Callable[[], FieldValue]]

# Tipos para validação
ValidationResult = Tuple[bool, Optional[str]]
ValidatorFunction = Callable[[Any, str], None]

# Tipos para queries
QueryCondition = Union[Dict[str, Any], 'Q']
QueryFields = Union[List[str], Literal["*"]]
QueryJoins = List[Dict[str, Any]]

# Tipos para resultados de query
QueryResult = Dict[str, Any]
QueryResults = List[QueryResult]

# Tipos para transações
TransactionID = str
PoolID = str

# Tipos para callbacks
CallbackFunction = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)

# Tipos para bridge
class BridgeConfig(TypedDict, total=False):
    """Configuração da bridge."""
    debug: bool
    lib_path: Optional[str]
    timeout: Optional[float]
    max_connections: Optional[int]
    min_connections: Optional[int]

# Tipos para logging
class LogRecord(TypedDict):
    """Registro de log."""
    timestamp: datetime
    level: LogLevel
    message: str
    module: str
    function: str
    line: int

# Tipos para validação de campos
class ValidationErrorInfo(TypedDict):
    """Erro de validação."""
    field_name: str
    field_value: Any
    error_message: str
    error_code: Optional[str]

# Tipos para operações de banco
DatabaseOperation = Literal["select", "insert", "update", "delete", "create_table", "drop_table"]
class DatabaseResult(TypedDict):
    """Resultado de operação de banco."""
    success: bool
    data: Optional[QueryResults]
    error: Optional[str]
    affected_rows: Optional[int]
    last_insert_id: Optional[int]

# Tipos para configuração de campo
class FieldConfig(TypedDict, total=False):
    """Configuração de campo."""
    required: bool
    default: Optional[FieldDefault]
    primary_key: bool
    max_length: Optional[int]
    min_length: Optional[int]
    max_value: Optional[Union[int, float]]
    min_value: Optional[Union[int, float]]
    auto_now_add: bool
    auto_now: bool
    choices: Optional[List[Any]]
    validators: Optional[List[ValidatorFunction]]

# Tipos para utilitários
class PlatformInfo(TypedDict):
    """Informações da plataforma."""
    system: str
    release: str
    version: str
    machine: str
    processor: str
    python_version: str
    architecture: str

# TypeVar para modelos
ModelT = TypeVar('ModelT', bound='Model')

# Protocolos
class FieldProtocol(Protocol):
    """Protocolo para campos."""
    name: Optional[str]
    required: bool
    default: Optional[FieldDefault]
    primary_key: bool
    
    def validate(self, value: Any) -> None:
        """Valida o valor do campo."""
        ...
    
    def get_default(self) -> Any:
        """Retorna o valor padrão."""
        ...

class ModelProtocol(Protocol):
    """Protocolo para modelos."""
    _meta: ModelMeta
    _data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        ...
    
    @classmethod
    def from_dict(cls: Type[ModelT], data: Dict[str, Any]) -> ModelT:
        """Cria a partir de dicionário."""
        ...

class BridgeProtocol(Protocol):
    """Protocolo para bridge."""
    driver: str
    conn_params: ConnectionParams
    pool_id: Optional[PoolID]
    debug: bool
    
    async def select(
        self, 
        table: str, 
        fields: Optional[QueryFields] = None,
        where: Optional[QueryCondition] = None,
        joins: Optional[QueryJoins] = None
    ) -> QueryResults:
        """Executa SELECT."""
        ...
    
    async def insert(self, table: str, data: Dict[str, Any]) -> DatabaseResult:
        """Executa INSERT."""
        ...
    
    async def update(
        self, 
        table: str, 
        data: Dict[str, Any], 
        where: Optional[QueryCondition] = None
    ) -> DatabaseResult:
        """Executa UPDATE."""
        ...
    
    async def delete(self, table: str, where: Optional[QueryCondition] = None) -> DatabaseResult:
        """Executa DELETE."""
        ...
    
    async def close(self) -> None:
        """Fecha a conexão."""
        ...

# Tipos para async generators
AsyncQueryResult = AsyncIterator[QueryResult]
AsyncModelResult = AsyncIterator[ModelT]

# Tipos para configuração de validação
class ValidationConfig(TypedDict, total=False):
    """Configuração de validação."""
    stop_on_first_error: bool
    include_field_names: bool
    include_field_values: bool
    custom_messages: Optional[Dict[str, str]]

# Tipos para métricas
class Metrics(TypedDict):
    """Métricas do sistema."""
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_query_time: float
    active_connections: int
    pool_size: int

# Tipos para cache
CacheKey = Union[str, Tuple[str, ...]]
CacheValue = Any
CacheTTL = int  # Time to live in seconds

# Tipos para migrations
class Migration(TypedDict):
    """Migração de banco."""
    version: str
    name: str
    up_sql: str
    down_sql: str
    dependencies: List[str]

# Tipos para índices
class Index(TypedDict):
    """Índice de banco."""
    name: str
    table: str
    columns: List[str]
    unique: bool
    type: Optional[str]

# Tipos para constraints
class Constraint(TypedDict):
    """Constraint de banco."""
    name: str
    table: str
    type: Literal["primary_key", "foreign_key", "unique", "check", "not_null"]
    columns: List[str]
    references: Optional[Dict[str, str]]
    condition: Optional[str]

# Tipos para schema
class Schema(TypedDict):
    """Schema de banco."""
    tables: List[str]
    indexes: List[Index]
    constraints: List[Constraint]
    views: List[str]
    functions: List[str]

# Tipos para backup
class BackupInfo(TypedDict):
    """Informações de backup."""
    timestamp: datetime
    size: int
    tables: List[str]
    format: Literal["sql", "csv", "json"]
    compressed: bool

# Tipos para monitoramento
class HealthCheck(TypedDict):
    """Health check do sistema."""
    status: Literal["healthy", "degraded", "unhealthy"]
    checks: Dict[str, bool]
    timestamp: datetime
    response_time: float

# Tipos para configuração de pool
class PoolConfig(TypedDict, total=False):
    """Configuração do pool de conexões."""
    min_connections: int
    max_connections: int
    connection_timeout: float
    idle_timeout: float
    max_lifetime: float
    health_check_interval: float

# Tipos para retry
class RetryConfig(TypedDict, total=False):
    """Configuração de retry."""
    max_attempts: int
    base_delay: float
    max_delay: float
    exponential_backoff: bool
    jitter: bool

# Tipos para logging de queries
class QueryLog(TypedDict):
    """Log de query."""
    timestamp: datetime
    query: str
    params: List[Any]
    duration: float
    success: bool
    error: Optional[str]

# Tipos para auditoria
class AuditLog(TypedDict):
    """Log de auditoria."""
    timestamp: datetime
    user: Optional[str]
    action: str
    table: str
    record_id: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]

# Tipos para configuração de segurança
class SecurityConfig(TypedDict, total=False):
    """Configuração de segurança."""
    encrypt_connections: bool
    ssl_cert: Optional[str]
    ssl_key: Optional[str]
    ssl_ca: Optional[str]
    allowed_hosts: Optional[List[str]]
    max_connections_per_ip: Optional[int]

# Tipos para performance
class PerformanceMetrics(TypedDict):
    """Métricas de performance."""
    query_count: int
    total_time: float
    average_time: float
    min_time: float
    max_time: float
    slow_queries: List[QueryLog]

# Tipos para configuração de logging
class LoggingConfig(TypedDict, total=False):
    """Configuração de logging."""
    level: LogLevel
    format: str
    file: Optional[str]
    max_size: Optional[int]
    backup_count: Optional[int]
    enable_console: bool
    enable_file: bool
    enable_rotation: bool
