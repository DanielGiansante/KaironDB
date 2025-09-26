"""
Utilitários para KaironDB
"""

import os
import sys
import platform
from typing import Optional, Dict, Any, List, Union
from pathlib import Path


def get_platform_library_name() -> str:
    """Retorna o nome da biblioteca baseado na plataforma."""
    if platform.system() == "Windows":
        return "sqlbridge.dll"
    else:
        return "sqlbridge.so"


def find_library_path(custom_path: Optional[str] = None) -> str:
    """Encontra o caminho da biblioteca Go."""
    if custom_path:
        if os.path.exists(custom_path):
            return custom_path
        else:
            raise FileNotFoundError(f"Biblioteca não encontrada em: {custom_path}")
    
    # Tentar encontrar na pasta do pacote
    package_dir = Path(__file__).parent
    lib_name = get_platform_library_name()
    lib_path = package_dir / lib_name
    
    if lib_path.exists():
        return str(lib_path)
    
    # Tentar encontrar na pasta GO
    go_dir = package_dir.parent.parent / "GO"
    lib_path = go_dir / lib_name
    
    if lib_path.exists():
        return str(lib_path)
    
    raise FileNotFoundError(
        f"Biblioteca {lib_name} não encontrada. "
        f"Procurou em: {package_dir} e {go_dir}"
    )


def format_connection_string(
    driver: str,
    server: str,
    database: str,
    username: str,
    password: str,
    **kwargs
) -> str:
    """Formata string de conexão baseada no driver."""
    if driver.lower() == "sqlite3":
        return f"file:{server}"
    
    elif driver.lower() == "postgres":
        port = kwargs.get("port", 5432)
        sslmode = kwargs.get("sslmode", "prefer")
        return f"postgresql://{username}:{password}@{server}:{port}/{database}?sslmode={sslmode}"
    
    elif driver.lower() == "mysql":
        port = kwargs.get("port", 3306)
        charset = kwargs.get("charset", "utf8mb4")
        return f"mysql://{username}:{password}@{server}:{port}/{database}?charset={charset}"
    
    elif driver.lower() == "sqlserver":
        port = kwargs.get("port", 1433)
        instance = kwargs.get("instance", "")
        if instance:
            server = f"{server}\\{instance}"
        return f"sqlserver://{username}:{password}@{server}:{port}/{database}"
    
    else:
        raise ValueError(f"Driver não suportado: {driver}")


def parse_connection_string(connection_string: str) -> Dict[str, Any]:
    """Parse de string de conexão para parâmetros."""
    # Implementação básica - pode ser expandida
    if connection_string.startswith("file:"):
        return {
            "driver": "sqlite3",
            "server": connection_string[5:],
            "database": "",
            "username": "",
            "password": ""
        }
    
    # Para outros drivers, implementação mais complexa seria necessária
    raise NotImplementedError("Parse de connection string não implementado para este driver")


def validate_driver(driver: str) -> bool:
    """Valida se o driver é suportado."""
    supported_drivers = ["postgres", "sqlserver", "mysql", "sqlite3"]
    return driver.lower() in supported_drivers


def get_driver_requirements(driver: str) -> List[str]:
    """Retorna os parâmetros obrigatórios para um driver."""
    if driver.lower() == "sqlite3":
        return ["server"]  # server = caminho do arquivo
    else:
        return ["server", "database", "username", "password"]


def sanitize_table_name(name: str) -> str:
    """Sanitiza nome de tabela para evitar SQL injection."""
    # Remove caracteres perigosos
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    # Garante que não comece com número
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    
    return sanitized or "table"


def sanitize_column_name(name: str) -> str:
    """Sanitiza nome de coluna para evitar SQL injection."""
    return sanitize_table_name(name)


def format_sql_identifier(identifier: str) -> str:
    """Formata identificador SQL com aspas se necessário."""
    if not identifier:
        return '""'
    
    # Se contém caracteres especiais ou é palavra reservada, usar aspas
    import re
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        return identifier
    else:
        return f'"{identifier}"'


def get_python_version() -> str:
    """Retorna versão do Python."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_platform_info() -> Dict[str, str]:
    """Retorna informações da plataforma."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": get_python_version(),
        "architecture": platform.architecture()[0]
    }


def format_bytes(bytes_value: int) -> str:
    """Formata bytes em formato legível."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Trunca string se exceder o comprimento máximo."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Faz merge profundo de dois dicionários."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Achata um dicionário aninhado."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_int(value: Any, default: int = 0) -> int:
    """Converte valor para int de forma segura."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Converte valor para float de forma segura."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Converte valor para string de forma segura."""
    try:
        return str(value)
    except Exception:
        return default


def is_valid_identifier(name: str) -> bool:
    """Verifica se é um identificador Python válido."""
    import keyword
    return (
        name.isidentifier() and 
        not keyword.iskeyword(name) and
        not name.startswith('_')
    )


def get_class_name(obj: Any) -> str:
    """Retorna nome da classe de um objeto."""
    return obj.__class__.__name__


def get_module_name(obj: Any) -> str:
    """Retorna nome do módulo de um objeto."""
    return obj.__class__.__module__
