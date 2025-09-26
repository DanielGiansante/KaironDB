"""
Sistema de campos para modelos KaironDB
"""

import datetime
from typing import Any, Optional, Callable, Union
from .exceptions import ValidationError


class Field:
    """Classe base para todos os campos de modelo."""
    
    def __init__(
        self,
        required: bool = False,
        default: Optional[Union[Any, Callable]] = None,
        primary_key: bool = False,
        **kwargs
    ):
        self.required = required
        self.default = default
        self.primary_key = primary_key
        self.name: Optional[str] = None
        self._extra_kwargs = kwargs
    
    def validate(self, value: Any) -> None:
        """Valida o valor do campo."""
        if value is None and self.required:
            raise ValidationError(
                f"O campo '{self.name}' é obrigatório.",
                field_name=self.name,
                field_value=value
            )
    
    def get_default(self) -> Any:
        """Retorna o valor padrão do campo."""
        if self.default is None:
            return None
        return self.default() if callable(self.default) else self.default


class StringField(Field):
    """Campo para strings com validação de comprimento."""
    
    def __init__(
        self,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
    
    def validate(self, value: Any) -> None:
        """Valida string com comprimento."""
        super().validate(value)
        
        if value is None:
            return
        
        if not isinstance(value, str):
            raise ValidationError(
                f"O campo '{self.name}' espera uma string, mas recebeu {type(value).__name__}.",
                field_name=self.name,
                field_value=value
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                f"O campo '{self.name}' excede o comprimento máximo de {self.max_length} caracteres.",
                field_name=self.name,
                field_value=value
            )
        
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                f"O campo '{self.name}' deve ter pelo menos {self.min_length} caracteres.",
                field_name=self.name,
                field_value=value
            )


class IntegerField(Field):
    """Campo para inteiros com validação de range."""
    
    def __init__(
        self,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> None:
        """Valida inteiro com range."""
        super().validate(value)
        
        if value is None:
            return
        
        if not isinstance(value, int):
            raise ValidationError(
                f"O campo '{self.name}' espera um inteiro, mas recebeu {type(value).__name__}.",
                field_name=self.name,
                field_value=value
            )
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"O campo '{self.name}' deve ser maior ou igual a {self.min_value}.",
                field_name=self.name,
                field_value=value
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"O campo '{self.name}' deve ser menor ou igual a {self.max_value}.",
                field_name=self.name,
                field_value=value
            )


class DateTimeField(Field):
    """Campo para datetime com validação de tipo."""
    
    def __init__(
        self,
        auto_now_add: bool = False,
        auto_now: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.auto_now_add = auto_now_add
        self.auto_now = auto_now
        
        if auto_now_add or auto_now:
            self.default = datetime.datetime.now
    
    def validate(self, value: Any) -> None:
        """Valida datetime."""
        super().validate(value)
        
        if value is None:
            return
        
        if not isinstance(value, datetime.datetime):
            raise ValidationError(
                f"O campo '{self.name}' espera um objeto datetime, mas recebeu {type(value).__name__}.",
                field_name=self.name,
                field_value=value
            )


class BooleanField(Field):
    """Campo para valores booleanos."""
    
    def validate(self, value: Any) -> None:
        """Valida boolean."""
        super().validate(value)
        
        if value is None:
            return
        
        if not isinstance(value, bool):
            raise ValidationError(
                f"O campo '{self.name}' espera um valor booleano, mas recebeu {type(value).__name__}.",
                field_name=self.name,
                field_value=value
            )


class FloatField(Field):
    """Campo para valores float com validação de range."""
    
    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> None:
        """Valida float com range."""
        super().validate(value)
        
        if value is None:
            return
        
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"O campo '{self.name}' espera um número, mas recebeu {type(value).__name__}.",
                field_name=self.name,
                field_value=value
            )
        
        value = float(value)
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"O campo '{self.name}' deve ser maior ou igual a {self.min_value}.",
                field_name=self.name,
                field_value=value
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"O campo '{self.name}' deve ser menor ou igual a {self.max_value}.",
                field_name=self.name,
                field_value=value
            )
