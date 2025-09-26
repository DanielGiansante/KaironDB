from .bridge import SQLBridge, Transaction, TransactionalBridge
from .pool import AdvancedConnectionPool, ConnectionState, ConnectionInfo
from .cache import QueryCache, CacheManager, CachePolicy, CacheEntry
from .migrations import MigrationManager, MigrationStatus, MigrationRecord
from .profiling import Profiler, PerformanceMetrics, QueryMetrics, profile_operation
from .optimizations import PerformanceOptimizer, OptimizationConfig, OptimizedSerializer, LazyLoader
from .dashboard import MetricsDashboard, DashboardConfig, DashboardData, Alert
from .models import Model
from .fields import Field, StringField, IntegerField, DateTimeField, BooleanField, FloatField
from .fields_advanced import (
    EmailField, URLField, PhoneField, CPFField, CNPJField, RegexField,
    RangeIntegerField, RangeFloatField, ChoiceField, PasswordField,
    DateField, TimeField, JSONField, UUIDField, IPAddressField,
    CustomField, ArrayField, DecimalField
)
from .query import Q
from .exceptions import (
    KaironDBError, ValidationError, ConnectionError, QueryError, 
    TimeoutError, ConfigurationError, PoolError
)
from .validators import (
    EmailValidator, URLValidator, PhoneValidator, CPFValidator, CNPJValidator,
    RegexValidator, RangeValidator, ChoiceValidator,
    validate_email, validate_url, validate_phone, validate_cpf, validate_cnpj
)
from .utils import (
    get_platform_library_name, find_library_path, format_connection_string,
    validate_driver, get_driver_requirements, sanitize_table_name,
    sanitize_column_name, format_sql_identifier, get_python_version,
    get_platform_info, format_bytes, truncate_string, deep_merge_dicts,
    flatten_dict, safe_int, safe_float, safe_str, is_valid_identifier,
    get_class_name, get_module_name
)

__all__ = [
    # Core classes
    'SQLBridge',
    'Transaction',
    'TransactionalBridge',
    'Model',
    
    # Advanced features
    'AdvancedConnectionPool',
    'ConnectionState',
    'ConnectionInfo',
    'QueryCache',
    'CacheManager',
    'CachePolicy',
    'CacheEntry',
    'MigrationManager',
    'MigrationStatus',
    'MigrationRecord',
    
    # Performance and monitoring
    'Profiler',
    'PerformanceMetrics',
    'QueryMetrics',
    'profile_operation',
    'PerformanceOptimizer',
    'OptimizationConfig',
    'OptimizedSerializer',
    'LazyLoader',
    'MetricsDashboard',
    'DashboardConfig',
    'DashboardData',
    'Alert',
    
    # Field types
    'Field',
    'StringField',
    'IntegerField',
    'DateTimeField',
    'BooleanField',
    'FloatField',
    
    # Advanced field types
    'EmailField',
    'URLField',
    'PhoneField',
    'CPFField',
    'CNPJField',
    'RegexField',
    'RangeIntegerField',
    'RangeFloatField',
    'ChoiceField',
    'PasswordField',
    'DateField',
    'TimeField',
    'JSONField',
    'UUIDField',
    'IPAddressField',
    'CustomField',
    'ArrayField',
    'DecimalField',
    
    # Query system
    'Q',
    
    # Exceptions
    'KaironDBError',
    'ValidationError',
    'ConnectionError',
    'QueryError',
    'TimeoutError',
    'ConfigurationError',
    'PoolError',
    
    # Validators
    'EmailValidator',
    'URLValidator',
    'PhoneValidator',
    'CPFValidator',
    'CNPJValidator',
    'RegexValidator',
    'RangeValidator',
    'ChoiceValidator',
    'validate_email',
    'validate_url',
    'validate_phone',
    'validate_cpf',
    'validate_cnpj',
    
    # Utilities
    'get_platform_library_name',
    'find_library_path',
    'format_connection_string',
    'validate_driver',
    'get_driver_requirements',
    'sanitize_table_name',
    'sanitize_column_name',
    'format_sql_identifier',
    'get_python_version',
    'get_platform_info',
    'format_bytes',
    'truncate_string',
    'deep_merge_dicts',
    'flatten_dict',
    'safe_int',
    'safe_float',
    'safe_str',
    'is_valid_identifier',
    'get_class_name',
    'get_module_name',
]