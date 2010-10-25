import inspect
from django.db.models.fields import NOT_PROVIDED
from django.utils.encoding import force_unicode
from django.db import connection

class ModelInstanceAwareDefault():
    """
    This callable class provides model instance awareness in order to generate a default.
    It uses 9th level voodoo, so may break if django changes much. Probably much better to patch django to send the model instance and field into the callable.
    Could be expanded to be general.
    """
    def __init__(self, attr, old_default=None):
        self.attr = attr
        self.old_default = old_default

    def has_old_default(self):
        "Returns a boolean of whether this field has a default value."
        return self.old_default is not NOT_PROVIDED

    def get_old_default(self, field):
        "Returns the default value for this field."
        if self.has_old_default():
            if callable(self.old_default):
                return self.old_default()
            return force_unicode(self.old_default, strings_only=True)
        if hasattr(field, 'empty_strings_allowed'):
            if not field.empty_strings_allowed or (field.null and not connection.features.interprets_empty_strings_as_nulls):
                return None
        return ""


    def __call__(self):
        # it would be so awesome if django passed the field/instance in question to the default callable.
        # since it doesn't, let's grab it with voodoo.
        frame = inspect.currentframe().f_back
        field = frame.f_locals.get('self', None)

        parent = None
        if field:
            frame = frame.f_back
        else:
            frame = None
        while frame is not None:
            if frame.f_locals.has_key('kwargs'):
                modelbasekwargs = frame.f_locals['kwargs']
                if modelbasekwargs.has_key('parent'):
                    parent = modelbasekwargs['parent']
                    break
            frame = frame.f_back

        if parent is not None:
            return getattr(parent, field.attname, self.get_old_default(field))
        return self.get_old_default(field)
