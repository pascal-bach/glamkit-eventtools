# You can override these settings in Django.
# Import with
# from eventtools.conf import settings

import calendar
FIRST_DAY_OF_WEEK = calendar.MONDAY #you may prefer Saturday or Sunday.
FIRST_DAY_OF_WEEKEND = calendar.SATURDAY
LAST_DAY_OF_WEEKEND = calendar.SUNDAY #you may prefer to add Friday

EVENT_GET_MAP = {
    'startdate': 'startdate',
    'enddate': 'enddate',
}