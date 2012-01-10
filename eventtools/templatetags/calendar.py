import sys, imp

pycal = sys.modules.get('calendar')
if not pycal:
    pycal = imp.load_module('calendar',*imp.find_module('calendar'))

import datetime
from dateutil.relativedelta import *
from django import template
from django.template.context import RequestContext
from django.template import TemplateSyntaxError
from django.core.urlresolvers import reverse

from eventtools.conf import settings as eventtools_settings
from eventtools.models import EventModel, OccurrenceModel

register = template.Library()

def DATE_HREF_FACTORY(test_dates=True, dates=[]):
    """
    If test_dates is True, then URLs will only be returned if the day is in the
    dates iterable.
    
    If test_dates is False, URLs are always returned.
    """
    def f(day):
        """
        Given a day, return a URL to navigate to.
        """
        if (test_dates and day in dates) or (not test_dates):
            return reverse('events:on_date', args=(
                day.year, 
                day.month,
                day.day,
            ))
        return None
    return f

def DATE_CLASS_HIGHLIGHT_FACTORY(dates, selected_day):
    def f(day):
        r = set()
        if day == selected_day:
            r.add('selected')
        if day in dates:
            r.add('highlight')
        return r
    return f

class DecoratedDate(object):
    """
    A wrapper for date that has some css classes and a link, to use in rendering
    that date in a calendar.
    """
    def __init__(self, date, href=None, classes=[], data=""):
        self.date = date
        self.href = href
        self.classes = classes
        self.data = data
    
    def __unicode__(self):
        if self.href:
            return "%s (%s)" % (self.date, self.href)
        return unicode(self.date)
                
def calendar(
        context, day=None,
        date_class_fn=None,
        date_href_fn=None,
        month_href_fn=None,
    ):
    """
    Creates an html calendar displaying one month, where each day has a link and
    various classes, followed by links to the previous and next months.
    
    Arguments:
    
    context:        context from the parent template
    day:            a date or occurrence defining the month to be displayed
                    (if it isn't given, today is assumed).
    date_class_fn:  a function that returns an iterable of CSS classes,
                    given a date.
    date_href_fn:   a function that returns the url for a date, given a date
    month_href_fn:  a function that returns the url for a date, given a date
                    (which will be the first day of the next and previous
                    months)
                    

    Automatic attributes:
    
        Every day is given the 'data' attribute of the date in ISO form.

        The class 'today' is given to today's date.

        Every day is given the class of the day of the week 'monday' 'tuesday', 
        etc.

        Leading and trailing days are given the classes 'last_month' and 
        'next_month' respectively.

    """
    
    if date_class_fn is None:
        date_class_fn = lambda x: set()
        
    if date_href_fn is None:
        date_href_fn = lambda x: None

    if month_href_fn is None:
        month_href_fn = lambda x: None
    
    today = datetime.date.today()

    if day is None:
        day = today
    else:
        try:
            day = day[0]
        except TypeError:
            pass
        
    if isinstance(day, OccurrenceModel):
        day = day.start.date()

    cal = pycal.Calendar(eventtools_settings.FIRST_DAY_OF_WEEK)
    # cal is a list of the weeks in the month of the year as full weeks. 
    # Weeks are lists of seven dates
    weeks = cal.monthdatescalendar(day.year, day.month)
    
    # Transform into decorated dates
    decorated_weeks = []
    for week in weeks:
        decorated_week = []
        for wday in week:
            classes = set(date_class_fn(wday))
            if wday == today:
                classes.add('today')
            if wday.month != day.month:
                if wday < day:
                    classes.add('last_month')
                if wday > day:
                    classes.add('next_month')
            #day of the week class
            classes.add(wday.strftime('%A').lower())
            #ISO class
            data = wday.isoformat()
            
            decorated_week.append(
                DecoratedDate(
                    date=wday, href=date_href_fn(wday), classes=classes, data=data,
                )
            )
        decorated_weeks.append(decorated_week)

    prev = day+relativedelta(months=-1)
    prev_date = datetime.date(prev.year, prev.month, 1)
    decorated_prev_date = DecoratedDate(
        date=prev_date, href=month_href_fn(prev_date)
    )
    
    next = day+relativedelta(months=+1)
    next_date = datetime.date(next.year, next.month, 1)
    decorated_next_date = DecoratedDate(
        date=next_date, href=month_href_fn(next_date)
    )


    context.update({
        'weeks': decorated_weeks,
        'prev_month': decorated_prev_date,
        'next_month': decorated_next_date,
    })
    
    return context


def nav_calendar(
        context, date=None, occurrence_qs=[],
        date_href_fn=None,
        month_href_fn=None,
        date_class_fn=None,
    ):
    """
    Renders a nav calendar for a date, and an optional occurrence_qs.
    Dates in the occurrence_qs are given the class 'highlight'.
    """
    
    #TODO: allow dates, not just occurrence_qs
    if occurrence_qs:
        occurrence_days = [o.start.date() for o in occurrence_qs]
    else:
        occurrence_days = []
    
    if date_href_fn is None:
        date_href_fn = DATE_HREF_FACTORY(dates=occurrence_days)

    if month_href_fn is None:
        month_href_fn = DATE_HREF_FACTORY(test_dates = False)
        
    if date_class_fn is None:
        date_class_fn = DATE_CLASS_HIGHLIGHT_FACTORY(dates=occurrence_days, selected_day = date)

    return calendar(
        context, day=date, 
        date_href_fn=date_href_fn,
        date_class_fn=date_class_fn,
        month_href_fn=month_href_fn,
    )

def nav_calendars(
        context, occurrence_qs=[], selected_occurrence=None,
        date_href_fn=None,
        date_class_fn=None,
    ):
    """
    Renders several calendars, so as to encompass all dates in occurrence_qs.
    These will be folded up into a usable widget with javascript.
    """
    
    #TODO: allow dates, not just occurrence_qs
    if date_class_fn is None and occurrence_qs:
        occurrence_days = [o.start.date() for o in occurrence_qs]
        if selected_occurrence:
            date_class_fn = DATE_CLASS_HIGHLIGHT_FACTORY(occurrence_days, selected_occurrence.start.date())
        else:
            date_class_fn = DATE_CLASS_HIGHLIGHT_FACTORY(occurrence_days, None)


    calendars = []
    if occurrence_qs.count() > 0:
        first_date = occurrence_qs[0].start.date()
        last_date = occurrence_qs.reverse()[0].start.date()
    else:
        first_date = last_date = datetime.date.today()
    first_month = datetime.date(first_date.year, first_date.month, 1)
    month = first_month
    
    while month <= last_date:
        calendars.append(
             calendar(
                {}, day=month, 
                date_href_fn=date_href_fn,
                date_class_fn=date_class_fn,
            )
        )
        month += relativedelta(months=+1)


    context.update({
        'calendars': calendars
    })
    return context

register.inclusion_tag("eventtools/calendar/calendar.html", takes_context=True)(calendar)
register.inclusion_tag("eventtools/calendar/calendar.html", takes_context=True)(nav_calendar)
register.inclusion_tag("eventtools/calendar/calendars.html", takes_context=True)(nav_calendars)