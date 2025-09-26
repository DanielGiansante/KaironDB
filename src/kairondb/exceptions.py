class KaironDBError(Exception):
    """Exceção base para todos os erros do KaironDB."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

class ValidationError(KaironDBError):
    """Exceção levantada para erros de validação nos campos do modelo."""
    
    def __init__(self, message: str, field_name: str = None, field_value=None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field_name = field_name
        self.field_value = field_value

class ConnectionError(KaironDBError):
    """Exceção levantada para erros de conexão com o banco de dados."""
    
    def __init__(self, message: str, driver: str = None, server: str = None, **kwargs):
        super().__init__(message, error_code="CONNECTION_ERROR", **kwargs)
        self.driver = driver
        self.server = server

class QueryError(KaironDBError):
    """Exceção levantada para erros de execução de queries."""
    
    def __init__(self, message: str, sql: str = None, params: list = None, **kwargs):
        super().__init__(message, error_code="QUERY_ERROR", **kwargs)
        self.sql = sql
        self.params = params

class TimeoutError(KaironDBError):
    """Exceção levantada para erros de timeout em queries."""
    
    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        self.timeout_seconds = timeout_seconds

class ConfigurationError(KaironDBError):
    """Exceção levantada para erros de configuração."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key

class PoolError(KaironDBError):
    """Exceção levantada para erros de pool de conexões."""
    
    def __init__(self, message: str, pool_id: str = None, **kwargs):
        super().__init__(message, error_code="POOL_ERROR", **kwargs)
        self.pool_id = pool_id