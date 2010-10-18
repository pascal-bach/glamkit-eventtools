from django.db import models
from eventtools.utils import datetimeify, dayify
from datetime import date, time, datetime
from eventtools.conf import settings
from eventtools.utils import dateranges
from eventtools.utils.pprint_timespan import pprint_datetime_span

from dateutil import parser as dateparser
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class OccurrenceQuerySetFN(object):
    """
    All the query functions are defined here, so they can be easily inspected by the manager metaclass.
    """

    def starts_before(self, date):
        end = datetimeify(date, clamp="max")
        return self.filter(start__lte=end)
    def ends_before(self, date):
        end = datetimeify(date, clamp="max")
        return self.filter(end__lte=end)

    def starts_after(self, date):
        start = datetimeify(date, clamp="min")
        return self.filter(start__gte=start)
    def ends_after(self, date):
        start = datetimeify(date, clamp="min")
        return self.filter(end__gte=start)

    def starts_between(self, d1, d2, forthcoming_only=False, test=False):
        """
        returns the occurrences that start in a given date/datetime range
        if forthcoming_only == True, and now is between start and end, then 
        only occurrences that start AFTER datetime.now() are included.
        """
        if forthcoming_only:
            now = datetime.now()
            if d1 <= now <= d2:
                d1 = now
        return self.starts_after(d1).starts_before(d2)     
    def ends_between(self, d1, d2, forthcoming_only=False):
        if forthcoming_only:
            now = datetime.now()
            if d1 <= now <= d2:
                d1 = now
        return self.ends_after(d1).ends_before(d2)
    def entirely_between(self, d1, d2, forthcoming_only=False):
        """
        returns the occurrences that both start and end in a given datetime range
        """
        if forthcoming_only:
            now = datetime.now()
            if d1 <= now <= d2:
                d1 = now
        return self.starts_after(d1).ends_before(d2)

    def starts_on(self, day, forthcoming_only=False):
        d1, d2 = dayify(day)
        return self.starts_between(d1, d2, forthcoming_only)
    def ends_on(self, day, forthcoming_only=False):
        d1, d2 = dayify(day)
        return self.ends_between(d1, d2, forthcoming_only)
    def entirely_on(self, day, forthcoming_only=False):
        d1, d2 = dayify(day)
        return self.entirely_between(d1, d2, forthcoming_only)
    
    def starts_in_week_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_week_of(day)
        return self.starts_between(d1, d2, forthcoming_only)
    def ends_in_week_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_week_of(day)
        return self.ends_between(d1, d2, forthcoming_only)
    def entirely_in_week_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_week_of(day)
        return self.entirely_between(d1, d2, forthcoming_only)

    def starts_in_weekend_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_weekend_of(day)
        return self.starts_between(d1, d2, forthcoming_only)
    def ends_in_weekend_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_weekend_of(day)
        return self.ends_between(d1, d2, forthcoming_only)
    def entirely_in_weekend_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_weekend_of(day)
        return self.entirely_between(d1, d2, forthcoming_only)

    def starts_in_fortnight_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_fortnight_of(day)
        return self.starts_between(d1, d2, forthcoming_only)
    def ends_in_fortnight_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_fortnight_of(day)
        return self.ends_between(d1, d2, forthcoming_only)
    def entirely_in_fortnight_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_fortnight_of(day)
        return self.entirely_between(d1, d2, forthcoming_only)

    def starts_in_month_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_month_of(day)
        return self.starts_between(d1, d2, forthcoming_only)
    def ends_in_month_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_month_of(day)
        return self.ends_between(d1, d2, forthcoming_only)
    def entirely_in_month_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_month_of(day)
        return self.entirely_between(d1, d2, forthcoming_only)

    def starts_in_year_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_year_of(day)
        return self.starts_between(d1, d2, forthcoming_only)
    def ends_in_year_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_year_of(day)
        return self.ends_between(d1, d2, forthcoming_only)
    def entirely_in_year_of(self, day, forthcoming_only=False):
        d1, d2 = dateranges.dates_for_year_of(day)
        return self.entirely_between(d1, d2, forthcoming_only)

    #queries relative to now
    def starts_today(self, forthcoming_only=False):
        return self.starts_on(date.today(), forthcoming_only)
    def ends_today(self, forthcoming_only=False):
        return self.ends_on(date.today(), forthcoming_only)
    def entirely_today(self, forthcoming_only=False):
        return self.entirely_on(date.today(), forthcoming_only)

    def starts_this_week(self, forthcoming_only=False):
        return self.starts_in_week_of(date.today(), forthcoming_only)
    def ends_this_week(self, forthcoming_only=False):
        return self.ends_in_week_of(date.today(), forthcoming_only)
    def entirely_this_week(self, forthcoming_only=False):
        return self.entirely_in_week_of(date.today(), forthcoming_only)

    def starts_this_weekend(self, forthcoming_only=False):
        return self.starts_in_weekend_of(date.today(), forthcoming_only)
    def ends_this_weekend(self, forthcoming_only=False):
        return self.ends_in_weekend_of(date.today(), forthcoming_only)
    def entirely_this_weekend(self, forthcoming_only=False):
        return self.entirely_in_weekend_of(date.today(), forthcoming_only)

    def starts_this_fortnight(self, forthcoming_only=False):
        return self.starts_in_fortnight_of(date.today(), forthcoming_only)
    def ends_this_week(self, forthcoming_only=False):
        return self.ends_in_fortnight_of(date.today(), forthcoming_only)
    def entirely_this_week(self, forthcoming_only=False):
        return self.entirely_in_fortnight_of(date.today(), forthcoming_only)

    def starts_this_month(self, forthcoming_only=False):
        return self.starts_in_month_of(date.today(), forthcoming_only)
    def ends_this_month(self, forthcoming_only=False):
        return self.ends_in_month_of(date.today(), forthcoming_only)
    def entirely_this_month(self, forthcoming_only=False):
        return self.entirely_in_month_of(date.today(), forthcoming_only)

    def starts_this_year(self, forthcoming_only=False):
        return self.starts_in_year_of(date.today(), forthcoming_only)
    def ends_this_year(self, forthcoming_only=False):
        return self.ends_in_year_of(date.today(), forthcoming_only)
    def entirely_this_year(self, forthcoming_only=False):
        return self.entirely_in_year_of(date.today(), forthcoming_only)



    def starts_yesterday(self):
        return self.starts_on(date.today()-timedelta(1))
    def ends_yesterday(self):
        return self.ends_on(date.today()-timedelta(1))
    def entirely_yesterday(self):
        return self.entirely_on(date.today()-timedelta(1))

    def starts_last_week(self):
        return self.starts_in_week_of(date.today()-timedelta(7))
    def ends_last_week(self):
        return self.ends_in_week_of(date.today()-timedelta(7))
    def entirely_last_week(self):
        return self.entirely_in_week_of(date.today()-timedelta(7))

    def starts_last_weekend(self):
        return self.starts_in_weekend_of(date.today()-timedelta(7))
    def ends_last_weekend(self):
        return self.ends_in_weekend_of(date.today()-timedelta(7))
    def entirely_last_weekend(self):
        return self.entirely_in_weekend_of(date.today()-timedelta(7))

    def starts_last_fortnight(self):
        return self.starts_in_fortnight_of(date.today()-timedelta(14))
    def ends_last_week(self):
        return self.ends_in_fortnight_of(date.today()-timedelta(14))
    def entirely_last_week(self):
        return self.entirely_in_fortnight_of(date.today()-timedelta(14))

    def starts_last_month(self):
        return self.starts_in_month_of(date.today()+relativedelta(months=-1))
    def ends_last_month(self):
        return self.ends_in_month_of(date.today()+relativedelta(months=-1))
    def entirely_last_month(self):
        return self.entirely_in_month_of(date.today()+relativedelta(months=-1))

    def starts_last_year(self):
        return self.starts_in_year_of(date.today()+relativedelta(years=-1))
    def ends_last_year(self):
        return self.ends_in_year_of(date.today()+relativedelta(years=-1))
    def entirely_last_year(self):
        return self.entirely_in_year_of(date.today()+relativedelta(years=-1))



    def starts_tomorrow(self):
        return self.starts_on(date.today()+timedelta(1))
    def ends_tomorrow(self):
        return self.ends_on(date.today()+timedelta(1))
    def entirely_tomorrow(self):
        return self.entirely_on(date.today()+timedelta(1))

    def starts_next_week(self):
        return self.starts_in_week_of(date.today()+timedelta(7))
    def ends_next_week(self):
        return self.ends_in_week_of(date.today()+timedelta(7))
    def entirely_next_week(self):
        return self.entirely_in_week_of(date.today()+timedelta(7))

    def starts_next_weekend(self):
        return self.starts_in_weekend_of(date.today()+timedelta(7))
    def ends_next_weekend(self):
        return self.ends_in_weekend_of(date.today()+timedelta(7))
    def entirely_next_weekend(self):
        return self.entirely_in_weekend_of(date.today()+timedelta(7))

    def starts_next_fortnight(self):
        return self.starts_in_fortnight_of(date.today()+timedelta(14))
    def ends_next_week(self):
        return self.ends_in_fortnight_of(date.today()+timedelta(14))
    def entirely_next_week(self):
        return self.entirely_in_fortnight_of(date.today()+timedelta(14))

    def starts_next_month(self):
        return self.starts_in_month_of(date.today()+relativedelta(months=1))
    def ends_next_month(self):
        return self.ends_in_month_of(date.today()+relativedelta(months=1))
    def entirely_next_month(self):
        return self.entirely_in_month_of(date.today()+relativedelta(months=1))

    def starts_next_year(self):
        return self.starts_in_year_of(date.today()+relativedelta(years=+1))
    def ends_next_year(self):
        return self.ends_in_year_of(date.today()+relativedelta(years=+1))
    def entirely_next_year(self):
        return self.entirely_in_year_of(date.today()+relativedelta(years=+1))

    #defaults
    before = starts_before
    after = starts_after
    between = starts_between
    on = starts_on
    in_week_of = starts_in_week_of
    in_weekend_of = starts_in_weekend_of
    in_fortnight_of = starts_in_fortnight_of
    in_month_of = starts_in_month_of
    in_year_of = starts_in_year_of
    # default shortcuts
    today = starts_today
    this_week = starts_this_week
    this_weekend = starts_this_weekend
    this_fortnight = starts_this_fortnight
    this_month = starts_this_month
    this_year = starts_this_year
    yesterday = starts_yesterday
    last_week = starts_last_week
    last_weekend = starts_last_weekend
    last_fortnight = starts_last_fortnight
    last_month = starts_last_month
    last_year = starts_last_year
    tomorrow = starts_tomorrow
    next_week = starts_next_week
    next_weekend = starts_next_weekend
    next_fortnight = starts_next_fortnight
    next_month = starts_next_month
    next_year = starts_next_year

    #misc queries (note they assume starts_ and ends_)
    def forthcoming(self):
        return self.starts_after(datetime.now())

    def recent(self):
        return self.ends_before(datetime.now())
        
    def now_on(self):
        n = datetime.now()
        return self.starts_before(n).ends_after(n)
        
    def events(self):
        """
        Return a queryset corresponding to the events matched by these occurrences.
        """
        event_ids = self.values_list('event_id', flat=True).distinct()
        return self.model.Event().objects.filter(id__in=event_ids)
        
    def from_GET(self, GET={}):
        mapped_GET = {}
        for k, v in GET.iteritems():
            mapped_GET[settings.EVENT_GET_MAP.get(k, k)] = v
        
        fr = mapped_GET.get('startdate', None)
        to = mapped_GET.get('enddate', None)
        
        if fr is not None:
            fr = dateparser.parse(fr)
        if to is not None:
            to = dateparser.parse(to)

        if fr is None:
            if to is None:
                return self.forthcoming()
            else:
                return self.before(to)
        else:
            if to is None:
                return self.after(fr)
            else:
                return self.between(fr, to)
                
        
class OccurrenceQuerySet(models.query.QuerySet, OccurrenceQuerySetFN):
    pass #all the goodness is inherited from OccurrenceQuerySetFN

class OccurrenceManagerType(type):
    """
    Injects proxies for all the queryset's functions into the Manager
    """
    @staticmethod
    def _fproxy(name):
        def f(self, *args, **kwargs):
            return getattr(self.get_query_set(), name)(*args, **kwargs)
        return f

    def __init__(cls, *args):
        for fname in dir(OccurrenceQuerySetFN):
            if not fname.startswith("_"):
                setattr(cls, fname, OccurrenceManagerType._fproxy(fname))
        super(OccurrenceManagerType, cls).__init__(*args)

class OccurrenceManager(models.Manager):    
    __metaclass__ = OccurrenceManagerType

    def get_query_set(self): 
        return OccurrenceQuerySet(self.model)

class OccurrenceModel(models.Model):
    """
    An abstract model for an event occurrence.
    
    Implementing subclasses should define 'event' ForeignKey to an EventModel subclass. The related_name for the ForeignKey should be 'occurrences'.

    event = models.Foreignkey(SomeEvent, related_name="occurrences")
    """
    start = models.DateTimeField(db_index=True)
    end = models.DateTimeField(blank=True, db_index=True)
        
    objects = OccurrenceManager()
    
    class Meta:
        abstract = True
        ordering = ('start', 'end',)

    def clean(self):
        if self.start > self.end:
            raise ValidationError('start must be earlier than end')
        super(OccurrenceModel, self).clean()

    def save(self, *args, **kwargs):
        if self.end is None:
            self.end = self.start

        self.start = datetimeify(self.start, clamp="min")
        self.end = datetimeify(self.end, clamp="max")
        if self.end.time == time.min:
            self.end.time == time.max

        if self.start > self.end:
            raise AttributeError('start must be earlier than end')
        
        
        super(OccurrenceModel, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return "%s: %s" % (self.event, self.timespan_description())
        
    @classmethod
    def Event(cls):
        return cls._meta.get_field('event').rel.to
        
    def duration(self):
        return self.end - self.start
        
    def relative_duration(self):
        return relativedelta(self.end, self.start)
    
    def timespan_description(self):
        return pprint_datetime_span(self.start, self.end)
        
    @property
    def has_finished(self):
        return self.end < datetime.now()
        
    @property
    def has_started(self):
        return self.start < datetime.now()
        
    @property
    def now_on(self):
        return self.has_started and not self.has_finished
        
    def time_to_go(self):
        """
        If self is in future, return + timedelta.
        If self is in past, return - timedelta.
        If self is now on, return None
        """
        if not self.has_started:
            return self.start - datetime.now()
        if self.has_finished:
            return self.end - datetime.now()
        return None

    def relative_time_to_go(self):
        """
        If self is in future, return + timedelta.
        If self is in past, return - timedelta.
        If self is now on, return None
        """
        if not self.has_started:
            return relativedelta(self.start, datetime.now())
        if self.has_finished:
            return relativedelta(self.end, datetime.now())
        return None
                