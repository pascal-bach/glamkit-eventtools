from django import forms
from django.http import HttpResponseRedirect

FORMAT_CHOICES = [
    ('webcal', 'iCal/Outlook'),
    ('google', 'Google Calendar'),
    ('ics', '.ics file'),
]

class OccurrenceChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.html_timespan()
        

class ExportICalForm(forms.Form):
    """
    Form allows user to choose which occurrence (or all), and which format.
    """
    
    event = forms.ModelChoiceField(
        queryset=None,
        widget=forms.HiddenInput,
        required=True,
    ) #needed in case no (all) occurrence is selected.
    occurrence = OccurrenceChoiceField(
        queryset=None,
        empty_label="Save all",
        required=False,
        widget=forms.Select(attrs={'size':10}),
    )
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        required=True,
        widget=forms.RadioSelect,
        initial="webcal",
    )
    
    def __init__(self, event, *args, **kwargs):        
        self.base_fields['event'].queryset = type(event).objects.filter(id=event.id)
        self.base_fields['event'].initial = event.id
        self.base_fields['occurrence'].queryset = event.occurrences.forthcoming()            

        super(ExportICalForm, self).__init__(*args, **kwargs)

        
    def to_ical(self):
        format = self.cleaned_data['format']
        occurrence = self.cleaned_data['occurrence']

        if occurrence:
            if format == 'webcal':
                return HttpResponseRedirect(occurrence.webcal_url())
            if format == 'ics':
                return HttpResponseRedirect(occurrence.ics_url())
            if format == 'google':
                return HttpResponseRedirect(occurrence.gcal_url())
        else:
            event = self.cleaned_data['event']
            if format == 'webcal':
                return HttpResponseRedirect(event.webcal_url())
            if format == 'ics':
                return HttpResponseRedirect(event.ics_url())
            if format == 'google':
                return HttpResponseRedirect(event.gcal_url())


    # <p><a href="{% url occurrence_ical occurrence.id %}">Download .ics file</a></p>
    # <p><a href="{{ occurrence.webcal_url }}">Add to iCal/Outlook</a></p>
            