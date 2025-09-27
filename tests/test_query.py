"""
Testes para sistema de queries (Q objects)
"""

import pytest
from kairondb import Q


class TestQObjects:
    """Testes para objetos Q"""
    
    def test_simple_q_creation(self):
        """Testa criação de Q simples"""
        q = Q(name="João")
        
        assert q.connector == Q.AND
        assert len(q.children) == 1
        assert q.children[0] == {"name": "João"}
    
    def test_q_with_multiple_conditions(self):
        """Testa Q com múltiplas condições"""
        q = Q(name="João", age=25)
        
        assert q.connector == Q.AND
        assert len(q.children) == 1
        assert q.children[0] == {"name": "João", "age": 25}
    
    def test_q_and_operation(self):
        """Testa operação AND entre Q objects"""
        q1 = Q(name="João")
        q2 = Q(age=25)
        combined = q1 & q2
        
        assert combined.connector == Q.AND
        assert len(combined.children) == 2
        assert q1 in combined.children
        assert q2 in combined.children
    
    def test_q_or_operation(self):
        """Testa operação OR entre Q objects"""
        q1 = Q(name="João")
        q2 = Q(name="Maria")
        combined = q1 | q2
        
        assert combined.connector == Q.OR
        assert len(combined.children) == 2
        assert q1 in combined.children
        assert q2 in combined.children
    
    def test_q_complex_operations(self):
        """Testa operações complexas com Q objects"""
        q1 = Q(name="João")
        q2 = Q(age=25)
        q3 = Q(age=30)
        q4 = Q(email="joao@test.com")
        
        # (name="João" AND age=25) OR (age=30 AND email="joao@test.com")
        complex_q = (q1 & q2) | (q3 & q4)
        
        assert complex_q.connector == Q.OR
        assert len(complex_q.children) == 2
        
        # Primeiro child deve ser AND
        first_child = complex_q.children[0]
        assert first_child.connector == Q.AND
        assert q1 in first_child.children
        assert q2 in first_child.children
        
        # Segundo child deve ser AND
        second_child = complex_q.children[1]
        assert second_child.connector == Q.AND
        assert q3 in second_child.children
        assert q4 in second_child.children
    
    def test_q_to_dict_simple(self):
        """Testa conversão de Q simples para dict"""
        q = Q(name="João")
        result = q.to_dict()
        
        expected = {
            'connector': 'AND',
            'children': [{'name': 'João'}]
        }
        assert result == expected
    
    def test_q_to_dict_with_and(self):
        """Testa conversão de Q com AND para dict"""
        q1 = Q(name="João")
        q2 = Q(age=25)
        combined = q1 & q2
        result = combined.to_dict()
        
        expected = {
            'connector': 'AND',
            'children': [
                {'connector': 'AND', 'children': [{'name': 'João'}]},
                {'connector': 'AND', 'children': [{'age': 25}]}
            ]
        }
        assert result == expected
    
    def test_q_to_dict_with_or(self):
        """Testa conversão de Q com OR para dict"""
        q1 = Q(name="João")
        q2 = Q(name="Maria")
        combined = q1 | q2
        result = combined.to_dict()
        
        expected = {
            'connector': 'OR',
            'children': [
                {'connector': 'AND', 'children': [{'name': 'João'}]},
                {'connector': 'AND', 'children': [{'name': 'Maria'}]}
            ]
        }
        assert result == expected
    
    def test_q_to_dict_complex(self):
        """Testa conversão de Q complexo para dict"""
        q1 = Q(name="João")
        q2 = Q(age=25)
        q3 = Q(age=30)
        complex_q = q1 & (q2 | q3)
        result = complex_q.to_dict()
        
        expected = {
            'connector': 'AND',
            'children': [
                {'connector': 'AND', 'children': [{'name': 'João'}]},
                {
                    'connector': 'OR',
                    'children': [
                        {'connector': 'AND', 'children': [{'age': 25}]},
                        {'connector': 'AND', 'children': [{'age': 30}]}
                    ]
                }
            ]
        }
        assert result == expected
    
    def test_q_invalid_and_operation(self):
        """Testa operação AND com tipo inválido"""
        q = Q(name="João")
        
        with pytest.raises(TypeError) as exc_info:
            q & "invalid"
        
        assert "A operação AND só pode ser feita entre objetos Q" in str(exc_info.value)
    
    def test_q_invalid_or_operation(self):
        """Testa operação OR com tipo inválido"""
        q = Q(name="João")
        
        with pytest.raises(TypeError) as exc_info:
            q | "invalid"
        
        assert "A operação OR só pode ser feita entre objetos Q" in str(exc_info.value)
    
    def test_q_empty_creation(self):
        """Testa criação de Q vazio"""
        q = Q()
        
        assert q.connector == Q.AND
        assert len(q.children) == 0
    
    def test_q_constants(self):
        """Testa constantes do Q"""
        assert Q.AND == 'AND'
        assert Q.OR == 'OR'
    
    def test_q_nested_operations(self):
        """Testa operações aninhadas complexas"""
        # ((name="João" OR name="Maria") AND age=25) OR (email="admin@test.com")
        q1 = Q(name="João")
        q2 = Q(name="Maria")
        q3 = Q(age=25)
        q4 = Q(email="admin@test.com")
        
        nested_q = ((q1 | q2) & q3) | q4
        result = nested_q.to_dict()
        
        # Verificar estrutura
        assert result['connector'] == 'OR'
        assert len(result['children']) == 2
        
        # Primeiro child deve ser AND
        first_child = result['children'][0]
        assert first_child['connector'] == 'AND'
        assert len(first_child['children']) == 2
        
        # Segundo child deve ser simples
        second_child = result['children'][1]
        assert second_child['connector'] == 'AND'
        assert second_child['children'] == [{'email': 'admin@test.com'}]
