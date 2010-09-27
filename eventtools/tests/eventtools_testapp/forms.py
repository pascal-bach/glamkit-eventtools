from django.forms import ModelForm
from .models import LectureEvent


class LectureEventForm(ModelForm):
    class Meta:
        model = LectureEvent

class LectureEventOccurrenceForm(ModelForm):
    class Meta:
        model = LectureEvent.Occurrence

class LectureEventOccurrenceGeneratorForm(ModelForm):
    class Meta:
        model = LectureEvent.OccurrenceGenerator
