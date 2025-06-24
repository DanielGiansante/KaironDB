class Q:
    """
    Encapsula condições de query complexas para permitir operações lógicas (AND/OR).
    """
    AND = 'AND'
    OR = 'OR'

    def __init__(self, **kwargs):
        self.connector = self.AND
        self.children = [kwargs] if kwargs else []

    def __or__(self, other):
        if not isinstance(other, Q):
            raise TypeError("A operação OR só pode ser feita entre objetos Q.")
        combined = Q()
        combined.connector = self.OR
        combined.children.extend([self, other])
        return combined

    def __and__(self, other):
        if not isinstance(other, Q):
            raise TypeError("A operação AND só pode ser feita entre objetos Q.")
        combined = Q()
        combined.connector = self.AND
        combined.children.extend([self, other])
        return combined

    def to_dict(self):
        """Converte a árvore de objetos Q numa estrutura de dicionário recursiva."""
        return {
            'connector': self.connector,
            'children': [c.to_dict() if isinstance(c, Q) else c for c in self.children]
        }