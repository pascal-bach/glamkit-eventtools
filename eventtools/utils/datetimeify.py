from datetime import datetime, date, time

__all__ = ('datetimeify', 'dayify')

MIN = "min"
MAX = "max"

def datetimeify(d, t=None, clamp=MIN):
    # pass in a date or a date and a time or a datetime, pass out a datetime.
    if isinstance(d, datetime):
        if clamp == MAX and d.time() == time.min:
            d = datetime.combine(d.date(), time.max)
        return d
    if t:
        return datetime.combine(d, t)
    if clamp.lower()==MAX:
        return datetime.combine(d, time.max)
    return datetime.combine(d, time.min)

def dayify(d, d2=None): #returns two datetimes that encompass the day or days given
    if isinstance(d, datetime):
        d = d.date()
    start = datetimeify(d, clamp=MIN)
    
    if d2 is not None:
        if isinstance(d2, datetime):
            d2 = d2.date()
        end = datetimeify(d2, clamp=MAX)    
    else:
        end = datetimeify(d, clamp=MAX)
    return start, end