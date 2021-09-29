class NamedModel:
    """model with the name as representation"""

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.name}'

