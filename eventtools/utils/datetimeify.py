from datetime import datetime, date, time

__all__ = ('datetimeify', 'dayify')

MIN = "min"
MAX = "max"

def datetimeify(dt, tm=None, clamp=MIN):
    # pass in a date or a date and a time or a datetime, pass out a datetime.
    if isinstance(dt, datetime):
        if clamp == MAX and dt.time() == time.min:
            dt = datetime.combine(dt.date(), time.max)
        return dt
    if tm:
        return datetime.combine(dt, tm)
    if clamp.lower()==MAX:
        return datetime.combine(dt, time.max)
    return datetime.combine(dt, time.min)
    
def dayify(d1, d2=None): #returns two datetimes that encompass the day or days given
    if isinstance(d1, datetime):
        d1 = d1.date()
    start = datetimeify(d1, clamp=MIN)
    
    if d2 is not None:
        if isinstance(d2, datetime):
            d2 = d2.date()
        end = datetimeify(d2, clamp=MAX)    
    else:
        end = datetimeify(d1, clamp=MAX)
    return start, end