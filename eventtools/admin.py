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

from models import Rule

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
        list_display = ('title', 'complete_occurrences_count', 'season')
        change_form_template = 'admin/eventtools/event.html'
        save_on_top = True
        prepopulated_fields = {'slug': ('title', )}
        inlines = [
            OccurrenceInline(EventModel.OccurrenceModel()),
            GeneratorInline(EventModel.GeneratorModel()),
        ]

        def __init__(self, *args, **kwargs):
            super(_EventAdmin, self).__init__(*args, **kwargs)
                
        def get_urls(self):
            return patterns(
                '',
                url(r'(?P<parent_id>\d+)/create_child/',
                    self.admin_site.admin_view(self._create_child))
                ) + super(_EventAdmin, self).get_urls()
        
        def _create_child(self, request, parent_id):
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

class OccurrenceInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        kwargs['queryset'] = kwargs['queryset'].filter(generated_by__isnull=True)
        super(OccurrenceInlineFormSet, self).__init__(*args, **kwargs)

 

def OccurrenceInline(OccurrenceModel):
    class _OccurrenceInline(admin.TabularInline):
        model = OccurrenceModel
        formset = OccurrenceInlineFormSet
        extra = 1
        fields = ('start', 'end',)        
        formfield_overrides = {
            models.DateTimeField: {'form_class': DateAndMaybeTimeField},
        }        
    return _OccurrenceInline


def GeneratorInline(GeneratorModel):
    class _GeneratorInline(admin.TabularInline):
        model = GeneratorModel
        extra = 0
        exclude = ('exceptions', ) #JSON exceptions are going the way of the dinosaurs
        formfield_overrides = {
            models.DateTimeField: {'form_class': DateAndMaybeTimeField},
        }        
    return _GeneratorInline
    
admin.site.register(Rule)
