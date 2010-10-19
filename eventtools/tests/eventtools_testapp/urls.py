from models import Event, Occurrence
from django.conf.urls.defaults import *

urlpatterns = patterns('eventtools.views',
    url(r'^$', 'occurrence_list', {'qs': Occurrence.objects.all()}, name='occurrence_list'),
    url(r'^(?P<event_slug>[-\w]+)/$', 'event', {'qs': Event.eventobjects.all()}, name='event'),
    url(r'^(?P<event_slug>[-\w]+)/(?P<occurrence_id>\d+)/$', \
        'occurrence', {'qs': Occurrence.objects.all()}, name='occurrence'),
)