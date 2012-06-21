# (We thought of calling it Exceptions, but Python has them)

from django.db import models

class ExclusionModel(models.Model):
    """
    Represents the time of an occurrence which is not to be generated for a given event.

    Implementing subclasses should define an 'event' ForeignKey to an EventModel
    subclass. The related_name for the ForeignKey should be 'exclusions'.
    
    event = models.ForeignKey(SomeEvent, related_name="exclusions")
    """
    start = models.DateTimeField(db_index=True)

    class Meta:
        abstract = True
        ordering = ('start',)
        verbose_name = "repeating occurrence exclusion"
        verbose_name_plural = "repeating occurrence exclusions"
        unique_together = ('event', 'start')
        
    def __unicode__(self):
        return "%s starting on %s is excluded" % (self.event, self.start)

    def save(self, *args, **kwargs):
        """
        When an exclusion is saved, any generated occurrences that match should
        be unhooked.
        """
        r = super(ExclusionModel, self).save(*args, **kwargs)
        
        clashing = self.event.occurrences.filter(start = self.start, generated_by__isnull=False)
        for c in clashing:
            c.generated_by = None
            c.save()
        
        return r