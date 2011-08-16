from django.db import models
from eventtools.models import EventModel, OccurrenceModel, GeneratorModel, ExclusionModel
from django.conf import settings

class ExampleVenue(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

class ExampleEvent(EventModel):
    venue = models.ForeignKey(ExampleVenue, null=True, blank=True)            
    difference_from_parent = models.CharField(max_length=250, blank=True, null=True)
    
    def __unicode__(self):
        if self.difference_from_parent and self.parent:
            return u"%s (%s)" % (self.title, self.difference_from_parent)
        return self.title
        
    class EventMeta:
        fields_to_inherit = ['title', 'slug', 'venue']
        
class ExampleGenerator(GeneratorModel):
    event = models.ForeignKey(ExampleEvent, related_name="generators")    
    
class ExampleOccurrence(OccurrenceModel):
    generated_by = models.ForeignKey(ExampleGenerator, related_name="occurrences", blank=True, null=True)  
    event = models.ForeignKey(ExampleEvent, related_name="occurrences")
    status = models.CharField(max_length=20, blank=True, null=True)

class ExampleExclusion(ExclusionModel):
    event = models.ForeignKey(ExampleEvent, related_name="exclusions")