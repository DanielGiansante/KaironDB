import datetime
from .exceptions import ValidationError

class Field:
    """Classe base para todos os tipos de campo do modelo."""
    def __init__(self, required=False, default=None, primary_key=False):
        self.required = required
        self.default = default
        self.primary_key = primary_key
        self.name = None

    def validate(self, value):
        if self.required and value is None:
            raise ValidationError(f"O campo '{self.name}' é obrigatório.")

class StringField(Field):
    def __init__(self, max_length=None, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length

    def validate(self, value):
        super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                raise ValidationError(f"O campo '{self.name}' espera uma string.")
            if self.max_length is not None and len(value) > self.max_length:
                raise ValidationError(f"O campo '{self.name}' excede o comprimento máximo de {self.max_length} caracteres.")

class IntegerField(Field):
    def validate(self, value):
        super().validate(value)
        if value is not None and not isinstance(value, int):
            raise ValidationError(f"O campo '{self.name}' espera um inteiro.")

class DateTimeField(Field):
    def __init__(self, auto_now_add=False, **kwargs):
        super().__init__(**kwargs)
        if auto_now_add:
            self.default = datetime.datetime.now
            
    def validate(self, value):
        super().validate(value)
        if value is not None and not isinstance(value, datetime.datetime):
            raise ValidationError(f"O campo '{self.name}' espera um objeto datetime.")

class ModelMeta(type):
    """Metaclasse que descobre os campos declarados num modelo e os armazena."""
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return super().__new__(cls, name, bases, attrs)
        
        fields = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
        
        attrs['_meta'] = {
            'fields': fields,
            'table_name': attrs.get('_table_name', name.lower() + 's')
        }
        return super().__new__(cls, name, bases, attrs)

class Model(metaclass=ModelMeta):
    """Classe base para todos os modelos declarativos assíncronos."""
    _bridge = None

    def __init__(self, **kwargs):
        self._data = {}
        for name, field in self._meta['fields'].items():
            if field.default is not None:
                self._data[name] = field.default() if callable(field.default) else field.default
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, key, value):
        if key in self._meta['fields']:
            self._meta['fields'][key].validate(value)
            self._data[key] = value
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key):
        if key in self._data:
            return self._data[key]
        raise AttributeError(f"'{type(self).__name__}' não tem o atributo '{key}'")

    @classmethod
    def set_bridge(cls, bridge):
        cls._bridge = bridge

    async def save(self):
        if self._bridge is None: raise Exception("Bridge não definida.")
        pk_field_name = next((name for name, field in self._meta['fields'].items() if field.primary_key), None)
        
        if pk_field_name and self._data.get(pk_field_name) is not None:
            # UPDATE
            data_to_update = {k: v for k, v in self._data.items() if k != pk_field_name}
            return await self._bridge.update(self._meta['table_name'], data=data_to_update, where={pk_field_name: self._data[pk_field_name]})
        else:
            # INSERT
            # Nota: a lógica para inserir e retornar o ID da chave primária precisaria ser implementada
            return await self._bridge.insert(self._meta['table_name'], data=self._data)

    @classmethod
    async def create(cls, **kwargs):
        instance = cls(**kwargs)
        await instance.save()
        return instance

    @classmethod
    async def select(cls, fields=None, where=None, joins=None):
        if cls._bridge is None: raise Exception("Bridge não definida.")
        return await cls._bridge.select(cls._meta['table_name'], fields, where, joins)

    @classmethod
    async def update(cls, data, where):
        if cls._bridge is None: raise Exception("Bridge não definida.")
        return await cls._bridge.update(cls._meta['table_name'], data, where)

    @classmethod
    async def delete(cls, where):
        if cls._bridge is None: raise Exception("Bridge não definida.")
        return await cls._bridge.delete(cls._meta['table_name'], where)

