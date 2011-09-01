from django.db import models
from eventtools.utils.pprint_timespan \
    import pprint_datetime_span, pprint_date_span
from django.core.exceptions import ValidationError

class SeasonModelManager(models.Manager):
    def current_on(self, date):
        return self.filter(start__lte=date, end__gte=date)
        
    def forthcoming_on(self, date):
        return self.filter(start__gt=date)
        
    def previous_on(self, date):
        return self.filter(end__lt=date)

class SeasonModel(models.Model):
    """
    Describes an entity which takes place between start and end dates. For
    example, a festival or exhibition.
    
    The fields are optional - both omitted means 'ongoing'.
    """

    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)
    
    objects = SeasonModelManager()

    class Meta:
        abstract = True
        
    def clean(self):
        if (self.start is not None and self.end is None) or \
            (self.end is not None and self.start is None):
            raise ValidationError('Start and End must both be provided, or blank')

        if self.start > self.end:
            raise ValidationError('Start must be earlier than End')
            
    def season(self):
        """
        Returns a string describing the first and last dates of this event.
        """        
        if self.start and self.end:
            first = self.start
            last = self.end
        
            return pprint_date_span(first, last)
        
        return None
        
    def __unicode__(self):
        return self.season()
