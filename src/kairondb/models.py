"""
Sistema de modelos declarativos assíncronos para KaironDB
"""

import datetime
from typing import Any, Dict, Optional, Union, Callable
from .exceptions import ValidationError
from .fields import Field, StringField, IntegerField, DateTimeField, BooleanField, FloatField


class ModelMeta(type):
    """Metaclasse que descobre os campos declarados num modelo e os armazena."""
    
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return super().__new__(cls, name, bases, attrs)
        
        fields = {}
        
        # Coletar campos das classes base primeiro
        for base in bases:
            if hasattr(base, '_meta') and 'fields' in base._meta:
                for field_name, field in base._meta['fields'].items():
                    # Criar uma cópia do campo para evitar compartilhamento
                    new_field = type(field)(
                        required=field.required,
                        default=field.default,
                        primary_key=field.primary_key
                    )
                    # Copiar atributos específicos do campo
                    for attr_name in ['max_length', 'min_length', 'min_value', 'max_value', 'auto_now_add', 'auto_now']:
                        if hasattr(field, attr_name):
                            setattr(new_field, attr_name, getattr(field, attr_name))
                    new_field.name = field_name
                    fields[field_name] = new_field
        
        # Coletar campos da classe atual
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
                self._data[name] = field.get_default()
        
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # Validar campos obrigatórios após inicialização
        for name, field in self._meta['fields'].items():
            if field.required and name not in self._data:
                field.validate(None)  # Isso vai levantar ValidationError

    def __setattr__(self, key, value):
        # Verificar se _meta já foi definido (após __init__)
        if hasattr(self, '_meta') and key in self._meta['fields']:
            self._meta['fields'][key].validate(value)
            self._data[key] = value
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key):
        if key in self._data:
            return self._data[key]
        raise AttributeError(f"'{type(self).__name__}' não tem o atributo '{key}'")
    
    def __getattribute__(self, key):
        # Se for um campo do modelo, retornar o valor do _data
        if key != '_data' and hasattr(type(self), '_meta') and key in type(self)._meta.get('fields', {}):
            if key in self._data:
                return self._data[key]
            else:
                # Campo não foi definido, retornar None ou default
                field = type(self)._meta['fields'][key]
                if field.default is not None:
                    return field.get_default()
                return None
        return super().__getattribute__(key)

    @classmethod
    def set_bridge(cls, bridge):
        """Define a bridge para o modelo."""
        cls._bridge = bridge

    async def save(self):
        """Salva o modelo no banco de dados."""
        if self._bridge is None:
            raise Exception("Bridge não definida.")
        
        pk_field_name = next(
            (name for name, field in self._meta['fields'].items() if field.primary_key), 
            None
        )
        
        if pk_field_name and self._data.get(pk_field_name) is not None:
            # UPDATE
            data_to_update = {k: v for k, v in self._data.items() if k != pk_field_name}
            return await self._bridge.update(
                self._meta['table_name'], 
                data=data_to_update, 
                where={pk_field_name: self._data[pk_field_name]}
            )
        else:
            # INSERT
            return await self._bridge.insert(self._meta['table_name'], data=self._data)

    @classmethod
    async def create(cls, **kwargs):
        """Cria e salva uma nova instância do modelo."""
        instance = cls(**kwargs)
        await instance.save()
        return instance

    @classmethod
    async def select(cls, fields=None, where=None, joins=None):
        """Seleciona registros do modelo."""
        if cls._bridge is None:
            raise Exception("Bridge não definida.")
        return await cls._bridge.select(cls._meta['table_name'], fields, where, joins)

    @classmethod
    async def update(cls, data, where):
        """Atualiza registros do modelo."""
        if cls._bridge is None:
            raise Exception("Bridge não definida.")
        return await cls._bridge.update(cls._meta['table_name'], data, where)

    @classmethod
    async def delete(cls, where):
        """Deleta registros do modelo."""
        if cls._bridge is None:
            raise Exception("Bridge não definida.")
        return await cls._bridge.delete(cls._meta['table_name'], where)

    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para dicionário."""
        return self._data.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Cria instância do modelo a partir de dicionário."""
        return cls(**data)

    def __repr__(self) -> str:
        """Representação string do modelo."""
        class_name = self.__class__.__name__
        fields_str = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"{class_name}({fields_str})"

    def __str__(self) -> str:
        """String representation do modelo."""
        return self.__repr__()