from datetime import date, time
from eventtools.utils import datetimeify, MIN, MAX
from eventtools.pprint_datetime_span import pprint_datetime_span, pprint_time_span
from django.utils.timesince import timesince
from django.utils.translation import ugettext, ugettext_lazy as _

class SmartDateTimeSpan(object):
    def __init__(self, sd=None, st=None, ed=None, et=None, sdt=None, edt=None):
        """
        Does commonly-needed things with time ranges that may or may not include times.
        
        RULES:
        - start date is compulsory.
        - end date is set to start date if not provided
        - start time and end time are not compulsory
        - end time requires a start time.
        
        Times are voluntary, but to omit them may mean either that they are unknown, or that the event is 'all-day'.
        To explicitly indicate an 'all-day' event, use time.min and time.max in the time fields.
        
        """
        
        #passed in datetimes instead?
        if sdt is not None:
            sd = sdt.date()
            st = sdt.time()
        if edt is not None:
            ed = edt.date()
            et = edt.time()

        if not sd:
            raise AttributeError("Start date is required")

        if et and not st:
            raise AttributeError("May not have an end time without a start time")
        
        #shortcuts
        self.start_date = self.sd = sd
        self.start_time = self.st = st
        self.end_date = self.ed = ed or sd
        self.end_time = self.et = et or st
        
        if self.start_datetime > self.end_datetime:
            raise AttributeError("End time is before start time")
        
    def __unicode__(self):
        return self.robot_description()
        
    def __repr__(self):
        return self.robot_description()

    def __cmp__(self, other):
        
        #if the dates are different, return those
        c1 = cmp(self.sd, other.sd)
        if c1 != 0:
            return c1
        
        if self.dates_only:
            if other.dates_only:
                return cmp(self.ed, other.ed)
            else:
                return -1 #put self first if other has times
        else:
            if other.dates_only:
                return 1 #put other first if self has times
            else:
                return cmp(self.st, other.st) or cmp(self.et, other.et)
            
    def __eq__(self, other):
        return self.sd == other.sd and \
            self.st == other.st and \
            self.ed == other.ed and \
            self.et == other.et
    
    @property
    def all_day(self):
        return self.st == time.min and self.et == time.max

    @property
    def dates_only(self):
        return self.all_day or (self.st is None and self.et is None)
    
    @property
    def start_datetime(self):
        return datetimeify(self.sd, self.st, clamp=MIN)

    @property
    def end_datetime(self):
        return datetimeify(self.ed, self.et, clamp=MAX)
        
    @property
    def start(self):
        if self.dates_only:
            return self.start_date
        else:
            return self.start_datetime

    @property
    def end(self):
        if self.dates_only:
            return self.end_date
        else:
            return self.end_datetime
    
    def robot_description(self):
        return pprint_datetime_span(self.sd, self.st, self.ed, self.et)

    def robot_time_description(self):
        return pprint_time_span(self.st, self.et)

    def robot_start_time_description(self):
        return pprint_time_span(self.st, self.st)

    def robot_end_time_description(self):
        return pprint_time_span(self.et, self.et)

    def start_description(self):
        if self.dates_only:
            return ugettext("%(day)s") % {
                'day': self.sd.strftime('%a, %d %b %Y'),
            }            
        else:
            return ugettext("%(day)s, %(time)s") % {
                'day': self.start_datetime.strftime('%a, %d %b %Y'),
                'time': self.start_datetime.strftime('%H:%M'),
            }
        
    def duration(self):
        if self.dates_only:
            return self.ed - self.sd
        else:
            return self.end_datetime - self.start_datetime
    
    def humanized_duration(self):
        if self.dates_only:
            return timesince(self.sd, self.ed)
        else:
            return timesince(self.start_datetime, self.end_datetime)