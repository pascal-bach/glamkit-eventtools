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
from eventtools.models import EventModel

register = template.Library()

def make_calendar(context, date_classes):
    """
    Creates a configurable html calendar displaying one month.
    
    Arguments:
    
    date_classes: a dictionary, containing:
        ['month'] - a date in the month to be displayed (if it isn't given, today is assumed.
        other entries in the dictionary are assumed to be lists of dates.
        Each date in the month is compared with these lists. If the date is in the list, then a css class is given to that day, corresponding to the key of the dictionary. For example:
        
        ['selected'] = (d1, d2, ... dn)
        
        will mark d1..n with the css class 'selected'.
        
        A special case is the 'active' list. Dates in this list will be classed 'active' and will work as links.
        
    The class 'today' is given to today's date.
    Every day is given the class of the day of the week 'monday' 'tuesday', etc.
    Leading and trailing days are given the classes last_month and next_month respectively.
    """
    week_start = eventtools_settings.FIRST_DAY_OF_WEEK

    cal = pycal.Calendar(week_start)

    today = date.today()
    month_day = date_classes.get('month', None)
    if month_day is None:
        month_day = today

    # month_calendar is a list of the weeks in the month of the year as full weeks. Weeks are lists of seven day numbers
    weeks = cal.monthdatescalendar(month_day.year, month_day.month)
    
    annotated_weeks = []
    
    for week in weeks:
        annotated_week = []
        for day in week:
            classes = []
            for css_class, css_dates in date_classes.iteritems():
                if css_class != 'month': #ignore the month config
                    if day in css_dates:
                        classes.append(css_class)
            # now add generic classes
            if day == today:
                classes.append('today')
            if day.month != month_day.month:
                if day < month_day:
                    classes.append('last_month')
                if day > month_day:
                    classes.append('next_month')
            #day of the week
            classes.append(day.strftime('%A').lower())
            annotated_week.append({'date': day, 'classes': classes})
        annotated_weeks.append(annotated_week)
    
    prev = month_day+relativedelta(months=-1)
    prev = date(prev.year, prev.month, 1)
    
    next = month_day+relativedelta(months=+1)
    next = date(next.year, next.month, 1)
                    
    links = {'prev': prev, 'next': next }

    

    context.update({
        'month_day': month_day,
        'month_weeks': annotated_weeks,
        'month_links': links,
    })
    
    return {}

#workarond for takes_context
register.inclusion_tag('eventtools/_empty_.html', takes_context=True)(make_calendar)