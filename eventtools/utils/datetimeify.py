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

def dayify(d): #returns two datetimes indicated the date given
    if isinstance(d, datetime):
        d = d.date()
    start = datetimeify(d, clamp=MIN)
    end = datetimeify(d, clamp=MAX)
    return start, end