from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from generic_ecom.settings import NV_CURRENT_CLIENT
import importlib
module = importlib.import_module(NV_CURRENT_CLIENT + '.model_user')
ExtendedUser = getattr(module, "ExtendedUser")


class BaseNotDeletedManager(models.Manager):
    def get_queryset(self):
        return super(BaseNotDeletedManager, self).get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):

    """BaseModel has audit log handling"""
    is_deleted = models.BooleanField(default=False)
    
    # created = models.DateTimeField(editable=False)
    # modified = models.DateTimeField(editable=False)
    # created_by = models.ForeignKey(
    #     ExtendedUser, related_query_name="%(app_label)s_%(class)ss", related_name="%(app_label)s_%(class)s_created_by_user", editable=False, null=True)
    # modified_by = models.ForeignKey(
    #     ExtendedUser, related_query_name="%(app_label)s_%(class)ss", related_name="%(app_label)s_%(class)s_modified_by_user", editable=False, null=True)

    objects = BaseNotDeletedManager()
    allobjects = models.Manager()

    def delete(self, using='default', *args, **kwarg):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True

@python_2_unicode_compatible
class BaseInventoryType(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True