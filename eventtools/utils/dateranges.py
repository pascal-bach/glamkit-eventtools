from datetime import *
from dateutil.relativedelta import *
from eventtools.conf import settings
import calendar

WEEKDAY_MAP = {
    calendar.MONDAY: MO,
    calendar.TUESDAY: TU,
    calendar.WEDNESDAY: WE,
    calendar.THURSDAY: TH,
    calendar.FRIDAY: FR,
    calendar.SATURDAY: SA,
    calendar.SUNDAY: SU,
}

def _weekday_fn(wk):
   return WEEKDAY_MAP.get(wk, wk)

FIRST_DAY_OF_WEEK = _weekday_fn(settings.FIRST_DAY_OF_WEEK)
FIRST_DAY_OF_WEEKEND = _weekday_fn(settings.FIRST_DAY_OF_WEEKEND)
LAST_DAY_OF_WEEKEND = _weekday_fn(settings.LAST_DAY_OF_WEEKEND)

class XDateRange(object):
    """
    Embryo class to replace xdaterange below, that allows d1 or d2 to be None.
    
    For now this is only used in calendar sets (which uses the 'in' method)
    """
    def __init__(self, d1, d2):
        self.d1 = d1
        self.d2 = d2
        
    def __contains__(self, d):
        if self.d1 is not None:
            after_start = d >= self.d1
        else:
            after_start = True
        if self.d2 is not None:
            before_end = d <= self.d2
        else:
            before_end = True
        return after_start and before_end  

class DateTester(object):
    """
    A class that takes a set of occurrences. Then you can test dates with it to see if the date is in that set.
    
    if date.today() in date_tester_object:
        ...
    
    """
    def __init__(self, occurrence_qs):
        self.occurrence_qs = occurrence_qs
        
    def __contains__(self, d):
        occs = self.occurrence_qs.starts_on(d)
        return occs
            

        
def xdaterange(d1, d2):
    delta_range = range((d2-d1).days)
    for td in delta_range:
        yield d1 + timedelta(td)
        
def daterange(d1, d2):
    return list(xdaterange(d1, d2))

def dates_for_week_of(d):
    d1 = d + relativedelta(weekday = FIRST_DAY_OF_WEEK(-1))
    d2 = d1 + timedelta(7)
    return d1, d2

def dates_in_week_of(d):
    return daterange(*dates_for_week_of(d))

def dates_for_weekend_of(d):
    d1 = d + relativedelta(weekday = FIRST_DAY_OF_WEEKEND(+1))
    d2 = d1 + relativedelta(weekday = LAST_DAY_OF_WEEKEND(+1))
    return d1, d2

def dates_in_weekend_of(d):
    return daterange(*dates_for_weekend_of(d))

def dates_for_fortnight_of(d): #fortnights overlap
    d1 = d + relativedelta(weekday = FIRST_DAY_OF_WEEK(-1))
    d2 = d1 + timedelta(14)
    return d1, d2

def dates_in_fortnight_of(d):
    return daterange(*dates_for_fortnight_of(d))

def dates_for_month_of(d):
    d1 = d + relativedelta(day=1) #looks like a bug; isn't.
    d2 = d1 + relativedelta(months=+1, days=-1)
    return d1, d2

def dates_in_month_of(d):
    return daterange(*dates_for_month_of(d))

def dates_for_year_of(d):
    d1 = date(d.year, 1, 1)
    d2 = date(d.year, 12, 31)
    return d1, d2

def dates_in_year_of(d):
    return daterange(*dates_for_year_of(d))

def is_weekend(d):
    if type(d) in [date, datetime]:
        d = d.weekday()
    if type(d) == type(MO):
        d = d.weekday
    if FIRST_DAY_OF_WEEKEND <= LAST_DAY_OF_WEEKEND:
        return (FIRST_DAY_OF_WEEKEND.weekday <= d <= LAST_DAY_OF_WEEKEND.weekday)
    else:
        return (d >= FIRST_DAY_OF_WEEKEND.weekday) or (d <= LAST_DAY_OF_WEEKEND.weekday)

def is_weekday(d):
    return not is_weekend(d)