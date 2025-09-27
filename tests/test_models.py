"""
Testes para sistema de modelos
"""

import pytest
from kairondb import Model, StringField, IntegerField, DateTimeField
from kairondb.exceptions import ValidationError
import datetime


class User(Model):
    """Modelo de teste para usuário"""
    _table_name = "test_users"
    id = IntegerField(primary_key=True)
    name = StringField(required=True, max_length=100)
    email = StringField(required=False, max_length=255)
    age = IntegerField(required=False)
    created_at = DateTimeField(auto_now_add=True)


class TestModelFields:
    """Testes para campos de modelo"""
    
    def test_string_field_validation(self):
        """Testa validação de StringField"""
        # Campo válido
        field = StringField(required=True, max_length=50)
        field.name = "name"
        field.validate("João")
        
        # Campo obrigatório vazio
        with pytest.raises(ValidationError) as exc_info:
            field.validate(None)
        assert "obrigatório" in str(exc_info.value)
        
        # String muito longa
        with pytest.raises(ValidationError) as exc_info:
            field.validate("A" * 100)
        assert "excede o comprimento máximo" in str(exc_info.value)
        
        # Tipo inválido
        with pytest.raises(ValidationError) as exc_info:
            field.validate(123)
        assert "espera uma string" in str(exc_info.value)
    
    def test_integer_field_validation(self):
        """Testa validação de IntegerField"""
        field = IntegerField(required=True)
        field.name = "age"
        
        # Campo válido
        field.validate(25)
        
        # Campo obrigatório vazio
        with pytest.raises(ValidationError) as exc_info:
            field.validate(None)
        assert "obrigatório" in str(exc_info.value)
        
        # Tipo inválido
        with pytest.raises(ValidationError) as exc_info:
            field.validate("25")
        assert "espera um inteiro" in str(exc_info.value)
    
    def test_datetime_field_validation(self):
        """Testa validação de DateTimeField"""
        field = DateTimeField(required=True)
        field.name = "created_at"
        
        # Campo válido
        now = datetime.datetime.now()
        field.validate(now)
        
        # Campo obrigatório vazio
        with pytest.raises(ValidationError) as exc_info:
            field.validate(None)
        assert "obrigatório" in str(exc_info.value)
        
        # Tipo inválido
        with pytest.raises(ValidationError) as exc_info:
            field.validate("2023-01-01")
        assert "espera um objeto datetime" in str(exc_info.value)
    
    def test_datetime_field_auto_now_add(self):
        """Testa DateTimeField com auto_now_add"""
        field = DateTimeField(auto_now_add=True)
        field.name = "created_at"
        
        # Deve ter default como função
        assert callable(field.default)
        
        # Deve retornar datetime atual
        default_value = field.default()
        assert isinstance(default_value, datetime.datetime)


class TestModelCreation:
    """Testes para criação de modelos"""
    
    def test_model_creation_with_valid_data(self):
        """Testa criação de modelo com dados válidos"""
        user = User(name="João Silva", email="joao@test.com", age=30)
        
        assert user.name == "João Silva"
        assert user.email == "joao@test.com"
        assert user.age == 30
        assert user.id is None  # Primary key não definida
    
    def test_model_creation_with_required_field_missing(self):
        """Testa criação de modelo sem campo obrigatório"""
        with pytest.raises(ValidationError) as exc_info:
            User(email="joao@test.com", age=30)
        
        assert "name" in str(exc_info.value)
        assert "obrigatório" in str(exc_info.value)
    
    def test_model_creation_with_invalid_field_type(self):
        """Testa criação de modelo com tipo de campo inválido"""
        with pytest.raises(ValidationError) as exc_info:
            User(name=123)  # name deve ser string
        
        assert "espera uma string" in str(exc_info.value)
    
    def test_model_creation_with_string_too_long(self):
        """Testa criação de modelo com string muito longa"""
        with pytest.raises(ValidationError) as exc_info:
            User(name="A" * 200)  # max_length=100
        
        assert "excede o comprimento máximo" in str(exc_info.value)
    
    def test_model_creation_with_default_values(self):
        """Testa criação de modelo com valores padrão"""
        user = User(name="João Silva")
        
        assert user.name == "João Silva"
        assert user.email is None  # Campo opcional
        assert user.age is None    # Campo opcional
        assert isinstance(user.created_at, datetime.datetime)  # auto_now_add


class TestModelAttributes:
    """Testes para atributos de modelo"""
    
    def test_setattr_validation(self):
        """Testa validação no __setattr__"""
        user = User(name="João Silva")
        
        # Atributo válido
        user.age = 25
        assert user.age == 25
        
        # Atributo inválido
        with pytest.raises(ValidationError):
            user.age = "vinte e cinco"  # age deve ser int
        
        # Atributo não definido no modelo
        user.custom_field = "test"  # Deve funcionar
        assert user.custom_field == "test"
    
    def test_getattr(self):
        """Testa __getattr__"""
        user = User(name="João Silva", age=25)
        
        # Atributo existente
        assert user.name == "João Silva"
        assert user.age == 25
        
        # Atributo não existente
        with pytest.raises(AttributeError):
            _ = user.non_existent_field


class TestModelMeta:
    """Testes para metaclasse ModelMeta"""
    
    def test_meta_fields_discovery(self):
        """Testa descoberta de campos pela metaclasse"""
        meta = User._meta
        
        assert 'name' in meta['fields']
        assert 'email' in meta['fields']
        assert 'age' in meta['fields']
        assert 'id' in meta['fields']
        assert 'created_at' in meta['fields']
        
        # Verificar se os campos têm o nome correto
        assert meta['fields']['name'].name == 'name'
        assert meta['fields']['email'].name == 'email'
    
    def test_meta_table_name(self):
        """Testa nome da tabela"""
        meta = User._meta
        assert meta['table_name'] == 'test_users'
    
    def test_meta_table_name_default(self):
        """Testa nome padrão da tabela"""
        class SimpleModel(Model):
            name = StringField()
        
        meta = SimpleModel._meta
        assert meta['table_name'] == 'simplemodels'  # Nome da classe + 's'


class TestModelInheritance:
    """Testes para herança de modelos"""
    
    def test_model_inheritance(self):
        """Testa herança de modelos"""
        class BaseModel(Model):
            id = IntegerField(primary_key=True)
            created_at = DateTimeField(auto_now_add=True)
        
        class UserModel(BaseModel):
            _table_name = "users"
            name = StringField(required=True)
        
        # Verificar se herda campos da classe base
        meta = UserModel._meta
        assert 'id' in meta['fields']
        assert 'created_at' in meta['fields']
        assert 'name' in meta['fields']
        
        # Verificar se pode criar instância
        user = UserModel(name="João")
        assert user.name == "João"
        assert isinstance(user.created_at, datetime.datetime)
