from models import Event, Occurrence
from eventtools.views import EventViews
from django.conf.urls.defaults import *

class TestEventViews(EventViews):
    occurrence_qs = Occurrence.objects.all()
    event_qs = Event.eventobjects.all()
    
views = TestEventViews()
    
urlpatterns = views.get_urls()