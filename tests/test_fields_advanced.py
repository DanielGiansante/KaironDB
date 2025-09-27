"""
Testes para campos avançados com validações customizadas
"""

import pytest
import datetime
from kairondb import (
    EmailField, URLField, PhoneField, CPFField, CNPJField, RegexField,
    RangeIntegerField, RangeFloatField, ChoiceField, PasswordField,
    DateField, TimeField, JSONField, UUIDField, IPAddressField,
    CustomField, ArrayField, DecimalField, Model
)
from kairondb.exceptions import ValidationError


class TestEmailField:
    """Testes para EmailField"""
    
    def test_valid_email(self):
        """Testa email válido"""
        field = EmailField()
        field.name = "email"
        field.validate("user@example.com")
        field.validate("test.email+tag@domain.co.uk")
    
    def test_invalid_email(self):
        """Testa email inválido"""
        field = EmailField()
        field.name = "email"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("invalid-email")
        assert "Formato de email inválido" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            field.validate("user@")
        
        with pytest.raises(ValidationError):
            field.validate("@domain.com")


class TestURLField:
    """Testes para URLField"""
    
    def test_valid_url(self):
        """Testa URL válida"""
        field = URLField()
        field.name = "url"
        field.validate("https://www.example.com")
        field.validate("http://example.com/path")
        field.validate("ftp://files.example.com")
    
    def test_invalid_url(self):
        """Testa URL inválida"""
        field = URLField()
        field.name = "url"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("not-a-url")
        assert "Formato de URL inválido" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            field.validate("www.example.com")
        
        with pytest.raises(ValidationError):
            field.validate("")


class TestPhoneField:
    """Testes para PhoneField"""
    
    def test_valid_phone(self):
        """Testa telefone válido"""
        field = PhoneField()
        field.name = "phone"
        field.validate("(11) 99999-9999")
        field.validate("11999999999")
        field.validate("+55 11 99999-9999")
    
    def test_invalid_phone(self):
        """Testa telefone inválido"""
        field = PhoneField()
        field.name = "phone"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("123")
        assert "Formato de telefone inválido" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            field.validate("abc-def-ghij")


class TestCPFField:
    """Testes para CPFField"""
    
    def test_valid_cpf(self):
        """Testa CPF válido"""
        field = CPFField()
        field.name = "cpf"
        field.validate("123.456.789-09")
        field.validate("12345678909")
    
    def test_invalid_cpf(self):
        """Testa CPF inválido"""
        field = CPFField()
        field.name = "cpf"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("123.456.789-00")
        assert "CPF inválido" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            field.validate("111.111.111-11")
        
        with pytest.raises(ValidationError):
            field.validate("123")


class TestCNPJField:
    """Testes para CNPJField"""
    
    def test_valid_cnpj(self):
        """Testa CNPJ válido"""
        field = CNPJField()
        field.name = "cnpj"
        field.validate("11.222.333/0001-81")
        field.validate("11222333000181")
    
    def test_invalid_cnpj(self):
        """Testa CNPJ inválido"""
        field = CNPJField()
        field.name = "cnpj"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("11.222.333/0001-00")
        assert "CNPJ inválido" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            field.validate("11.111.111/1111-11")


class TestRegexField:
    """Testes para RegexField"""
    
    def test_valid_regex(self):
        """Testa regex válida"""
        field = RegexField(r'^[A-Z]{2}\d{4}$')
        field.name = "code"
        field.validate("AB1234")
        field.validate("XY9999")
    
    def test_invalid_regex(self):
        """Testa regex inválida"""
        field = RegexField(r'^[A-Z]{2}\d{4}$')
        field.name = "code"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("abc123")
        assert "não corresponde ao padrão esperado" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            field.validate("AB12")


class TestRangeIntegerField:
    """Testes para RangeIntegerField"""
    
    def test_valid_range(self):
        """Testa range válido"""
        field = RangeIntegerField(min_value=1, max_value=100)
        field.name = "age"
        field.validate(25)
        field.validate(1)
        field.validate(100)
    
    def test_invalid_range(self):
        """Testa range inválido"""
        field = RangeIntegerField(min_value=1, max_value=100)
        field.name = "age"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate(0)
        assert "deve estar entre 1 e 100" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate(101)
        assert "deve estar entre 1 e 100" in str(exc_info.value)


class TestRangeFloatField:
    """Testes para RangeFloatField"""
    
    def test_valid_range(self):
        """Testa range válido"""
        field = RangeFloatField(min_value=0.0, max_value=10.0)
        field.name = "score"
        field.validate(5.5)
        field.validate(0.0)
        field.validate(10.0)
    
    def test_invalid_range(self):
        """Testa range inválido"""
        field = RangeFloatField(min_value=0.0, max_value=10.0)
        field.name = "score"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate(-1.0)
        assert "deve estar entre 0.0 e 10.0" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate(11.0)
        assert "deve estar entre 0.0 e 10.0" in str(exc_info.value)


class TestChoiceField:
    """Testes para ChoiceField"""
    
    def test_valid_choice(self):
        """Testa escolha válida"""
        field = ChoiceField(["red", "green", "blue"])
        field.name = "color"
        field.validate("red")
        field.validate("green")
        field.validate("blue")
    
    def test_invalid_choice(self):
        """Testa escolha inválida"""
        field = ChoiceField(["red", "green", "blue"])
        field.name = "color"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("yellow")
        assert "deve ser um dos seguintes" in str(exc_info.value)


class TestPasswordField:
    """Testes para PasswordField"""
    
    def test_valid_password(self):
        """Testa senha válida"""
        field = PasswordField()
        field.name = "password"
        field.validate("Password123!")
        field.validate("MyStr0ng#Pass")
    
    def test_invalid_password(self):
        """Testa senha inválida"""
        field = PasswordField()
        field.name = "password"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("weak123!")  # Sem maiúscula
        assert "deve conter pelo menos uma letra maiúscula" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            field.validate("Password123")  # Sem caractere especial


class TestDateField:
    """Testes para DateField"""
    
    def test_valid_date(self):
        """Testa data válida"""
        field = DateField()
        field.name = "birth_date"
        field.validate(datetime.date(1990, 1, 1))
        field.validate(datetime.date.today())
    
    def test_invalid_date(self):
        """Testa data inválida"""
        field = DateField()
        field.name = "birth_date"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("2023-01-01")
        assert "espera uma data (date)" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate(datetime.datetime.now())
        assert "espera uma data (date)" in str(exc_info.value)


class TestTimeField:
    """Testes para TimeField"""
    
    def test_valid_time(self):
        """Testa horário válido"""
        field = TimeField()
        field.name = "start_time"
        field.validate(datetime.time(9, 30, 0))
        field.validate(datetime.time(14, 45, 30))
    
    def test_invalid_time(self):
        """Testa horário inválido"""
        field = TimeField()
        field.name = "start_time"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("09:30")
        assert "espera um horário (time)" in str(exc_info.value)


class TestJSONField:
    """Testes para JSONField"""
    
    def test_valid_json(self):
        """Testa JSON válido"""
        field = JSONField()
        field.name = "data"
        field.validate({"key": "value"})
        field.validate([1, 2, 3])
        field.validate('{"key": "value"}')
    
    def test_invalid_json(self):
        """Testa JSON inválido"""
        field = JSONField()
        field.name = "data"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("invalid json")
        assert "contém JSON inválido" in str(exc_info.value)


class TestUUIDField:
    """Testes para UUIDField"""
    
    def test_valid_uuid(self):
        """Testa UUID válido"""
        field = UUIDField()
        field.name = "id"
        field.validate("550e8400-e29b-41d4-a716-446655440000")
        field.validate("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    
    def test_invalid_uuid(self):
        """Testa UUID inválido"""
        field = UUIDField()
        field.name = "id"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("not-a-uuid")
        assert "deve ser um UUID válido" in str(exc_info.value)


class TestIPAddressField:
    """Testes para IPAddressField"""
    
    def test_valid_ipv4(self):
        """Testa IPv4 válido"""
        field = IPAddressField(version=4)
        field.name = "ip"
        field.validate("192.168.1.1")
        field.validate("127.0.0.1")
    
    def test_invalid_ipv4(self):
        """Testa IPv4 inválido"""
        field = IPAddressField(version=4)
        field.name = "ip"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate("256.256.256.256")
        assert "deve ser um endereço IPv4 válido" in str(exc_info.value)


class TestArrayField:
    """Testes para ArrayField"""
    
    def test_valid_array(self):
        """Testa array válido"""
        field = ArrayField(item_type=str, min_length=1, max_length=3)
        field.name = "tags"
        field.validate(["tag1", "tag2"])
        field.validate(["single"])
    
    def test_invalid_array(self):
        """Testa array inválido"""
        field = ArrayField(item_type=str, min_length=1, max_length=3)
        field.name = "tags"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate([])
        assert "deve ter pelo menos 1 itens" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            field.validate(["tag1", "tag2", "tag3", "tag4"])
        
        with pytest.raises(ValidationError):
            field.validate([1, 2, 3])  # Tipo errado


class TestCustomField:
    """Testes para CustomField"""
    
    def test_valid_custom(self):
        """Testa validação customizada válida"""
        def is_even(value):
            return value % 2 == 0
        
        field = CustomField(validator=is_even)
        field.name = "number"
        field.validate(2)
        field.validate(4)
    
    def test_invalid_custom(self):
        """Testa validação customizada inválida"""
        def is_even(value):
            return value % 2 == 0
        
        field = CustomField(validator=is_even)
        field.name = "number"
        
        with pytest.raises(ValidationError) as exc_info:
            field.validate(3)
        assert "Validação customizada falhou" in str(exc_info.value)


class TestModelWithAdvancedFields:
    """Testes para modelo com campos avançados"""
    
    def test_model_creation_with_advanced_fields(self):
        """Testa criação de modelo com campos avançados"""
        class User(Model):
            _table_name = "users"
            email = EmailField(required=True)
            phone = PhoneField(required=False)
            age = RangeIntegerField(min_value=18, max_value=120)
            color = ChoiceField(["red", "green", "blue"])
        
        user = User(
            email="user@example.com",
            phone="(11) 99999-9999",
            age=25,
            color="red"
        )
        
        assert user.email == "user@example.com"
        assert user.phone == "(11) 99999-9999"
        assert user.age == 25
        assert user.color == "red"
    
    def test_model_validation_with_advanced_fields(self):
        """Testa validação de modelo com campos avançados"""
        class User(Model):
            _table_name = "users"
            email = EmailField(required=True)
            age = RangeIntegerField(min_value=18, max_value=120)
        
        # Email inválido
        with pytest.raises(ValidationError) as exc_info:
            User(email="invalid-email", age=25)
        assert "Formato de email inválido" in str(exc_info.value)
        
        # Idade inválida
        with pytest.raises(ValidationError) as exc_info:
            User(email="user@example.com", age=15)
        assert "deve estar entre 18 e 120" in str(exc_info.value)
