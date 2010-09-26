# −*− coding: UTF−8 −*−
from datetime import datetime, date, time
   
def occurrences_to_events(occurrences):
    """ returns a list of events pertaining to these occurrences, maintaining order """
    event_ids = []
    events = []
    for occurrence in occurrences:
        # import pdb; pdb.set_trace()
        if occurrence.unvaried_event.id not in event_ids: #just testing the id saves database lookups (er, maybe)
            event_ids.append(occurrence.unvaried_event.id)
            events.append(occurrence.unvaried_event)
    return events

def occurrences_to_event_qs(occurrences):
    """ returns a qs of events pertaining to these occurrences. Order is lost. """
    if occurrences:
        event_ids = [o.unvaried_event.id for o in occurrences]
        return type(occurrences[0].unvaried_event).objects.filter(id__in=event_ids)
    return None
    
    events = []
    for occurrence in occurrences:
        # import pdb; pdb.set_trace()
        if occurrence.unvaried_event.id not in event_ids: #just testing the id saves database lookups (er, maybe)
            event_ids.append(occurrence.unvaried_event.id)
            events.append(occurrence.unvaried_event)
    return events
