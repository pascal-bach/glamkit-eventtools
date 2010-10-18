from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from eventtools.conf import settings
from eventtools.utils.pprint_timespan import humanized_date_range
from dateutil.relativedelta import relativedelta
from django.utils.safestring import mark_safe

def occurrence(request, occurrence_id, qs, event_slug=None):
    if event_slug:
        qs = qs.filter(event__slug=event_slug)
    occurrence = get_object_or_404(qs, id=occurrence_id)
    
    return render_to_response('eventtools/occurrence.html', {'occurrence': occurrence}, context_instance=RequestContext(request))
    
def event(request, event_slug, qs):
    event = get_object_or_404(qs, slug=event_slug)
    event_descendants = event.get_descendants(include_self=True)
    occurrence_pool = event_descendants.occurrences()
    
    paginator = Paginator(occurrence_pool, settings.OCCURRENCES_PER_PAGE)

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

    return render_to_response('eventtools/occurrence_list.html', {
        'event': event,
        'event_children': event_descendants,
        'occurrence_pool': occurrence_pool,
        'occurrence_page': pageinfo.object_list,
        'pageinfo': pageinfo,
    }, context_instance=RequestContext(request))
    
def occurrence_list(request, qs):
    
    occurrence_pool, date_bounds = qs.from_GET(request.GET)
    
    if date_bounds[0] is not None and date_bounds[1] is not None:
        # we're doing a date-bounded view, and the pool in tiny.
        date_delta = relativedelta(date_bounds[1]+relativedelta(days=1), date_bounds[0])
        
        earlier = (date_bounds[0] - date_delta, date_bounds[1] - date_delta)
        later = (date_bounds[0] + date_delta, date_bounds[1] + date_delta) 
                
        pageinfo = {
            'date_span': mark_safe(humanized_date_range(*date_bounds, imply_year=False, space="&nbsp;", range_str="&ndash;")),
            'previous_date_span': {
                'start': earlier[0].date().isoformat(),
                'end': earlier[1].date().isoformat(),
            },
            'next_date_span': {
                'start': later[0].date().isoformat(),
                'end': later[1].date().isoformat(),
            },
            'date_delta': date_delta.days
        }

        return render_to_response('eventtools/occurrence_datespan.html',{
            'date_bounds': date_bounds,
            'occurrence_pool': occurrence_pool,
            'occurrence_page': occurrence_pool,
            'pageinfo': pageinfo,
        }, context_instance=RequestContext(request))

    else:
        # we're paging through all events in the pool, OCCURRENCES_PER_PAGE at a time.
        paginator = Paginator(occurrence_pool, settings.OCCURRENCES_PER_PAGE)

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
                
        return render_to_response('eventtools/occurrence_list.html',{
            'occurrence_pool': occurrence_pool,
            'occurrence_page': pageinfo.object_list,
            'pageinfo': pageinfo,
        }, context_instance=RequestContext(request))
