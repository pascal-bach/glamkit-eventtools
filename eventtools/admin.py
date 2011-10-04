import datetime

import django
from django import forms
from django.conf import settings
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
from django.utils.translation import ugettext, ugettext_lazy as _

from utils.diff import generate_diff

from .models import Rule
# from .filters import IsGeneratedListFilter #needs django 1.4
MPTT_ADMIN_LEVEL_INDENT = getattr(settings, 'MPTT_ADMIN_LEVEL_INDENT', 10)


class TreeModelChoiceField(forms.ModelChoiceField):
    """ ModelChoiceField which displays depth of objects within MPTT tree. """
    def label_from_instance(self, obj):
        super_label = \
            super(TreeModelChoiceField, self).label_from_instance(obj)
        return u"%s%s" % ("-"*obj.level, super_label)


# ADMIN ACTIONS
def _remove_occurrences(modeladmin, request, queryset):
    for m in queryset:
        # if the occurrence was generated, then add it as an exclusion.
        if m.generated_by is not None:
            m.event.exclusions.get_or_create(start=m.start)
        m.delete()
_remove_occurrences.short_description = "delete occurrences (and create exclusions)"

def _wipe_occurrences(modeladmin, request, queryset):
    queryset.delete()
_wipe_occurrences.short_description = "delete occurrences (without creating exclusions)"


def _convert_to_manual(modeladmin, request, queryset):
    for m in queryset:
        # if the occurrence was generated, then add it as an exclusion.
        if m.generated_by is not None:
            m.event.exclusions.get_or_create(start=m.start)
    queryset.update(generated_by=None)
_convert_to_manual.short_description = "make occurrence manual (and create exclusions)"

class OccurrenceAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OccurrenceAdminForm, self).__init__(*args, **kwargs)
        EventModel = self.instance.EventModel()
        self.fields['event'] = TreeModelChoiceField(EventModel.objects)

        event = self.instance.event
        if event:
            if self.instance.generated_by:
                #generated_by events are limited to children of the generator event
                #(otherwise syncing breaks). TODO: make syncing look at ancestors as well?
                self.fields['event'].queryset = self.instance.generated_by.event.get_descendants(include_self=True)
            else:
                self.fields['event'].queryset = \
                    event.get_descendants(include_self = True) | \
                    event.get_ancestors() | \
                    event.get_siblings()



def OccurrenceAdmin(OccurrenceModel):
    class _OccurrenceAdmin(admin.ModelAdmin):
        form = OccurrenceAdminForm
        list_display = ['event', 'string_if_editable', 'start', '_duration', 'is_automatic',]
        list_display_links = ['string_if_editable',]
        list_editable = ['event']
        # list_filter = [IsGeneratedListFilter,] #when 1.4 comes...
        change_list_template = 'admin/eventtools/occurrence_list.html'
        fields = ("event" , "start", "_duration", "generated_by")
        readonly_fields = ('generated_by', )
        actions = [_remove_occurrences, _wipe_occurrences, _convert_to_manual]
        date_hierarchy = 'start'
        
        def __init__(self, *args, **kwargs):
            super(_OccurrenceAdmin, self).__init__(*args, **kwargs)
            self.event_model = self.model.EventModel()
  
        def string_if_editable(self, occurrence):
            if occurrence.generated_by is not None:
                return "" #can't click on an empty link
            else:
                return "Edit directly"
        string_if_editable.short_description = "edit manual occurrences"

        def get_changelist_form(self, request, **kwargs):
            kwargs.setdefault('form', OccurrenceAdminForm)
            return super(_OccurrenceAdmin, self).get_changelist_form(request, **kwargs)

        def event_edit_url(self, event):
            return reverse(
                '%s:%s_%s_change' % (
                    self.admin_site.name,
                    self.event_model._meta.app_label,
                    self.event_model._meta.module_name),
                args=(event.id,)
            )
  
#        def event_edit_link(self, occurrence):
#            return "<a href=\"%s\">%s</a>" % (
#                self.event_edit_url(occurrence.event), occurrence.event
#            )
#        event_edit_link.allow_tags = True
#        event_edit_link.short_description = "Event"
  
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
            if hasattr(request, '_event'):
                return request._event.occurrences_in_listing()
            else:
                qs = super(_OccurrenceAdmin, self).queryset(request)
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
        list_display = ['title_bold_if_listed', 'occurrence_link', 'season'] # leave as list to allow extension
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

        def title_bold_if_listed(self, obj):
            if obj.is_listed():
                result = "<span style='font-weight:bold;padding-left:%spx'>%s</span>"
            else:
                result = "<span style='font-weight:normal;padding-left:%spx'>%s</span>"

            return result % (
                (5 + MPTT_ADMIN_LEVEL_INDENT * obj.level),
                obj.title,
            )
        title_bold_if_listed.allow_tags = True
        title_bold_if_listed.short_description = _("title (items in bold will be listed; other items are templates or variations)")

        def occurrence_edit_url(self, event):
            return reverse("%s:%s_%s_changelist_for_event" % (
                        self.admin_site.name,
                        self.occurrence_model._meta.app_label,
                        self.occurrence_model._meta.module_name),
                        args=(event.id,)
                )
                
        def occurrence_link(self, event):
            count = event.occurrences_in_listing().count()
            direct_count = event.occurrences.count()

            url = self.occurrence_edit_url(event)
            if not count:
                return 'No occurrences yet'
            elif count == 1:
                r = '<a href="%s">1 Occurrence</a>' % url
            else:
                r = '<a href="%s">%s Occurrences</a>' % (
                    url,
                    count,
                )
            return r + ' (%s direct)' % direct_count
        occurrence_link.short_description = 'Edit Occurrences'
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
    return _OccurrenceInline

def ExclusionInline(ExclusionModel):
    class _ExclusionInline(admin.TabularInline):
        model = ExclusionModel
        extra = 0
        fields = ('start',)        
    return _ExclusionInline

def GeneratorInline(GeneratorModel):
    class _GeneratorInline(admin.TabularInline):
        model = GeneratorModel
        extra = 0
    return _GeneratorInline
    
admin.site.register(Rule)
