import datetime

import django
from django import forms
from django.conf.urls.defaults import patterns, url
from django.contrib import admin, messages
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.http import QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.forms.models import BaseInlineFormSet
from mptt.forms import TreeNodeChoiceField
from mptt.admin import MPTTModelAdmin

from utils.diff import generate_diff

from .models import Rule
# from .filters import IsGeneratedListFilter #needs django 1.4


class DateAndMaybeTimeField(forms.SplitDateTimeField):
    """
    Allow blank time; default to 00:00:00:00 / 11:59:59:99999 (based on field label) 
    These times are time.min and time.max, by the way.
    """

    widget = admin.widgets.AdminSplitDateTime
    
    def clean(self, value):
        """ Override to make the TimeField not required. """
        try:
            return super(DateAndMaybeTimeField, self).clean(value)
        except ValidationError, error:
            if error.messages == [self.error_messages['required']]:
                if value[0] not in validators.EMPTY_VALUES:
                    out = self.compress([self.fields[0].clean(value[0]), None])
                    self.validate(out)
                    return out
            raise
                    
    def compress(self, data_list):
        if data_list:
            if data_list[0] in validators.EMPTY_VALUES:
                raise ValidationError(self.error_messages['invalid_date'])
            if data_list[1] in validators.EMPTY_VALUES:
                if self.label.lower().count('end'):
                    data_list[1] = datetime.time.max
                else:
                    data_list[1] = datetime.time.min
            return datetime.datetime.combine(*data_list)
        return None


def _remove_occurrences(modeladmin, request, queryset):
    for m in queryset:
        # if the occurrence was generated, then add it as an exclusion.
        if m.generated_by is not None:
            m.event.exclusions.get_or_create(start=m.start)
        m.delete()
_remove_occurrences.short_description = "delete occurrences (and create exclusions)"
        
def _convert_to_manual(modeladmin, request, queryset):
    for m in queryset:
        # if the occurrence was generated, then add it as an exclusion.
        if m.generated_by is not None:
            m.event.exclusions.get_or_create(start=m.start)
    queryset.update(generated_by=None)
_convert_to_manual.short_description = "make occurrence manual (and create exclusions)"
    

def OccurrenceAdmin(OccurrenceModel):
    class _OccurrenceAdmin(admin.ModelAdmin):
        list_display = ['string_if_editable', 'start', '_duration', 'is_automatic',]
        list_display_links = ['string_if_editable',]
        # list_display_filter = [IsGeneratedListFilter,] #when 1.4 comes...
        change_list_template = 'admin/eventtools/occurrence_list.html'
        formfield_overrides = {
            models.DateTimeField: {'form_class':DateAndMaybeTimeField},
        }
        fields = ("event_edit_link", "start", "_duration", "generated_by")
        exclude=("event",)
        readonly_fields = ('event_edit_link', 'generated_by')
        actions = [_remove_occurrences, _convert_to_manual]
        date_hierarchy = 'start'
        
        def __init__(self, *args, **kwargs):
            super(_OccurrenceAdmin, self).__init__(*args, **kwargs)
            self.event_model = self.model.EventModel()
  
        def string_if_editable(self, occurrence):
            if occurrence.generated_by is not None:
                return "" #can't click on an empty link
            else:
                return "Edit"
        string_if_editable.short_description = "edit manual occurrences"

        def event_edit_url(self, event):
            return reverse(
                '%s:%s_%s_change' % (
                    self.admin_site.name,
                    self.event_model._meta.app_label,
                    self.event_model._meta.module_name),
                args=(event.id,)
            )
  
        def event_edit_link(self, occurrence):
            return "<a href=\"%s\">%s</a>" % (
                self.event_edit_url(occurrence.event), occurrence.event
            )
        event_edit_link.allow_tags = True
        event_edit_link.short_description = "Event"
  
        def is_automatic(self, occurrence):
            return occurrence.generated_by is not None
        is_automatic.boolean = True
  
        def get_urls(self):
            """
            Add the event-specific occurrence list.
            """
            return patterns('',
                # causes redirect to events list, because we don't want to see all occurrences.
                url(r'^$',
                    self.admin_site.admin_view(self.changelist_view_for_event)),
                url(r'for_event/(?P<event_id>\d+)/$',
                    self.admin_site.admin_view(self.changelist_view_for_event),
                    name="%s_%s_changelist_for_event" % (
                        OccurrenceModel._meta.app_label,
                        OccurrenceModel._meta.module_name)),
                # workaround fix for "../" links in changelist breadcrumbs
                # causes redirect to events changelist
                url(r'for_event/$',
                    self.admin_site.admin_view(self.changelist_view_for_event)),
                url(r'for_event/(?P<event_id>\d+)/(?P<object_id>\d+)/$',
                    self.redirect_to_change_view),
            ) + super(_OccurrenceAdmin, self).get_urls()
      
        def changelist_view_for_event(self, request, event_id=None, extra_context=None):
            if event_id:
                request._event = get_object_or_404(
                    self.event_model, id=event_id)
            else:
                messages.info(
                    request, "Occurrences can only be accessed via events.")
                return redirect("%s:%s_%s_changelist" % (
                        self.admin_site.name, self.event_model._meta.app_label,
                        self.event_model._meta.module_name))
            extra_context = extra_context or {}
            extra_context['root_event'] = request._event
            extra_context['root_event_change_url'] = reverse(
                '%s:%s_%s_change' % (
                    self.admin_site.name,
                    self.event_model._meta.app_label,
                    self.event_model._meta.module_name),
                args=(event_id,))
            return super(_OccurrenceAdmin, self).changelist_view(
                request, extra_context)
     
        def redirect_to_change_view(self, request, event_id, object_id):
            return redirect('%s:%s_%s_change' % (
                    self.admin_site.name,
                    OccurrenceModel._meta.app_label,
                    OccurrenceModel._meta.module_name), object_id)
     
        def queryset(self, request):
            qs = super(_OccurrenceAdmin, self).queryset(request)
            if hasattr(request, '_event'):
                return qs.filter(event=request._event)
            return qs
     
        def get_actions(self, request):
            # remove 'delete' action
            actions = super(_OccurrenceAdmin, self).get_actions(request)
            if 'delete_selected' in actions:
                del actions['delete_selected']
            return actions
     
    return _OccurrenceAdmin

def EventForm(EventModel):
    class _EventForm(forms.ModelForm):
        parent = TreeNodeChoiceField(queryset=EventModel._event_manager.all(), level_indicator=u"-", required=False)

        class Meta:
            model = EventModel
    return _EventForm

def EventAdmin(EventModel, SuperModel=MPTTModelAdmin):
    """ pass in the name of your EventModel subclass to use this admin. """
    
    class _EventAdmin(SuperModel):
        form = EventForm(EventModel)
        list_display = ['title', 'occurrence_link', 'season'] # leave as list to allow extension
        change_form_template = 'admin/eventtools/event.html'
        save_on_top = True
        prepopulated_fields = {'slug': ('title', )}
        inlines = [
            OccurrenceInline(EventModel.OccurrenceModel()),
            GeneratorInline(EventModel.GeneratorModel()),
            ExclusionInline(EventModel.ExclusionModel()),
        ] #leave as a list, not tuple, for easy extension

        def __init__(self, *args, **kwargs):
            super(_EventAdmin, self).__init__(*args, **kwargs)
            self.occurrence_model = EventModel.OccurrenceModel()
                
        def occurrence_edit_url(self, event):
            return reverse("%s:%s_%s_changelist_for_event" % (
                        self.admin_site.name,
                        self.occurrence_model._meta.app_label,
                        self.occurrence_model._meta.module_name),
                        args=(event.id,)
                )
                
        def occurrence_link(self, event):
            count = event.occurrences_count()
            url = self.occurrence_edit_url(event)
            if count == 0:
                return 'No occurrences yet'
            elif count == 1:
                return '<a href="%s">View 1 Occurrence</a>' % (
                    url,
                )
            else:
                return '<a href="%s">View all %s Occurrences</a>' % (
                    url,
                    count,
                )
        occurrence_link.short_description = 'Occurrences'
        occurrence_link.allow_tags = True

        def get_urls(self):
            return patterns(
                '',
                url(r'(?P<parent_id>\d+)/create_variation/',
                    self.admin_site.admin_view(self._create_variation))
                ) + super(_EventAdmin, self).get_urls()
        
        def _create_variation(self, request, parent_id):
            parent = get_object_or_404(EventModel, id=parent_id)
            child = EventModel(parent=parent)
        
            # We don't want to save child yet, as it is potentially incomplete.
            # Instead, we'll get the parent and inheriting fields out of Event
            # and put them into a GET string for the new_event form.
            
            GET = QueryDict("parent=%s" % parent.id).copy()
            
            for field_name in EventModel._event_meta.fields_to_inherit:
                parent_attr = getattr(parent, field_name)
                if parent_attr:
                    if hasattr(parent_attr, 'all'): #for m2m. Sufficient?
                        GET[field_name] = u",".join([unicode(i.pk) for i in parent_attr.all()])
                    elif hasattr(parent_attr, 'pk'): #for fk. Sufficient?
                        GET[field_name] = parent_attr.pk
                    else:
                        GET[field_name] = parent_attr
        
            return redirect(
                reverse("%s:%s_%s_add" % (
                    self.admin_site.name, EventModel._meta.app_label,
                    EventModel._meta.module_name)
                )+"?%s" % GET.urlencode())
        
        def change_view(self, request, object_id, extra_context={}):
            obj = EventModel._event_manager.get(pk=object_id)
        
            if obj.parent:
                fields_diff = generate_diff(obj.parent, obj, include=EventModel._event_meta.fields_to_inherit)
            else:
                fields_diff = None
            extra_extra_context = {
                'fields_diff': fields_diff,
                'django_version': django.get_version()[:3],
                'object': obj,
                'occurrence_edit_url': self.occurrence_edit_url(event=obj),
            }
            extra_context.update(extra_extra_context)      
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

class OccurrenceInlineFormSet(BaseInlineFormSet):
    """
    Shows non-generated occurrences
    """
    def __init__(self, *args, **kwargs):
        kwargs['queryset'] = kwargs['queryset'].filter(generated_by__isnull=True)
        super(OccurrenceInlineFormSet, self).__init__(*args, **kwargs)

def OccurrenceInline(OccurrenceModel):
    class _OccurrenceInline(admin.TabularInline):
        model = OccurrenceModel
        formset = OccurrenceInlineFormSet
        extra = 1
        fields = ('start', '_duration',)        
        formfield_overrides = {
            models.DateTimeField: {'form_class': DateAndMaybeTimeField},
        }        
    return _OccurrenceInline

def ExclusionInline(ExclusionModel):
    class _ExclusionInline(admin.TabularInline):
        model = ExclusionModel
        extra = 0
        fields = ('start',)        
        formfield_overrides = {
            models.DateTimeField: {'form_class': DateAndMaybeTimeField},
        }        
    return _ExclusionInline

def GeneratorInline(GeneratorModel):
    class _GeneratorInline(admin.TabularInline):
        model = GeneratorModel
        extra = 0
        formfield_overrides = {
            models.DateTimeField: {'form_class': DateAndMaybeTimeField},
        }        
    return _GeneratorInline
    
admin.site.register(Rule)
