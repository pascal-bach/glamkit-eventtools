from django.db import models
from eventtools.models import EventModel, OccurrenceModel, GeneratorModel
from django.conf import settings

class ExampleVenue(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

class ExampleEvent(EventModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, default="the-slug")
    venue = models.ForeignKey(ExampleVenue, null=True, blank=True)            
    difference_from_parent = models.CharField(max_length=250, blank=True, null=True)
    
    def __unicode__(self):
        if self.difference_from_parent and self.parent:
            return u"%s (%s)" % (self.name, self.difference_from_parent)
        return self.name
        
    class EventMeta:
        fields_to_inherit = ['name', 'slug', 'venue']
        
    
class ExampleOccurrence(OccurrenceModel):
    event = models.ForeignKey(ExampleEvent, related_name="occurrences")
    status = models.CharField(max_length=20, blank=True, null=True)
    
# with generator

class ExampleGEvent(EventModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, default="the-slug")
    venue = models.ForeignKey(ExampleVenue, null=True, blank=True)            

    def __unicode__(self):
        return self.name
        
    class EventMeta:
        fields_to_inherit = ['name', 'slug', 'venue']

class ExampleGenerator(GeneratorModel):
    event = models.ForeignKey(ExampleGEvent, related_name="generators")    
    
class ExampleGOccurrence(OccurrenceModel):
    generator = models.ForeignKey(ExampleGenerator, related_name="occurrences", blank=True, null=True)  
    event = models.ForeignKey(ExampleGEvent, related_name="occurrences")
    status = models.CharField(max_length=20, blank=True, null=True)

