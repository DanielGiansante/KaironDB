"""
Validadores customizados para campos KaironDB
"""

import re
import urllib.parse
from typing import Any, Callable, Optional
from .exceptions import ValidationError


class BaseValidator:
    """Classe base para validadores customizados."""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or self.default_message
    
    @property
    def default_message(self) -> str:
        """Mensagem padrão de erro."""
        return f"Validação falhou para o campo"
    
    def __call__(self, value: Any, field_name: str) -> None:
        """Executa a validação."""
        if not self.validate(value):
            raise ValidationError(
                self.message or f"Validação falhou para o campo '{field_name}'",
                field_name=field_name,
                field_value=value
            )
    
    def validate(self, value: Any) -> bool:
        """Implementar validação específica."""
        raise NotImplementedError


class EmailValidator(BaseValidator):
    """Validador para endereços de email."""
    
    def __init__(self, message: Optional[str] = None):
        super().__init__(message)
        self.pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    @property
    def default_message(self) -> str:
        return "Formato de email inválido"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        return isinstance(value, str) and bool(self.pattern.match(value))


class URLValidator(BaseValidator):
    """Validador para URLs."""
    
    def __init__(self, message: Optional[str] = None):
        super().__init__(message)
    
    @property
    def default_message(self) -> str:
        return "Formato de URL inválido"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        if not isinstance(value, str):
            return False
        
        try:
            result = urllib.parse.urlparse(value)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


class PhoneValidator(BaseValidator):
    """Validador para números de telefone."""
    
    def __init__(self, message: Optional[str] = None):
        super().__init__(message)
        # Padrão para telefone brasileiro
        self.pattern = re.compile(
            r'^(\+55\s?)?(\(?[1-9]{2}\)?)\s?[9]?[0-9]{4}-?[0-9]{4}$'
        )
    
    @property
    def default_message(self) -> str:
        return "Formato de telefone inválido"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        if not isinstance(value, str):
            return False
        
        # Remove espaços e caracteres especiais para validação
        clean_value = re.sub(r'[\s\-\(\)]', '', value)
        return bool(self.pattern.match(clean_value))


class CPFValidator(BaseValidator):
    """Validador para CPF brasileiro."""
    
    def __init__(self, message: Optional[str] = None):
        super().__init__(message)
    
    @property
    def default_message(self) -> str:
        return "CPF inválido"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        if not isinstance(value, str):
            return False
        
        # Remove caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', value)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Validação do primeiro dígito verificador
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = (sum1 * 10) % 11
        if digit1 == 10:
            digit1 = 0
        if digit1 != int(cpf[9]):
            return False
        
        # Validação do segundo dígito verificador
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = (sum2 * 10) % 11
        if digit2 == 10:
            digit2 = 0
        if digit2 != int(cpf[10]):
            return False
        
        return True


class CNPJValidator(BaseValidator):
    """Validador para CNPJ brasileiro."""
    
    def __init__(self, message: Optional[str] = None):
        super().__init__(message)
    
    @property
    def default_message(self) -> str:
        return "CNPJ inválido"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        if not isinstance(value, str):
            return False
        
        # Remove caracteres não numéricos
        cnpj = re.sub(r'[^0-9]', '', value)
        
        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Validação do primeiro dígito verificador
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
        digit1 = sum1 % 11
        digit1 = 0 if digit1 < 2 else 11 - digit1
        if digit1 != int(cnpj[12]):
            return False
        
        # Validação do segundo dígito verificador
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
        digit2 = sum2 % 11
        digit2 = 0 if digit2 < 2 else 11 - digit2
        if digit2 != int(cnpj[13]):
            return False
        
        return True


class RegexValidator(BaseValidator):
    """Validador genérico baseado em regex."""
    
    def __init__(self, pattern: str, message: Optional[str] = None):
        super().__init__(message)
        self.pattern = re.compile(pattern)
    
    @property
    def default_message(self) -> str:
        return "Valor não corresponde ao padrão esperado"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        if not isinstance(value, str):
            return False
        
        return bool(self.pattern.match(value))


class RangeValidator(BaseValidator):
    """Validador para valores numéricos em um range."""
    
    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        message: Optional[str] = None
    ):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(message)
    
    @property
    def default_message(self) -> str:
        if self.min_value is not None and self.max_value is not None:
            return f"Valor deve estar entre {self.min_value} e {self.max_value}"
        elif self.min_value is not None:
            return f"Valor deve ser maior ou igual a {self.min_value}"
        elif self.max_value is not None:
            return f"Valor deve ser menor ou igual a {self.max_value}"
        return "Valor fora do range permitido"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False
        
        if self.min_value is not None and num_value < self.min_value:
            return False
        
        if self.max_value is not None and num_value > self.max_value:
            return False
        
        return True


class ChoiceValidator(BaseValidator):
    """Validador para valores de uma lista de opções."""
    
    def __init__(self, choices: list, message: Optional[str] = None):
        self.choices = choices
        super().__init__(message)
    
    @property
    def default_message(self) -> str:
        return f"Valor deve ser um dos seguintes: {', '.join(map(str, self.choices))}"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        return value in self.choices


def validate_email(value: Any, field_name: str) -> None:
    """Função de conveniência para validar email."""
    EmailValidator()(value, field_name)


def validate_url(value: Any, field_name: str) -> None:
    """Função de conveniência para validar URL."""
    URLValidator()(value, field_name)


def validate_phone(value: Any, field_name: str) -> None:
    """Função de conveniência para validar telefone."""
    PhoneValidator()(value, field_name)


def validate_cpf(value: Any, field_name: str) -> None:
    """Função de conveniência para validar CPF."""
    CPFValidator()(value, field_name)


def validate_cnpj(value: Any, field_name: str) -> None:
    """Função de conveniência para validar CNPJ."""
    CNPJValidator()(value, field_name)
