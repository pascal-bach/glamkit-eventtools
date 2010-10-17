from django.db import models
from eventtools.models import EventModel, OccurrenceModel
from django.conf import settings

class Venue(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

class Event(EventModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, default="the-slug")
    venue = models.ForeignKey(Venue, null=True, blank=True)            
    difference_from_parent = models.CharField(max_length=250, blank=True, null=True)
    
    def __unicode__(self):
        if self.difference_from_parent and self.parent:
            return "%s (%s)" % (self.name, self.difference_from_parent)
        return self.name
        
    class EventMeta:
        fields_to_inherit = ['name', 'slug', 'venue']
        
class Occurrence(OccurrenceModel):
    event = models.ForeignKey(Event, related_name="occurrences")
    status = models.CharField(max_length=20, blank=True, null=True, choices=settings.OCCURRENCE_STATUS_CHOICES)
    
    # def __unicode__(self):
    #     return "%s (%s)" % (self.event, self.annotation)