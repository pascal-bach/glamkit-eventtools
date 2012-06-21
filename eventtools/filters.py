# Needs Django 1.4
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.db.models import F

class IsGeneratedListFilter(SimpleListFilter):
     # Human-readable title which will be displayed in the
     # right admin sidebar just above the filter options.
     title = _('type')

     # Parameter for the filter that will be used in the URL query.
     parameter_name = 'method'

     def lookups(self, request, model_admin):
         """
         Returns a list of tuples. The first element in each
         tuple is the coded value for the option that will
         appear in the URL query. The second element is the
         human-readable name for the option that will appear
         in the right sidebar.
         """
         return (
             ('generated_self', _('Generated in same event')),
             ('generated_ancestor', _('Generated in ancestor event')),
             ('generated', _('Generated anywhere')),
             ('one-off', _('One-off')),
         )

     def queryset(self, request, queryset):
         """
         Returns the filtered queryset based on the value
         provided in the query string and retrievable via
         `self.value()`.
         """
         # Compare the requested value (either '80s' or 'other')
         # to decide how to filter the queryset.


         if self.value() == 'generated_self':
             return queryset.filter(generated_by__event=F('event'))
         if self.value() == 'generated_ancestor':
             return queryset.filter(generated_by__isnull=False).exclude(generated_by__event=F('event'))
         if self.value() == 'generated':
             return queryset.filter(generated_by__isnull=False)
         if self.value() == 'one-off':
             return queryset.filter(generated_by__isnull=True)
