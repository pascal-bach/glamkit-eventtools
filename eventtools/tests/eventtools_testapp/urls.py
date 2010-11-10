from models import ExampleEvent, ExampleOccurrence
from eventtools.views import EventViews
from django.conf.urls.defaults import *

class TestEventViews(EventViews):
    occurrence_qs = ExampleOccurrence.objects.all()
    event_qs = ExampleEvent.eventobjects.all()
    
views = TestEventViews()
    
urlpatterns = views.get_urls()