from django.db import models
from eventtools.models import EventModel, OccurrenceModel, GeneratorModel, ExclusionModel
from django.conf import settings

class ExampleEvent(EventModel):
    difference_from_parent = models.CharField(max_length=250, blank=True, null=True)
    
    def __unicode__(self):
        if self.difference_from_parent and self.parent:
            return u"%s (%s)" % (self.title, self.difference_from_parent)
        return self.title
        
    class EventMeta:
        fields_to_inherit = ['title',]
        
class ExampleGenerator(GeneratorModel):
    event = models.ForeignKey(ExampleEvent, related_name="generators")    
    
class ExampleOccurrence(OccurrenceModel):
    generated_by = models.ForeignKey(ExampleGenerator, related_name="occurrences", blank=True, null=True)
    event = models.ForeignKey(ExampleEvent, related_name="occurrences")

class ExampleExclusion(ExclusionModel):
    event = models.ForeignKey(ExampleEvent, related_name="exclusions")

class ExampleTicket(models.Model):
    # used to test that an occurrence is unhooked rather than deleted.
    occurrence = models.ForeignKey(ExampleOccurrence, on_delete=models.PROTECT)