from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from diff import generate_diff
import django

def create_children(modeladmin, request, queryset):
    for event in queryset:
        e = type(event).objects.create(parent=event)
create_children.short_description = "Create children of selected events"


def EventAdmin(EventModel): #pass in the name of your EventModel subclass to use this admin.
    class _EventAdmin(MPTTModelAdmin):
        actions = [create_children]
        exclude = ['parent']
        change_form_template = 'admin/eventtools/event.html'
    
        def change_view(self, request, object_id, extra_context=None):
            obj = EventModel.objects.get(pk=object_id)

            if obj.parent:
                fields_diff = generate_diff(obj.parent, obj, include=EventModel._event_meta.fields_to_inherit)
            else:
                fields_diff = None

            extra_context = {'fields_diff': fields_diff,
                             'django_version': django.get_version()[:3],
                             'object': obj,
                             }
                         
            return super(_EventAdmin, self).change_view(request, object_id, extra_context)
    return _EventAdmin

try:
    from feincms.admin.tree_editor import TreeEditor
except ImportError:
    pass
else:
    def FeinCMSEventAdmin(EventModel):
        class _FeinCMSEventAdmin(EventAdmin(EventModel), TreeEditor):
            pass
        return _FeinCMSEventAdmin
        
    
