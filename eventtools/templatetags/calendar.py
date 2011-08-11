import sys, imp

pycal = sys.modules.get('calendar')
if not pycal:
    pycal = imp.load_module('calendar',*imp.find_module('calendar'))

from datetime import date, timedelta
from dateutil.relativedelta import *
from django import template
from django.template.context import RequestContext
from django.template import TemplateSyntaxError

from eventtools.conf import settings as eventtools_settings
from eventtools.models import EventModel, OccurrenceModel

register = template.Library()


class DecoratedDate(object):
    """
    A wrapper for date that has some css classes and a link, to use in rendering
    that date in a calendar.
    """
    def __init__(self, date, href=None, classes=[]):
        self.date = date
        self.href = href
        self.classes = classes
    
    def __unicode__(self):
        if self.href:
            return "%s (%s)" % (self.date, self.href)
        return unicode(self.date)
                
def calendar(
        context, day=None,
        date_class_fn=lambda x: [],
        date_href_fn=lambda x: "",
        month_href_fn=lambda x: "",
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
                    

    Automatic classes:
    
        The class 'today' is given to today's date.

        Every day is given the class of the day of the week 'monday' 'tuesday', 
        etc.

        Leading and trailing days are given the classes 'last_month' and 
        'next_month' respectively.

    """
    today = date.today()

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
            classes = date_class_fn(wday)
            if wday == today:
                classes.append('today')
            if wday == day:
                classes.append('selected')
            if wday.month != day.month:
                if wday < day:
                    classes.append('last_month')
                if wday > day:
                    classes.append('next_month')
            #day of the week class
            classes.append(wday.strftime('%A').lower())
            
            decorated_week.append(
                DecoratedDate(
                    date=wday, href=date_href_fn(wday), classes=classes
                )
            )
        decorated_weeks.append(decorated_week)

    prev = day+relativedelta(months=-1)
    prev_date = date(prev.year, prev.month, 1)
    decorated_prev_date = DecoratedDate(
        date=prev_date, href=month_href_fn(prev_date)
    )
    
    next = day+relativedelta(months=+1)
    next_date = date(next.year, next.month, 1)
    decorated_next_date = DecoratedDate(
        date=next_date, href=month_href_fn(next_date)
    )


    context.update({
        'weeks': decorated_weeks,
        'prev_month': decorated_prev_date,
        'next_month': decorated_next_date,
    })
    
    return context

def nav_calendar(context, occurrences_or_date=None):
    def date_href_fn(day):
        #TODO: make url reverse!
        return "/events?startdate=%s-%s-%s" % (
            day.year, 
            day.month,
            day.day,
        )

    return calendar(
        context, day=occurrences_or_date, 
        date_href_fn=date_href_fn,
        month_href_fn=date_href_fn,
    )

#workaround for takes_context - renders a null template!
register.inclusion_tag("eventtools/calendar/calendar.html", takes_context=True)(nav_calendar)