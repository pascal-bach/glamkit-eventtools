# −*− coding: UTF−8 −*−
from dateutil import rrule
from django.db.models.base import ModelBase
from django.core.exceptions import ValidationError
from eventtools.utils import OccurrenceReplacer, datetimeify
from eventtools.smartdatetimespan import SmartDateTimeSpan
import datetime
from django.template.defaultfilters import date as date_filter
from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from rules import Rule
import string
from eventtools.pprint_datetime_span import pprint_date_span
from eventtools.deprecated import deprecated


"""
An OccurrenceGenerator defines the rules for generating a series of events. For example:
    • One occurrence, Tuesday 18th August 2010, 1500-1600
    • Every Tuesday, starting Tuesday 18th August
    • Every day except during Training Week, starting 17th August, finishing 30th October.
    • etc.

Occurrences which repeat need a repetition Rule (see rules.py for details).

The first_start/end_date/time fields describe the first occurrence. The repetition rule is then applied, to generate all occurrences that start before the `repeat_until` datetime.

Occurrences are NOT normally stored in the database, because there is a potentially infinite number of them, and besides, they can be generated quite quickly. Instead, only the Occurrences that have been edited are stored.

You might want to edit an occurrence if it's an exception to the 'norm'. For example:
    • It has a different start/end date
    • It has a different start/end time
    • It is cancelled
    • It has a more complex variation. This a foreign key to an EventVariation model.

See occurrences.py for details.
"""

class OccurrenceGeneratorManager(models.Manager):
    
    def occurrences_between(self, start, end, hide_hidden=True):
        """
        Returns all Occurrences with a start_date/time between two datetimes, sorted.
        
        This function is placed here because OccurrenceGenerators know the name of the Occurrence model, not currently vice-versa.
        However, we really want to hide this model, so lets make a convenience method in EventBaseManager.
        
        Get all OccurrenceGenerators that have the potential to produce occurrences between these dates.
        Run 'em all, and grab the ones that are in range.
        
        TODO - make this a queryset function too!
        """
        
        start = datetimeify(start, clamp="start")
        end = datetimeify(end, clamp='end')
        
        # relevant generators have
        # the first_start_date before the requested end date AND
        # the end date is NULL or after the requested start date
        potential_occurrence_generators = self.filter(first_start_date__lte=end) & (self.filter(repeat_until__isnull=True) | self.filter(repeat_until__gte=start))
        
        occurrences = []
        for generator in potential_occurrence_generators:
            occurrences += generator.get_occurrences(start, end, hide_hidden)
        
        #In case you are pondering returning a queryset, remember that potentially occurrences are not in the database, so no such QS exists.
        
        return sorted(occurrences)

class OccurrenceGeneratorBase(models.Model):
    """
    Defines a repetition sequence for an event, and generates the occurrences.
    
    2010/09/23 added a date-only mode, which generates occurrences with a date but not a time.
    """
    
    objects = OccurrenceGeneratorManager()
    # Injected by EventModelBase:
    # event = models.ForeignKey(somekindofEvent)
    
    first_start_date = models.DateField(_('start date of the first occurrence'))
    first_start_time = models.TimeField(_('start time of the first occurrence'), null=True, blank=True)
    first_end_date = models.DateField(_('end date of the first occurrence'), null = True, blank = True, help_text=_("Only use for an event that starts once and lasts for several days (like a summer camp)."))
    first_end_time = models.TimeField(_('end time of the first occurrence'), null=True, blank=True)

    rule = models.ForeignKey(Rule, verbose_name=_("repetition rule"), null = True, blank = True, help_text=_("Select '----' for a one-off event."))
    repeat_until = models.DateTimeField(null = True, blank = True, help_text=_("This date is ignored for one-off events."))
    _date_description = models.CharField(_("Description of occurrences"), blank=True, max_length=255, help_text=_("e.g. \"Every Tuesday in March 2010\". If this is ommitted, an automatic description will be attempted."))
    
    class Meta:
        ordering = ('first_start_date', 'first_start_time')
        abstract = True
        verbose_name = _('occurrence generator')
        verbose_name_plural = _('occurrence generators')
    
    def __unicode__(self):
        return self.date_description()
    
    def clean(self):
        """ check that the end datetime must be after start date, and that end time is not supplied without a start time. """
        try:
            self.timespan
        except AttributeError as e:
            raise ValidationError(e)            

    # TODO check for boolean tests of time, and change to is not None

    def save(self, *args, **kwargs):
        # if the occurrence generator changes, we must not break the link with persisted occurrences
        if self.id: # must already exist
            for occ in self.occurrences.all(): # only persisted occurrences of course
                occ.unvaried_start_date = self.first_start_date
                occ.unvaried_start_time = self.first_start_time
                occ.unvaried_end_date = self.first_end_date
                occ.unvaried_end_time = self.first_end_time
                occ.save()
        super(OccurrenceGeneratorBase, self).save(*args, **kwargs)
    
    
    @property
    def timespan(self):
        return SmartDateTimeSpan(self.first_start_date, self.first_start_time, self.first_end_date, self.first_end_time)
    
    def date_description(self):
        return self._date_description or self.robot_description()
        
    def robot_description(self):
        if self.rule:
            if self.repeat_until:
                return "%s repeating %s until %s" % (
                    self.timespan.robot_description(),
                    self.rule,
                    pprint_date_span(self.repeat_until, self.repeat_until)
                )
            else:
                return "%s repeating %s" % (
                    self.timespan.robot_description(),
                    self.rule,
                )
        else:
            return self.timespan.robot_description()
        
    def _occurrence_model(self):
        return models.get_model(self._meta.app_label, self._occurrence_model_name)
    OccurrenceModel = property(_occurrence_model)

    def _create_occurrence(self, unvaried_timespan, varied_timespan=None):
        occ = self.OccurrenceModel(generator=self, unvaried_timespan=unvaried_timespan, varied_timespan=varied_timespan )
        return occ
    
    #check
    def _get_occurrence_list(self, start, end):
        """
        generates a list of *unexceptional* Occurrences for this event between two datetimes, start and end.
        """
        
        event_duration = self.timespan.duration() #a timedelta
        if self.rule is not None:
            occurrences = []
            if self.repeat_until and self.repeat_until < end:
                end = self.repeat_until
            rule = self.get_rrule_object()
            o_starts = rule.between(start, end, inc=True) #event_duration was subtracted from start!?!
            for o_start in o_starts:
                o_end = o_start + event_duration
                if self.timespan.dates_only:
                    
                    yield self._create_occurrence(unvaried_timespan = SmartDateTimeSpan(sd=o_start.date(), ed=o_end.date()))
                else:
                    yield self._create_occurrence(unvaried_timespan = SmartDateTimeSpan(sdt=o_start, edt=o_end))
        else:
            # singleton event. check if event is in the period
            if self.timespan.start_datetime >= start and self.timespan.start_datetime < end and self.timespan.end_datetime >= start:
                if self.timespan.dates_only:
                    yield self._create_occurrence(unvaried_timespan = SmartDateTimeSpan(sd=self.timespan.start_date, ed=self.timespan.end_date))                    
                else:
                    yield self._create_occurrence(unvaried_timespan = SmartDateTimeSpan(sdt=self.timespan.start, edt=self.timespan.end))
            else:
                return
    
    #check
    def _occurrences_after_generator(self, after=None):
        """
        a generator that produces unexceptional occurrences after the
        datetime ``after``. For ever, if necessary.
        """
        
        if after is None:
            after = datetime.datetime.now()
        rule = self.get_rrule_object()
        if rule is None:
            if self.end > after:
                yield self._create_occurrence(unvaried_timespan = self.timespan)
            return
        date_iter = iter(rule)
        event_duration = self.timespan.duration()
        while True:
            o_start = date_iter.next()
            if o_start > self.repeat_until:
                raise StopIteration
            o_end = o_start + event_duration
            if o_end > after:
                yield self._create_occurrence(unvaried_timespan = SmartDateTimeSpan(sdt=o_start, edt=o_end))
    
    #check
    def get_occurrences(self, start, end, hide_hidden=True):
        """
        returns a list of occurrences between the datetimes ``start`` and ``end``.
        Includes all of the exceptional Occurrences.
        """
        
        start = datetimeify(start)
        end = datetimeify(end)
        
        exceptional_occurrences = self.occurrences.all()
        occ_replacer = OccurrenceReplacer(exceptional_occurrences)
        occurrences = self._get_occurrence_list(start, end)
        for occ in occurrences:
            # replace occurrences with their exceptional counterparts
            if occ_replacer.has_occurrence(occ):
                p_occ = occ_replacer.get_occurrence(occ)
                # ...but only if they're not hidden and you want to see them
                if not (hide_hidden and p_occ.hide_from_lists):
                    # ...but only if they are within this period
                    if p_occ.timespan.start >= start and p_occ.timespan.start < end and p_occ.timespan.end >= start:
                        yield p_occ
            else:
              yield occ
        # then add exceptional occurrences which originated outside of this period but now
        # fall within it
        additional = occ_replacer.get_additional_occurrences(start, end)
        yield additional.next()
            
    def get_exceptional_occurrences(self, exclude_hidden=True):
        """
        return ONLY a queryset of exceptional Occurrences.
        """
        
        exceptional_occurrences = self.occurrences.all()
        
        if exclude_hidden:
            exceptional_occurrences = exceptional_occurrences.exclude(hide_from_lists=True)
        return exceptional_occurrences
        
    # TODO: move most of this to rules?
    def get_rrule_object(self):
        if self.rule is not None:
            if self.rule.complex_rule:
                try:
                    return rrule.rrulestr(str(self.rule.complex_rule),dtstart=self.timespan.start)
                except:
                    pass
            params = self.rule.get_params()
            frequency = 'rrule.%s' % self.rule.frequency
            simple_rule = rrule.rrule(eval(frequency), dtstart=self.timespan.start, **params)
            rs = rrule.rruleset()
            rs.rrule(simple_rule)
            return rs
    
    def get_first_occurrence(self):
        occ = self.OccurrenceModel(
                generator=self,
                unvaried_start_date=self.first_start_date,
                unvaried_start_time=self.first_start_time,
                unvaried_end_date=self.first_end_date,
                unvaried_end_time=self.first_end_time,
            )
        occ = occ.check_for_exceptions()
        return occ
    
    def occurrences_after(self, after=None):
        """
        returns a generator that produces occurrences after the datetime
        ``after``.  Includes all of the exceptional Occurrences.
        
        TODO: this doesn't bring in occurrences that were originally outside this date range, but now fall within it (or vice versa).
        """
        occ_replacer = OccurrenceReplacer(self.occurrence_set.all())
        generator = self._occurrences_after_generator(after)
        while True:
            next = generator.next()
            yield occ_replacer.get_occurrence(next)
    
    ### DEPRECATIONS

    @property
    @deprecated
    def start(self):
        return self.timespan.start

    @property
    @deprecated
    def end(self):
        return self.timespan.end


    @property
    @deprecated
    def end_recurring_period(self):
        return self.repeat_until
    
    @property
    @deprecated
    def get_one_occurrence(self):
        return get_first_occurrence
    
    def get_occurrence(self, date):
        import warning
        warnings.warn("get_occurrence(d) is deprecated. Use objects.occurrences_between(d,d) instead.", DeprecationWarning, stacklevel = 2)
        
        rule = self.get_rrule_object()
        if rule:
            next_occurrence = rule.after(date, inc=True)
        else:
            next_occurrence = self.start
        if next_occurrence == date:
            try:
                return self.OccurrenceModel.objects.get(generator__event = self, unvaried_start_date = date)
            except self.OccurrenceModel.DoesNotExist:
                return self._create_occurrence(unvaried_timespan = SmartDateTimeSpan(sdt=next_occurrence))
    
    @deprecated
    def get_changed_occurrences(self):
        return self.get_exceptional_occurrences()
        
    @deprecated
    def check_for_exceptions(self, occ):
        """
        Pass in an occurrence, pass out the occurrence, or an exceptional occurrence, if one exists in the db.
        """
        return occ.check_for_exceptions()
    
