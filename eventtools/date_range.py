from pprint_datetime_range import *

import warnings
warnings.warn("date_range is deprecated and will disappear soon. Use pprint_datetime_range", DeprecationWarning)

def time_range(*args, **kwargs):
    if kwargs.has_key('separatorchar'):
        kwargs['separator'] = kwargs['separatorchar']
        del kwargs['separatorchar']
    if kwargs.has_key('rangechar'):
        kwargs['range_str'] = kwargs['rangechar']
        del kwargs['rangechar']
    if kwargs.has_key('spacechar'):
        kwargs['space'] = kwargs['spacechar']
        del kwargs['spacechar']
    return pprint_time_range(*args, **kwargs)

def date_range(*args, **kwargs):
    if not kwargs.has_key('range_str'):
        kwargs['range_str'] = "&ndash;"    
    if kwargs.has_key('separatorchar'):
        kwargs['separator'] = kwargs['separatorchar']
        del kwargs['separatorchar']
    if kwargs.has_key('rangechar'):
        kwargs['range_str'] = kwargs['rangechar']
        del kwargs['rangechar']
    if kwargs.has_key('spacechar'):
        kwargs['space'] = kwargs['spacechar']
        del kwargs['spacechar']
    return pprint_date_range(*args, **kwargs)
