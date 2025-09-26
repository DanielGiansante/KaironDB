"""
Campos avançados com validações customizadas para KaironDB
"""

import datetime
import re
from typing import Any, Optional, Callable, List, Union, Dict
from .fields import Field, StringField, IntegerField, DateTimeField, BooleanField, FloatField
from .validators import (
    EmailValidator, URLValidator, PhoneValidator, CPFValidator, CNPJValidator,
    RegexValidator, RangeValidator, ChoiceValidator
)
from .exceptions import ValidationError


class EmailField(StringField):
    """Campo para endereços de email com validação automática."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators = [EmailValidator()]
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class URLField(StringField):
    """Campo para URLs com validação automática."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators = [URLValidator()]
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class PhoneField(StringField):
    """Campo para números de telefone com validação automática."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators = [PhoneValidator()]
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class CPFField(StringField):
    """Campo para CPF brasileiro com validação automática."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators = [CPFValidator()]
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class CNPJField(StringField):
    """Campo para CNPJ brasileiro com validação automática."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators = [CNPJValidator()]
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class RegexField(StringField):
    """Campo para strings com validação por regex."""
    
    def __init__(self, pattern: str, message: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.validators = [RegexValidator(pattern, message)]
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class RangeIntegerField(IntegerField):
    """Campo para inteiros com validação de range."""
    
    def __init__(
        self, 
        min_value: Optional[int] = None, 
        max_value: Optional[int] = None, 
        **kwargs
    ):
        super().__init__(**kwargs)
        self.validators = [RangeValidator(min_value, max_value)]
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class RangeFloatField(FloatField):
    """Campo para floats com validação de range."""
    
    def __init__(
        self, 
        min_value: Optional[float] = None, 
        max_value: Optional[float] = None, 
        **kwargs
    ):
        super().__init__(**kwargs)
        self.validators = [RangeValidator(min_value, max_value)]
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class ChoiceField(StringField):
    """Campo para valores de uma lista de opções."""
    
    def __init__(self, choices: List[str], **kwargs):
        super().__init__(**kwargs)
        self.validators = [ChoiceValidator(choices)]
        self.choices = choices
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            for validator in self.validators:
                validator(value, self.name)


class PasswordField(StringField):
    """Campo para senhas com validação de força."""
    
    def __init__(
        self, 
        min_length: int = 8, 
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        **kwargs
    ):
        super().__init__(min_length=min_length, **kwargs)
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            self._validate_password_strength(value)
    
    def _validate_password_strength(self, password: str) -> None:
        """Valida a força da senha."""
        errors = []
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("deve conter pelo menos uma letra maiúscula")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("deve conter pelo menos uma letra minúscula")
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append("deve conter pelo menos um dígito")
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("deve conter pelo menos um caractere especial")
        
        if errors:
            raise ValidationError(
                f"Senha {', '.join(errors)}",
                field_name=self.name,
                field_value="***"  # Não expor senha
            )


class DateField(Field):
    """Campo para datas (sem hora)."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None and not (isinstance(value, datetime.date) and type(value) == datetime.date):
            raise ValidationError(
                f"O campo '{self.name}' espera uma data (date), mas recebeu {type(value).__name__}.",
                field_name=self.name,
                field_value=value
            )


class TimeField(Field):
    """Campo para horários."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None and not isinstance(value, datetime.time):
            raise ValidationError(
                f"O campo '{self.name}' espera um horário (time), mas recebeu {type(value).__name__}.",
                field_name=self.name,
                field_value=value
            )


class JSONField(Field):
    """Campo para dados JSON."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            try:
                import json
                if isinstance(value, str):
                    json.loads(value)
                elif not isinstance(value, (dict, list)):
                    raise ValidationError(
                        f"O campo '{self.name}' espera dados JSON válidos.",
                        field_name=self.name,
                        field_value=value
                    )
            except (json.JSONDecodeError, TypeError):
                raise ValidationError(
                    f"O campo '{self.name}' contém JSON inválido.",
                    field_name=self.name,
                    field_value=value
                )


class UUIDField(StringField):
    """Campo para UUIDs com validação automática."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            if not self.uuid_pattern.match(str(value)):
                raise ValidationError(
                    f"O campo '{self.name}' deve ser um UUID válido.",
                    field_name=self.name,
                    field_value=value
                )


class IPAddressField(StringField):
    """Campo para endereços IP com validação automática."""
    
    def __init__(self, version: int = 4, **kwargs):
        super().__init__(**kwargs)
        self.version = version
        if version == 4:
            self.pattern = re.compile(
                r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            )
        elif version == 6:
            self.pattern = re.compile(
                r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
            )
        else:
            raise ValueError("Versão de IP deve ser 4 ou 6")
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            if not self.pattern.match(str(value)):
                raise ValidationError(
                    f"O campo '{self.name}' deve ser um endereço IPv{self.version} válido.",
                    field_name=self.name,
                    field_value=value
                )


class CustomField(Field):
    """Campo com validação customizada."""
    
    def __init__(
        self, 
        validator: Optional[Callable[[Any], bool]] = None,
        validator_message: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.validator = validator
        self.validator_message = validator_message or "Validação customizada falhou"
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None and self.validator is not None:
            if not self.validator(value):
                raise ValidationError(
                    self.validator_message,
                    field_name=self.name,
                    field_value=value
                )


class ArrayField(Field):
    """Campo para arrays/listas."""
    
    def __init__(
        self, 
        item_type: type = str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.item_type = item_type
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            if not isinstance(value, list):
                raise ValidationError(
                    f"O campo '{self.name}' espera uma lista, mas recebeu {type(value).__name__}.",
                    field_name=self.name,
                    field_value=value
                )
            
            if self.min_length is not None and len(value) < self.min_length:
                raise ValidationError(
                    f"O campo '{self.name}' deve ter pelo menos {self.min_length} itens.",
                    field_name=self.name,
                    field_value=value
                )
            
            if self.max_length is not None and len(value) > self.max_length:
                raise ValidationError(
                    f"O campo '{self.name}' deve ter no máximo {self.max_length} itens.",
                    field_name=self.name,
                    field_value=value
                )
            
            # Validar tipo dos itens
            for i, item in enumerate(value):
                if not isinstance(item, self.item_type):
                    raise ValidationError(
                        f"O campo '{self.name}' item {i} deve ser do tipo {self.item_type.__name__}.",
                        field_name=self.name,
                        field_value=value
                    )


class DecimalField(Field):
    """Campo para valores decimais com precisão."""
    
    def __init__(
        self, 
        max_digits: Optional[int] = None,
        decimal_places: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            try:
                from decimal import Decimal
                decimal_value = Decimal(str(value))
            except (ValueError, TypeError):
                raise ValidationError(
                    f"O campo '{self.name}' deve ser um valor decimal válido.",
                    field_name=self.name,
                    field_value=value
                )
            
            if self.max_digits is not None:
                digits = len(str(decimal_value).replace('.', '').replace('-', ''))
                if digits > self.max_digits:
                    raise ValidationError(
                        f"O campo '{self.name}' deve ter no máximo {self.max_digits} dígitos.",
                        field_name=self.name,
                        field_value=value
                    )
            
            if self.decimal_places is not None:
                if decimal_value.as_tuple().exponent < -self.decimal_places:
                    raise ValidationError(
                        f"O campo '{self.name}' deve ter no máximo {self.decimal_places} casas decimais.",
                        field_name=self.name,
                        field_value=value
                    )
