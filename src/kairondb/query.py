"""
Sistema de queries (Q objects) para KaironDB
"""

from typing import Dict, Any, List, Union, Optional, TypeVar, Generic
from .typing import QueryCondition, QueryResults


class Q:
    """
    Encapsula condições de query complexas para permitir operações lógicas (AND/OR).
    """
    AND: str = 'AND'
    OR: str = 'OR'

    def __init__(self, **kwargs: Any) -> None:
        self.connector: str = self.AND
        self.children: List[Union[Dict[str, Any], 'Q']] = [kwargs] if kwargs else []

    def __or__(self, other: 'Q') -> 'Q':
        if not isinstance(other, Q):
            raise TypeError("A operação OR só pode ser feita entre objetos Q.")
        combined = Q()
        combined.connector = self.OR
        combined.children.extend([self, other])
        return combined

    def __and__(self, other: 'Q') -> 'Q':
        if not isinstance(other, Q):
            raise TypeError("A operação AND só pode ser feita entre objetos Q.")
        combined = Q()
        combined.connector = self.AND
        combined.children.extend([self, other])
        return combined

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o objeto Q para um dicionário que pode ser serializado.
        """
        if not self.children:
            return {'connector': self.connector, 'children': []}
        
        if len(self.children) == 1 and isinstance(self.children[0], dict):
            return {'connector': self.connector, 'children': self.children}
        
        return {
            'connector': self.connector,
            'children': [child.to_dict() if isinstance(child, Q) else child for child in self.children]
        }

    def __repr__(self) -> str:
        """Representação string do objeto Q."""
        if not self.children:
            return f"Q()"
        
        if len(self.children) == 1 and isinstance(self.children[0], dict):
            return f"Q({self.children[0]})"
        
        connector_str = " | " if self.connector == self.OR else " & "
        children_str = connector_str.join(
            str(child) if isinstance(child, dict) else repr(child) 
            for child in self.children
        )
        return f"Q({children_str})"

    def __str__(self) -> str:
        """String representation do objeto Q."""
        return self.__repr__()

    def is_empty(self) -> bool:
        """Verifica se o objeto Q está vazio."""
        return len(self.children) == 0

    def add_condition(self, **kwargs: Any) -> 'Q':
        """Adiciona uma nova condição ao objeto Q."""
        if kwargs:
            self.children.append(kwargs)
        return self

    def add_q(self, q: 'Q') -> 'Q':
        """Adiciona outro objeto Q como filho."""
        self.children.append(q)
        return self

    def clone(self) -> 'Q':
        """Cria uma cópia do objeto Q."""
        new_q = Q()
        new_q.connector = self.connector
        new_q.children = self.children.copy()
        return new_q

    def invert(self) -> 'Q':
        """Inverte a lógica do objeto Q (AND vira OR e vice-versa)."""
        new_q = Q()
        new_q.connector = self.OR if self.connector == self.AND else self.AND
        new_q.children = self.children.copy()
        return new_q

    def __bool__(self) -> bool:
        """Permite usar o objeto Q em contextos booleanos."""
        return not self.is_empty()

    def __len__(self) -> int:
        """Retorna o número de condições no objeto Q."""
        return len(self.children)

    def __iter__(self):
        """Permite iterar sobre as condições do objeto Q."""
        return iter(self.children)

    def __contains__(self, key: str) -> bool:
        """Verifica se uma chave está presente em alguma condição."""
        for child in self.children:
            if isinstance(child, dict) and key in child:
                return True
            elif isinstance(child, Q) and key in child:
                return True
        return False

    def get_conditions_for_key(self, key: str) -> List[Any]:
        """Retorna todos os valores para uma chave específica."""
        values = []
        for child in self.children:
            if isinstance(child, dict) and key in child:
                values.append(child[key])
            elif isinstance(child, Q):
                values.extend(child.get_conditions_for_key(key))
        return values

    def has_key(self, key: str) -> bool:
        """Verifica se uma chave específica está presente."""
        return key in self

    def remove_key(self, key: str) -> 'Q':
        """Remove todas as condições com uma chave específica."""
        new_children = []
        for child in self.children:
            if isinstance(child, dict):
                if key not in child:
                    new_children.append(child)
            elif isinstance(child, Q):
                new_q = child.remove_key(key)
                if not new_q.is_empty():
                    new_children.append(new_q)
        
        new_q = Q()
        new_q.connector = self.connector
        new_q.children = new_children
        return new_q

    def merge(self, other: 'Q') -> 'Q':
        """Mescla outro objeto Q com este."""
        if other.is_empty():
            return self.clone()
        
        if self.is_empty():
            return other.clone()
        
        new_q = Q()
        new_q.connector = self.connector
        new_q.children = self.children.copy()
        new_q.children.extend(other.children)
        return new_q

    def flatten(self) -> 'Q':
        """Achata o objeto Q removendo níveis desnecessários."""
        if len(self.children) <= 1:
            return self.clone()
        
        new_q = Q()
        new_q.connector = self.connector
        
        for child in self.children:
            if isinstance(child, Q):
                if child.connector == self.connector:
                    # Mesmo conector, achatar
                    new_q.children.extend(child.children)
                else:
                    # Conector diferente, manter como está
                    new_q.children.append(child)
            else:
                new_q.children.append(child)
        
        return new_q

    def optimize(self) -> 'Q':
        """Otimiza o objeto Q removendo redundâncias."""
        # Implementação básica - pode ser expandida
        return self.flatten()

    def to_sql_where(self) -> str:
        """Converte o objeto Q para uma cláusula WHERE SQL."""
        if self.is_empty():
            return "1=1"
        
        conditions = []
        for child in self.children:
            if isinstance(child, dict):
                # Condição simples
                for key, value in child.items():
                    if isinstance(value, str):
                        conditions.append(f"{key} = '{value}'")
                    else:
                        conditions.append(f"{key} = {value}")
            elif isinstance(child, Q):
                # Sub-query
                sub_where = child.to_sql_where()
                if sub_where != "1=1":
                    conditions.append(f"({sub_where})")
        
        if not conditions:
            return "1=1"
        
        connector = f" {self.connector} "
        return connector.join(conditions)

    def __eq__(self, other: Any) -> bool:
        """Compara dois objetos Q para igualdade."""
        if not isinstance(other, Q):
            return False
        
        return (
            self.connector == other.connector and
            self.children == other.children
        )

    def __ne__(self, other: Any) -> bool:
        """Compara dois objetos Q para desigualdade."""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Permite usar objetos Q como chaves de dicionário."""
        return hash((self.connector, tuple(self.children)))

    def __getitem__(self, key: str) -> Any:
        """Permite acessar valores como se fosse um dicionário."""
        for child in self.children:
            if isinstance(child, dict) and key in child:
                return child[key]
            elif isinstance(child, Q):
                try:
                    return child[key]
                except KeyError:
                    continue
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Permite definir valores como se fosse um dicionário."""
        if not self.children:
            self.children = [{}]
        
        if isinstance(self.children[0], dict):
            self.children[0][key] = value
        else:
            self.children.insert(0, {key: value})

    def keys(self) -> List[str]:
        """Retorna todas as chaves presentes no objeto Q."""
        keys = set()
        for child in self.children:
            if isinstance(child, dict):
                keys.update(child.keys())
            elif isinstance(child, Q):
                keys.update(child.keys())
        return list(keys)

    def values(self) -> List[Any]:
        """Retorna todos os valores presentes no objeto Q."""
        values = []
        for child in self.children:
            if isinstance(child, dict):
                values.extend(child.values())
            elif isinstance(child, Q):
                values.extend(child.values())
        return values

    def items(self) -> List[tuple]:
        """Retorna todos os pares chave-valor presentes no objeto Q."""
        items = []
        for child in self.children:
            if isinstance(child, dict):
                items.extend(child.items())
            elif isinstance(child, Q):
                items.extend(child.items())
        return items