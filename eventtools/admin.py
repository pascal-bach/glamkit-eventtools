from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from diff import generate_diff
import django
from eventtools import adminviews

def create_children(modeladmin, request, queryset):
    for event in queryset:
        e = type(event)._event_manager.create(parent=event)
create_children.short_description = "Create children of selected events"


def EventAdmin(EventModel): #pass in the name of your EventModel subclass to use this admin.
    class _EventAdmin(MPTTModelAdmin):
        actions = [create_children]
        exclude = ['parent']
        change_form_template = 'admin/eventtools/event.html'
        save_on_top = True
        
        # list_display = ('title', 'edit_occurrences_link', 'all_occurrences_count', 'my_occurrences_count')

        # def get_urls(self):
        #     super_urls = super(EventAdminBase, self).get_urls()
        #     my_urls = patterns('',
        #         url(r'^(?P<id>\d+)/occurrences/$', self.admin_site.admin_view(adminviews.occurrences), {'modeladmin': self}),
        #         # url(r'^(?P<event_id>\d+)/create_exception/(?P<gen_id>\d+)/(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})/(?P<hour>\d{1,2})-(?P<minute>\d{1,2})-(?P<second>\d{1,2})/$', self.admin_site.admin_view(make_exceptional_occurrence), {'modeladmin': self}),
        #     )
        #     return my_urls + super_urls
    
        def change_view(self, request, object_id, extra_context=None):
            obj = EventModel._event_manager.get(pk=object_id)

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
        
def OccurrenceAdmin(OccurrenceModel):
    class _OccurrenceAdmin(admin.ModelAdmin):
        list_display = ['__unicode__','start','end','event',]
        list_editable = ['start','end','event',]
        # list_filter = ['event',]
    return _OccurrenceAdmin
