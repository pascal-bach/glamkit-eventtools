from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse
from eventtools.conf import settings
from datetime import date
from dateutil import parser as dateparser
from vobject import iCalendar


def paginate(request, pool):
    paginator = Paginator(pool, settings.OCCURRENCES_PER_PAGE)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

   # If page request (9999) is out of range, deliver last page of results.
    try:
        pageinfo = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pageinfo = paginator.page(paginator.num_pages)

    return pageinfo

def parse_GET_date(GET={}):
    mapped_GET = {}
    for k, v in GET.iteritems():
        mapped_GET[settings.EVENT_GET_MAP.get(k, k)] = v

    fr = mapped_GET.get('startdate', None)
    to = mapped_GET.get('enddate', None)

    if fr is not None:
        try:
            fr = dateparser.parse(fr).date()
        except ValueError:
            fr = None
    if to is not None:
        try:
            to = dateparser.parse(to).date()
        except ValueError:
            to = None

    if fr is None:
        fr = date.today()
            
    return fr, to
    
def response_as_ical(request, occurrences):
    ical = iCalendar()
    ical.add('X-WR-CALNAME').value = settings.ICAL_CALNAME
    ical.add('X-WR-CALDESC').value = settings.ICAL_CALDESC
    ical.add('method').value = 'PUBLISH'  # IE/Outlook needs this

    if hasattr(occurrences, '__iter__'):
        for occ in occurrences:
            ical = occ.as_icalendar(ical, request)
    else:
        ical = occurrences.as_icalendar(ical, request)
    
    icalstream = ical.serialize()
    response = HttpResponse(icalstream, mimetype='text/calendar')
    response['Filename'] = 'events.ics'  # IE needs this
    response['Content-Disposition'] = 'attachment; filename=events.ics'
    return response
