# Needs Django 1.4
# from django.utils.translation import ugettext_lazy as _
# from django.contrib.admin import SimpleListFilter
# 
# class IsGeneratedListFilter(SimpleListFilter):
#     # Human-readable title which will be displayed in the
#     # right admin sidebar just above the filter options.
#     title = _('is_generated')
# 
#     # Parameter for the filter that will be used in the URL query.
#     parameter_name = 'is_generated'
# 
#     def lookups(self, request, model_admin):
#         """
#         Returns a list of tuples. The first element in each
#         tuple is the coded value for the option that will
#         appear in the URL query. The second element is the
#         human-readable name for the option that will appear
#         in the right sidebar.
#         """
#         return (
#             ('yes', _('yes')),
#             ('no', _('no')),
#         )
# 
#     def queryset(self, request, queryset):
#         """
#         Returns the filtered queryset based on the value
#         provided in the query string and retrievable via
#         `self.value()`.
#         """
#         # Compare the requested value (either '80s' or 'other')
#         # to decide how to filter the queryset.
#         if self.value() == 'yes':
#             return queryset.filter(generator__isnull=True)
#         if self.value() == 'no':
#             return queryset.filter(generator__isnull=False)
