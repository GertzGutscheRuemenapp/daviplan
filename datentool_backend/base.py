import json


class NamedModel:
    """model with the name as representation"""

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.name}'



class JsonAttributes:
    """model with a json-attributes field"""

    def get_attributes(self,
                      field_name: str = 'attributes') -> dict:
        """returns the json-field with the given field_name as dictionary"""
        field = getattr(self, field_name)
        json_dict = (json.loads(field)
                     if isinstance(field, str)
                     else field)
        return json_dict
