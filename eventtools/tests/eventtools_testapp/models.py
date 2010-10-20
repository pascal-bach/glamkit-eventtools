from django.db import models
from eventtools.models import EventModel, OccurrenceModel, GeneratorModel
from django.conf import settings

class TestVenue(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

class TestEvent(EventModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, default="the-slug")
    venue = models.ForeignKey(TestVenue, null=True, blank=True)            
    difference_from_parent = models.CharField(max_length=250, blank=True, null=True)
    
    def __unicode__(self):
        if self.difference_from_parent and self.parent:
            return "%s (%s)" % (self.name, self.difference_from_parent)
        return self.name
        
    class EventMeta:
        fields_to_inherit = ['name', 'slug', 'venue']
        
    
class TestOccurrence(OccurrenceModel):
    event = models.ForeignKey(TestEvent, related_name="occurrences")
    status = models.CharField(max_length=20, blank=True, null=True, choices=settings.OCCURRENCE_STATUS_CHOICES)
    
# with generator

class TestGEvent(EventModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, default="the-slug")
    venue = models.ForeignKey(TestVenue, null=True, blank=True)            

    def __unicode__(self):
        return self.name
        
    class EventMeta:
        fields_to_inherit = ['name', 'slug', 'venue']

class TestGenerator(GeneratorModel):
    event = models.ForeignKey(TestGEvent, related_name="generators")    
    
class TestGOccurrence(OccurrenceModel):
    generator = models.ForeignKey(TestGenerator, related_name="occurrences", blank=True, null=True)  
    event = models.ForeignKey(TestGEvent, related_name="occurrences")
    status = models.CharField(max_length=20, blank=True, null=True, choices=settings.OCCURRENCE_STATUS_CHOICES)

