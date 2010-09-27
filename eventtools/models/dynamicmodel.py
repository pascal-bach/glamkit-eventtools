from django.db import models
import sys

def create_model_for_module(model_name, __module__name, model_attrs={}, model_bases=(models.Model,)):
    meta = type('Meta', (object,), {
        # 'app_label': klass._meta.app_label,
        'managed': True,
    })
    
    if model_attrs.has_key('Meta'):
        meta.update(model_attrs['Meta'])
        del model_attrs['Meta']
    
    model_dict = {
        'Meta': meta,
        '__module__': __module__name, 
    }
    model_dict.update(model_attrs)
  
    return type(model_name, model_bases, model_dict)