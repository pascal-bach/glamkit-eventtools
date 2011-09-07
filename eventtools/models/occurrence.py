from datetime import date, time, datetime, timedelta
from dateutil.relativedelta import relativedelta
from vobject.icalendar import utc

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.db.models import signals
from django.db.models.base import ModelBase
from django.template.defaultfilters import urlencode
from django.utils.dateformat import format
from django.utils.translation import ugettext as _
from eventtools.models.xtimespan import XTimespanModel, XTimespanQSFN, XTimespanQuerySet, XTimespanManager

from eventtools.utils import datetimeify, dayify
from eventtools.utils.managertype import ManagerType


"""
eventtools.utils.dateranges has some handy functions for generating parameters for a query:

e.g.
from eventtools.utils import dateranges
dateranges.dates_for_week_of(day) # a tuple
dateranges.dates_in_week_of(day) # a generator

"""

class OccurrenceQSFN(XTimespanQSFN):
    """
    All the query functions are defined here, so they can be easily introspected
    and injected by the OccurrenceManagerType metaclass.
    """

    def events(self):
        """
        Return a queryset corresponding to the events matched by these
        occurrences.
        """
        event_ids = self.values_list('event_id', flat=True).distinct()
        return self.model.EventModel()._event_manager.filter(id__in=event_ids)                
        
class OccurrenceQuerySet(XTimespanQuerySet, OccurrenceQSFN):
    pass #all the goodness is inherited from OccurrenceQuerySetFN

class OccurrenceManager(XTimespanManager):
    __metaclass__ = ManagerType(OccurrenceQSFN, supertype=XTimespanManager.__metaclass__,)

    def get_query_set(self): 
        return OccurrenceQuerySet(self.model)

class OccurrenceModel(XTimespanModel):
    """
    An abstract model for an event occurrence.
    
     Implementing subclasses should define an 'event' ForeignKey to an
    EventModel subclass. The related_name for the ForeignKey should be
    'occurrences'.
    
     Implementing subclasses should define a 'generated_by' ForeignKey to a
    GeneratorModel subclass. The related_name for the ForeignKey should be
    'occurrences'. In almost all situations, this FK should be optional.
    
        event = models.Foreignkey(SomeEvent, related_name="occurrences")
        generated_by = models.ForeignKey(SomeGenerator, blank=True, null=True,
            related_name="occurrences")
    """

    objects = OccurrenceManager()
    
    class Meta:
        abstract = True
        ordering = ('start', 'event',)
        unique_together = ('start', 'event',)

    def __unicode__(self):
        return u"%s: %s" % (self.event, self.timespan_description())
        
    @classmethod
    def EventModel(cls):
        return cls._meta.get_field('event').rel.to

    def is_exclusion(self):
        qs = self.event.exclusions.filter(start=self.start)
        if qs.count():
            return True
        return False
        

    # ical is coming back soon.
    # def get_absolute_url(self):
    #     return self.event.get_absolute_url()
    # 
    # def _resolve_attr(self, attr):
    #     v = getattr(self, attr, None)
    #     if v is not None:
    #         if callable(v):
    #             v = v()
    #     return v
    # 
    # def ical_summary(self):
    #     return unicode(self.event)
    # 
    # def as_icalendar(self,
    #     ical,
    #     request,
    #     summary_attr='ical_summary',
    #     description_attr='ical_description',
    #     url_attr='get_absolute_url',
    #     location_attr='venue_description',
    #     latitude_attr='latitude',
    #     longitude_attr='longitude',
    #     cancelled_attr='is_cancelled',
    # ):
    #     """
    #     Returns the occurrence as an iCalendar object.
    #     
    #     Pass in an iCalendar, and this function will add `self` to it, otherwise it will create a new iCalendar named `calname` described `caldesc`.
    #     
    #     The property parameters passed indicate properties of an Event that return the info to be shown in the ical.
    #     
    #     location_property is the string describing the location/venue.
    #     
    #     Props to Martin de Wulf, Andrew Turner, Derek Willis
    #     http://www.multitasked.net/2010/jun/16/exporting-schedule-django-application-google-calen/
    #     
    #     
    #     """
    #     vevent = ical.add('vevent')
    #     
    #     start = self.start
    #     end = self.end
    #     
    #     if self.all_day:            
    #         vevent.add('dtstart').value = start.date()
    #         vevent.add('dtend').value = end.date()
    #     else:
    #         # Add the timezone specified in the project settings to the event start
    #         # and end datetimes, if they don't have a timezone already
    #         if not start.tzinfo and not end.tzinfo \
    #                 and getattr(settings, 'TIME_ZONE', None):
    #             tz = gettz(settings.TIME_ZONE)
    #             start = start.replace(tzinfo=tz)
    #             end = end.replace(tzinfo=tz)
    #             # Since Google Calendar (and probably others) can't handle timezone
    #             # declarations inside ICS files, convert to UTC before adding.
    #             start = start.astimezone(utc)
    #             end = end.astimezone(utc)
    #         vevent.add('dtstart').value = start
    #         vevent.add('dtend').value = end
    #     
    #     cancelled = self._resolve_attr(cancelled_attr)
    #     if cancelled:
    #         vevent.add('method').value = 'CANCEL'
    #         vevent.add('status').value = 'CANCELLED'
    #             
    #     summary = self._resolve_attr(summary_attr)
    #     if summary:
    #         vevent.add('summary').value = summary
    #     
    #     description = self._resolve_attr(description_attr)
    #     if description:
    #         vevent.add('description').value = description
    #     
    #     url = self._resolve_attr(url_attr)
    #     if url:
    #         domain = "".join(('http', ('', 's')[request.is_secure()], '://', request.get_host()))
    #         vevent.add('url').value = "%s%s" % (domain, url)
    #     
    #     location = self._resolve_attr(location_attr)
    #     if location:
    #         vevent.add('location').value = location
    #         
    #     lat = self._resolve_attr(latitude_attr)
    #     lon = self._resolve_attr(longitude_attr)
    #     if lat and lon:
    #         vevent.add('geo').value = "%s;%s" % (lon, lat)
    #         
    #     return ical 
    # 
    # def ics_url(self):
    #     """
    #     Needs to be fully-qualified (for sending to calendar apps). Your app needs to define
    #     an 'ics_for_occurrence' url, and properties for populating an ics for each event
    #     (see OccurrenceModel.as_icalendar)
    #     """
    #     return django_root_url() + reverse("ics_for_occurrence", args=[self.pk])
    # 
    # def webcal_url(self):
    #     return self.ics_url().replace("http://", "webcal://").replace("https://", "webcal://")
    #     
    # def gcal_url(self):
    #     return  "http://www.google.com/calendar/render?cid=%s" % urlencode(self.ics_url())