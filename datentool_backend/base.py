import json
from django.db import router
from django.db.models.deletion import Collector


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


class DatentoolModelMixin:

    @property
    def bulk_upload(self):
        return None

    def delete(self, using=None, keep_parents=False, use_protection=False):
        """
        delete the object
        Parameters:
        using: str, optional
        keep_parents: bool, optional(default=False)
        use_protection: bool, optional(default=False)
            if True, raise a ProtectedError
            when trying to delete related objects if on_delete=PROTECT_CASCADE
            if False, delete objects cascaded
        """
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self.pk is not None, (
            "%s object can't be deleted because its %s attribute is set to None." %
            (self._meta.object_name, self._meta.pk.attname)
        )

        collector = Collector(using=using)
        collector.use_protection = use_protection
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()
