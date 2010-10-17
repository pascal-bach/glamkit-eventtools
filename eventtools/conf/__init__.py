from django.conf import settings as django_settings
from .. import settings as app_settings

class SettingsHandler(object):
    def __getattr__(self, attr):
        try:
            return getattr(app_settings, attr)
        except AttributeError:
            return getattr(django_settings, attr)
        
settings = SettingsHandler()