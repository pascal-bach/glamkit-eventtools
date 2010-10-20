from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from diff import generate_diff
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
import django
from eventtools import adminviews

def create_children(modeladmin, request, queryset):
    for event in queryset:
        e = type(event)._event_manager.create(parent=event)
create_children.short_description = "Create children of selected events"


def EventAdmin(EventModel): #pass in the name of your EventModel subclass to use this admin.
    class _EventAdmin(MPTTModelAdmin):
        list_display = ('__unicode__', 'occurrence_link')
        actions = [create_children]
        exclude = ['parent']
        change_form_template = 'admin/eventtools/event.html'
        save_on_top = True

        def __init__(self, *args, **kwargs):
            super(_EventAdmin, self).__init__(*args, **kwargs)
            self.occurrence_model = self.model.occurrences.related.model
        
        def occurrence_link(self, event):
            return '<a href="%s?event_id=%d">View Occurrences</a>' % (
                reverse("%s:%s_%s_changelist" % (
                        self.admin_site.name,
                        self.occurrence_model._meta.app_label,
                        self.occurrence_model._meta.module_name)), event.id)
                
        occurrence_link.short_description = 'Occurrences'
        occurrence_link.allow_tags = True
        
        # list_display = ('title', 'edit_occurrences_link', 'all_occurrences_count', 'my_occurrences_count')

        # def get_urls(self):
        #     super_urls = super(EventAdminBase, self).get_urls()
        #     my_urls = patterns('',
        #         url(r'^(?P<id>\d+)/occurrences/$', self.admin_site.admin_view(adminviews.occurrences), {'modeladmin': self}),
        #         # url(r'^(?P<event_id>\d+)/create_exception/(?P<gen_id>\d+)/(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})/(?P<hour>\d{1,2})-(?P<minute>\d{1,2})-(?P<second>\d{1,2})/$', self.admin_site.admin_view(make_exceptional_occurrence), {'modeladmin': self}),
        #     )
        #     return my_urls + super_urls

        def get_urls(self):
            return patterns(
                '',
                url(r'(?P<parent_id>\d+)/create_child/',
                    self.admin_site.admin_view(self.create_child))
                ) + super(_EventAdmin, self).get_urls()

        def create_child(self, request, parent_id):
            parent = get_object_or_404(EventModel, id=parent_id)
            child = EventModel._default_manager.create(parent=parent)
            return redirect("%s:%s_%s_change" % (
                    self.admin_site.name, EventModel._meta.app_label,
                    EventModel._meta.module_name), child.id)
        
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

        def __init__(self, *args, **kwargs):
            super(_OccurrenceAdmin, self).__init__(*args, **kwargs)
            self.event_model = self.model.event.field.rel.to
        
        def changelist_view(self, request, extra_context=None):
            if 'event_id' in request.GET:
                request._event = get_object_or_404(
                    self.event_model, id=request.GET['event_id'])
                # remove from immutable GET, or use a proper url?
                GET = request.GET.copy()
                GET.pop('event_id')
                request.GET = GET
            else:
                messages.info(
                    request, "Occurrences can only be accessed via events.")
                return redirect("%s:%s_%s_changelist" % (
                        self.admin_site.name, self.event_model._meta.app_label,
                        self.event_model._meta.module_name))

            return super(_OccurrenceAdmin, self).changelist_view(
                request, extra_context)

        def queryset(self, request):
            queryset = super(_OccurrenceAdmin, self).queryset(request)
            if hasattr(request, '_event'):
                event_ids = request._event.get_descendants().values_list(
                    'id', flat=True)
                queryset = queryset.filter(event__id__in=event_ids)
            return queryset

    return _OccurrenceAdmin
