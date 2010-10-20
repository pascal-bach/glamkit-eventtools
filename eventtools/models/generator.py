# −*− coding: UTF−8 −*−
from dateutil import rrule
from django.db import models
from rule import Rule
from nosj.fields import JSONField
from django.utils.translation import ugettext, ugettext_lazy as _
from eventtools.utils import datetimeify
from datetime import date, time, datetime, timedelta
from django.db import transaction
from eventtools.conf import settings
from django.db.models.base import ModelBase

class GeneratorModel(models.Model):
    """
    A GeneratorModel generates Occurrences according to given rules. For example:
        • One occurrence, Tuesday 18th August 2010, 1500-1600
        • Every Tuesday, starting Tuesday 18th August 2012.
        • Every weekday except during Training Week, starting 17th August 2008, finishing 30th October 2008.
        • etc.

    Occurrences which repeat need a repetition Rule (see rules.py for details).

    The event_start/event_end datetime fields describe the first occurrence. The repetition rule is then applied, to
    generate all occurrences that start before the `repeat_until` datetime limit.

    Generators without repeat_until limits potentially repeat infinitely. In this case, we generate occurrences until a
    set timedelta in the future. This timedelta is set in the setting 'DEFAULT_GENERATOR_LIMIT'.    
    """

    #define a field called 'event' in the subclass
    event_start = models.DateTimeField(db_index=True)
    event_end = models.DateTimeField(blank=True, db_index=True)
    rule = models.ForeignKey(Rule, verbose_name=_("repetition rule"), null = True, blank = True, help_text=_("Select '----' for a one-off event."))
    repeat_until = models.DateTimeField(null = True, blank = True, help_text=_("These start dates are ignored for one-off events."))
    exceptions = JSONField(null=True, blank=True, help_text="These dates are skipped by the generator.", default={})
    
    class Meta:
        abstract = True

    def __unicode__(self):
        return "Generator %s" % self.id

    def clean(self):
        if self.event_start > self.event_end:
            raise ValidationError('start must be earlier than end')
        if self.repeat_until is not None and self.repeat_until < self.event_end:
            raise ValidationError('repeat_until must not be earlier than start')
        if self.repeat_until is not None and self.rule is None:
            raise ValidationError('repeat_until has no effect without a repetition rule')
        super(GeneratorModel, self).clean()

    def save(self, *args, **kwargs):
        generate = kwargs.pop('generate', True)
        
        if self.event_end is None:
            self.event_end = self.event_start

        self.event_start = datetimeify(self.event_start, clamp="min")
        self.event_end = datetimeify(self.event_end, clamp="max")
        if self.repeat_until is not None:
            self.repeat_until = datetimeify(self.repeat_until, clamp="max")

        if self.event_end.time == time.min:
            self.event_end.time == time.max

        if self.event_start > self.event_end:
            raise AttributeError('start must be earlier than end')

        if self.repeat_until is not None and self.repeat_until < self.event_start:
            raise AttributeError('repeat_until must not be earlier than start')
        
        if self.repeat_until is not None and self.rule is None:
            raise AttributeError('repeat_until has no effect without a repetition rule')

        super(GeneratorModel, self).save(*args, **kwargs)
        if generate:
            self.generate() #need to do this after save, so we have ids.
    
    @property
    def all_day(self):
        return self.event_start.time() == time.min and self.event_end.time() == time.max
    
    @property
    def event_duration(self):
        return self.event_end-self.event_start
    
    @classmethod
    def Occurrence(cls):
        return cls.occurrences.related.model

    def create_occurrence(self, start, end=None, honour_exceptions=False):
        """
        Occurrences are only generated if all of the following are true:
            * the start time isn't in the list of exceptions (unless we're 'force'-creating)
            * the occurrence hasn't already been saved by this generator (regardless of the event it is now assigned to)
            * the occurrence doesn't already exist for this event (regardless of the generator it came from)
        """
        if not honour_exceptions or (honour_exceptions and not self.is_exception(start)):
            if self.occurrences.filter(start=start, end=end).count() == 0:
                if self.Occurrence().objects.filter(event=self.event, start=start, end=end).count() == 0:
                    occ = self.occurrences.create(event=self.event, start=start, end=end) #generator = self
                    return occ

    @transaction.commit_on_success()
    def generate(self):
        """
        generate my occurrences
        """
                
        if self.rule is None: #the only occurrence in the village
            self.create_occurrence(start=self.event_start, end=self.event_end, honour_exceptions=True)
            return

        rule = self.rule.get_rrule(dtstart=self.event_start)
            
        date_iter = iter(rule)
        event_duration = self.event_duration
        drop_dead_date = self.repeat_until or datetime.now() + settings.DEFAULT_GENERATOR_LIMIT
        
        while True:
            o_start = date_iter.next()
            if o_start > drop_dead_date:
                break
            o_end = o_start + self.event_duration
            self.create_occurrence(start=o_start, end=o_end, honour_exceptions=True)

    # def robot_description(self):
    #     if self.rule:
    #         if self.repeat_until:
    #             return "%s, repeating %s until %s" % (
    #                 self.timespan.robot_description(),
    #                 self.rule,
    #                 pprint_date_span(self.repeat_until, self.repeat_until)
    #             )
    #         else:
    #             return "%s, repeating %s" % (
    #                 self.timespan.robot_description(),
    #                 self.rule,
    #             )
    #     else:
    #         return self.timespan.robot_description()
    
    def is_exception(self, dt):
        if self.exceptions is None:
            self.reset_exceptions()
        return self.exceptions.has_key(dt.isoformat())
    
    def add_exception(self, dt):
        if self.exceptions is None:
            self.reset_exceptions()
        
        self.exceptions[dt.isoformat()] = True
        self.save(generate=False)       

    def remove_exception(self, dt):
        if self.exceptions is None:
            self.reset_exceptions()
        if self.is_exception(dt):
            del self.exceptions[dt.isoformat()]
            self.save(generate=False)

    def reset_exceptions(self):
        self.exceptions = {}
        self.save(generate=False)

    def reload(self):
        """
        Call with x = x.reload() - it doesn't change itself
        """
        return type(self)._default_manager.get(pk=self.pk)

