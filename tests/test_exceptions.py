"""
Testes para o sistema de exceções
"""

import pytest
from kairondb.exceptions import (
    KaironDBError, ValidationError, ConnectionError, QueryError,
    TimeoutError, ConfigurationError, PoolError
)


class TestKaironDBError:
    """Testes para a exceção base KaironDBError"""
    
    def test_basic_error(self):
        """Testa criação básica de erro"""
        error = KaironDBError("Teste de erro")
        assert str(error) == "Teste de erro"
        assert error.message == "Teste de erro"
        assert error.error_code is None
        assert error.details == {}
    
    def test_error_with_code(self):
        """Testa erro com código de erro"""
        error = KaironDBError("Teste de erro", error_code="TEST_ERROR")
        assert str(error) == "[TEST_ERROR] Teste de erro"
        assert error.error_code == "TEST_ERROR"
    
    def test_error_with_details(self):
        """Testa erro com detalhes"""
        details = {"field": "name", "value": "test"}
        error = KaironDBError("Teste de erro", details=details)
        assert error.details == details


class TestValidationError:
    """Testes para ValidationError"""
    
    def test_basic_validation_error(self):
        """Testa erro de validação básico"""
        error = ValidationError("Campo inválido")
        assert str(error) == "[VALIDATION_ERROR] Campo inválido"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.field_name is None
        assert error.field_value is None
    
    def test_validation_error_with_field(self):
        """Testa erro de validação com campo"""
        error = ValidationError("Campo obrigatório", field_name="name", field_value="")
        assert error.field_name == "name"
        assert error.field_value == ""


class TestConnectionError:
    """Testes para ConnectionError"""
    
    def test_connection_error(self):
        """Testa erro de conexão"""
        error = ConnectionError("Falha na conexão", driver="postgres", server="localhost")
        assert error.driver == "postgres"
        assert error.server == "localhost"


class TestQueryError:
    """Testes para QueryError"""
    
    def test_query_error(self):
        """Testa erro de query"""
        error = QueryError("Query inválida", sql="SELECT * FROM", params=["test"])
        assert error.sql == "SELECT * FROM"
        assert error.params == ["test"]


class TestTimeoutError:
    """Testes para TimeoutError"""
    
    def test_timeout_error(self):
        """Testa erro de timeout"""
        error = TimeoutError("Query timeout", timeout_seconds=30.0)
        assert error.timeout_seconds == 30.0


class TestConfigurationError:
    """Testes para ConfigurationError"""
    
    def test_configuration_error(self):
        """Testa erro de configuração"""
        error = ConfigurationError("Config inválida", config_key="database_url")
        assert error.config_key == "database_url"


class TestPoolError:
    """Testes para PoolError"""
    
    def test_pool_error(self):
        """Testa erro de pool"""
        error = PoolError("Pool falhou", pool_id="pool_123")
        assert error.pool_id == "pool_123"


class TestExceptionHierarchy:
    """Testes para hierarquia de exceções"""
    
    def test_inheritance(self):
        """Testa se todas as exceções herdam de KaironDBError"""
        assert issubclass(ValidationError, KaironDBError)
        assert issubclass(ConnectionError, KaironDBError)
        assert issubclass(QueryError, KaironDBError)
        assert issubclass(TimeoutError, KaironDBError)
        assert issubclass(ConfigurationError, KaironDBError)
        assert issubclass(PoolError, KaironDBError)
    
    def test_exception_raising(self):
        """Testa se exceções podem ser levantadas"""
        with pytest.raises(ValidationError):
            raise ValidationError("Teste")
        
        with pytest.raises(ConnectionError):
            raise ConnectionError("Teste")
        
        with pytest.raises(QueryError):
            raise QueryError("Teste")
        
        with pytest.raises(TimeoutError):
            raise TimeoutError("Teste")
        
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Teste")
        
        with pytest.raises(PoolError):
            raise PoolError("Teste")
