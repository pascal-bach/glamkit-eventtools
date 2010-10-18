from models import Event, Occurrence
from django.conf.urls.defaults import *

urlpatterns = patterns('eventtools.views',
    url(r'^$', 'event_list', {'qs': Event.objects.all()}, name='occurrence_list'),
    url(r'^event/(?P<event_slug>[-\w]+)/$', 'event', {'qs': Event.objects.all()}, name='event'),
    url(r'^event/(?P<event_slug>[-\w]+)/(?P<occurrence_id>\d+)/$', 'event_occurrence', {'qs': Occurrence.objects.all()}, name='event_occurrence'),
)