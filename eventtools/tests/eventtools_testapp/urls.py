from models import TestEvent, TestOccurrence
from eventtools.views import EventViews
from django.conf.urls.defaults import *

class TestEventViews(EventViews):
    occurrence_qs = TestOccurrence.objects.all()
    event_qs = TestEvent.eventobjects.all()
    
views = TestEventViews()
    
urlpatterns = views.get_urls()