# -*- coding: utf-8“ -*-
from django.test import TestCase
from eventtools.tests._inject_app import TestCaseWithApp as AppTestCase
from eventtools.tests.eventtools_testapp.models import *
from datetime import date, time, datetime, timedelta
from eventtools.tests._fixture import generator_fixture
from eventtools.utils import datetimeify
from dateutil.relativedelta import relativedelta
from django.core.urlresolvers import reverse
from eventtools.models import Rule
from django.core.exceptions import ValidationError

class TestGenerators(AppTestCase):
    
    def setUp(self):
        super(TestGenerators, self).setUp()
        generator_fixture(self)
    
    def test_generation(self):
        """
        Occurrences can be generated by a Generator. An event can have many Generators.
        A Generator has event, start datetime, end datetime, rule, repeat_until,
        and 'exceptions'.

        (`exceptions` is a JSONfield of start/end datetime pairs that the generator
        skips over if it was about to generate them).
        
        A generator generates occurrences by repeating start/end datetimes according
        to the rule, until repeat_until is about to be exceeded.

        If repeat_until is omitted (and rule is set) then repetitions are created upto
        a preset period into the future. The preset is in settings. The preset period
        is continually updated.
        
        Every time a generator is saved, it does its generating.
        Every time an event is saved, generators with a rule and no repeat_until do their generating.

        A generator will not save occurrences for an event that are the same as occurrences
        already in the database (even if they were created by another generator).
        However, occurrences that differ only in start time or end time ARE generated,

        Occurrences are saved to the database, and have an FK to the generator that
        did so. The FK can be set to None so that an occurrence can be detatched from a generator.
        """

        self.assertTrue(self.endless_generator.occurrences.count() > 52)

        #test re-save event resaves 'boundless' generators, by deleting them first.
        self.endless_generator.occurrences.all().delete()
        self.ae(self.endless_generator.occurrences.count(), 0)
        self.bin_night.save()
        self.assertTrue(self.endless_generator.occurrences.count() > 52)

        #test dupes were not created.
        
        # have we got some weekly occurrences?
        self.ae(self.weekly_generator.occurrences.count(), 5)
        
        daily_starts = [x.start for x in self.endless_generator.occurrences.all()]
        weekly_starts = [x.start for x in self.weekly_generator.occurrences.all()]
        
        for s in weekly_starts:
            self.assertTrue(s not in daily_starts)
        
    def test_all_day(self):
        """
        If the start time of a generator is time.min and the duration is not given, then the generator generates all_day
        occurrences.
        """
        
        self.ae(self.all_day_generator.start, datetime(2010, 1, 4, 0, 0))
        self.assertTrue(not self.all_day_generator._duration)
    
        [self.ae(x.all_day(), True) for x in self.all_day_generator.occurrences.all()]
                
    def test_creation(self):
        """
        Same date/time constraints as occurrence.
        Attitionally, it is not valid to have a repeat_until without a rule.
        """
        e = self.bin_night
        d1 = date(2010,1,1)
        d2 = date(2010,1,2)
        d1min = datetimeify(d1, clamp='min')
        d1max = datetimeify(d1, clamp='max')
        d2min = datetimeify(d2, clamp='min')
        d2max = datetimeify(d2, clamp='max')
        t1 = time(9,00)
        t2 = time(10,00)
        
        dt1 = datetime.combine(d1, t1)
        dt2 = datetime.combine(d2, t2)

        #datetimes
        g = e.generators.create(start=dt1, _duration=60*24+60, rule=self.yearly)
        self.ae(g.start, dt1)
        self.ae(g.end(), dt2)

        g = e.generators.create(start=dt1, rule=self.yearly)
        self.ae(g.start, dt1)
        self.ae(g.end(), dt1)

        g = e.generators.create(start=d1min, rule=self.yearly)
        self.ae(g.start, d1min)
        self.ae(g.end(), d1min)

        # Missing start.
        self.assertRaises(
            Exception,
            e.generators.create, **{'_duration': 60, 'rule': self.yearly}
        )

        # Missing rule.
        self.assertRaises(
            Exception,
            e.generators.create, **{'start':dt1, }    
        )

        # Invalid start value.
        self.assertRaises(
            Exception,
            e.generators.create, **{'start':t1, 'rule': self.yearly}
        )

    def test_clash(self):
        """
        weekly_generator and endless_generator are set up to generate clashing
        occurrences. They shouldn't.
        """
        wo = set(self.weekly_generator.occurrences.all())
        eo = set(self.endless_generator.occurrences.all())
        
        # there should be no intersection of occurrences
        self.assertTrue(wo.isdisjoint(eo))
    
    def _reset_generator_fixture(self):
        """ In this test, changeable_generator initially generates events weekly
        from 27 December 2010 from 8.30-9.30am, until 2 Feb 2011 (before
        changes, the last occurrence is on 31st Jan 2011). """

        self.furniture_collection, created = ExampleEvent.eventobjects.get_or_create(title='Furniture Collection', slug="furniture-collection")
        self.furniture_collection.occurrences.all().delete()
        self.furniture_collection.generators.all().delete()
        self.changeable_generator = self.furniture_collection.generators.create(
            start=datetime(2010, 12, 27, 8, 30),
            _duration=60,
            rule=self.weekly,
            repeat_until=date(2011, 2, 2)
        )

        # assert count
        self.ae(self.changeable_generator.occurrences.count(), 6)
        self.original_generated_occurrences = \
            list(self.changeable_generator.occurrences.all())
        self.original_generated_occurrence_ids = \
                set([x.id for x in self.original_generated_occurrences])

        # assert initial duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in self.original_generated_occurrences]
        # assert initial day of the week
        [self.ae(x.start.weekday(), 0) \
            for x in self.original_generated_occurrences]
        [self.ae(x.end().weekday(), 0) \
            for x in self.original_generated_occurrences]
                
                
    def test_start_changes(self):     
        """
        test the effects of changing event start date/time.
        
        (If start date is changed, we'll end up with 'orphan' occurrences.)
        """
    
        # =================================
        # changing start time later to 0900
        # =================================
        self._reset_generator_fixture()
            
        self.changeable_generator.start = \
            datetime.combine(
                self.changeable_generator.start.date(),
                time(9,00)
            )
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.start.time(), time(9,00)) for x in new_occurrences]
        # assert same duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.start.weekday(), 0) \
            for x in new_occurrences]

        # ===================================
        # changing start time earlier to 0800
        # ===================================
        self._reset_generator_fixture()
            
        self.changeable_generator.start = \
            datetime.combine(
                self.changeable_generator.start.date(),
                time(8,00)
            )
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.start.time(), time(8,00)) for x in new_occurrences]
        # assert same duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.start.weekday(), 0) \
            for x in new_occurrences]

        # =============================================================
        # changing start time nearly 24h earlier to 0900 the day before 
        # =============================================================
        self._reset_generator_fixture()
            
        self.changeable_generator.start = \
            datetime.combine(
                self.changeable_generator.start.date() - timedelta(1),
                time(9,00)
            )
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.start.time(), time(9,00)) for x in new_occurrences]
        # assert same duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.start.weekday(), 6) \
            for x in new_occurrences]
  
        # =============================================================
        # changing start time more than 24h earlier to 0800 the day before 
        # =============================================================
        self._reset_generator_fixture()
            
        self.changeable_generator.start = \
            datetime.combine(
                self.changeable_generator.start.date() - timedelta(1),
                time(8,00)
            )
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.start.time(), time(8,00)) for x in new_occurrences]
        # assert same duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.start.weekday(), 6) \
            for x in new_occurrences]
    
        # =============================================================
        # changing start time more than 48h earlier to 0800 2 days before 
        # =============================================================
        self._reset_generator_fixture()
            
        self.changeable_generator.start = \
            datetime.combine(
                self.changeable_generator.start.date() - timedelta(2),
                time(8,00)
            )
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.start.time(), time(8,00)) for x in new_occurrences]
        # assert same duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.start.weekday(), 5) \
            for x in new_occurrences]

        # =============================================================
        # changing start time nearly 24h later, to 0800 the day after
        # =============================================================
        self._reset_generator_fixture()
            
        self.changeable_generator.start = \
            datetime.combine(
                self.changeable_generator.start.date() + timedelta(1),
                time(8,00)
            )
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        all_ids = set(
            [x.id for x in self.changeable_generator.event.occurrences.all()]
        )
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)

        # assert new times
        [self.ae(x.start.time(), time(8,00)) for x in new_occurrences]
        # assert same duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.start.weekday(), 1) \
            for x in new_occurrences]
  
        # =============================================================
        # changing start time more than 24h later to 0900 the day after 
        # =============================================================
        self._reset_generator_fixture()
            
        self.changeable_generator.start = \
            datetime.combine(
                self.changeable_generator.start.date() + timedelta(1),
                time(9,00)
            )
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        all_ids = set(
            [x.id for x in self.changeable_generator.event.occurrences.all()]
        )
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)

        # assert new times
        [self.ae(x.start.time(), time(9,00)) for x in new_occurrences]
        # assert same duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.start.weekday(), 1) \
            for x in new_occurrences]
    
        # =============================================================
        # changing start time more than 48h later to 0900 2 days after
        # =============================================================
        self._reset_generator_fixture()
            
        self.changeable_generator.start = \
            datetime.combine(
                self.changeable_generator.start.date() + timedelta(2),
                time(9,00)
            )
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        all_ids = set(
            [x.id for x in self.changeable_generator.event.occurrences.all()]
        )

        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.start.time(), time(9,00)) for x in new_occurrences]
        # assert same duration
        [self.ae(x.duration, timedelta(days=0, seconds=3600)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.start.weekday(), 2) \
            for x in new_occurrences]

    def test_duration_changes(self):
        """
        test the effects of changing duration date/time.
        
        (If only end datetime is changed, we'll never end up with 'orphan' 
        occurrences.)
        """
    
        # =================================
        # changing duration later to 1000
        # =================================
        self._reset_generator_fixture()
            
        self.changeable_generator._duration = 90
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.end().time(), time(10,00)) for x in new_occurrences]
        # assert new duration
        [self.ae(x.duration, timedelta(days=0, seconds=5400)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.end().weekday(), 0) \
            for x in new_occurrences]
    
        # ===================================
        # changing duration earlier to 0900
        # ===================================
        self._reset_generator_fixture()
            
        self.changeable_generator._duration = 30
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.end().time(), time(9,00)) for x in new_occurrences]
        # assert new duration
        [self.ae(x.duration, timedelta(days=0, seconds=1800)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.end().weekday(), 0) \
            for x in new_occurrences]
    
        # =============================================================
        # changing duration nearly 24h later to 0900 the day after
        # (start time = 8.30)
        # =============================================================
        self._reset_generator_fixture()
            
        self.changeable_generator._duration = 1470
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.end().time(), time(9,00)) for x in new_occurrences]
        # assert new duration (24.5h)
        [self.ae(x.duration, timedelta(days=1, seconds=1800)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.end().weekday(), 1) \
            for x in new_occurrences]
      
        # =============================================================
        # changing duration more than 24h later to 1000 the day after
        # =============================================================
        self._reset_generator_fixture()
            
        self.changeable_generator._duration = 1530
        self.changeable_generator.save()
        
        new_occurrences = self.changeable_generator.occurrences.all()
        new_ids = set([x.id for x in new_occurrences])
        # assert ids haven't changed
        self.ae(new_ids, self.original_generated_occurrence_ids)
        # assert new times
        [self.ae(x.end().time(), time(10,00)) for x in new_occurrences]
        # assert new duration (25.5h)
        [self.ae(x.duration, timedelta(days=1, seconds=5400)) \
            for x in new_occurrences]
        # assert new day of the week
        [self.ae(x.end().weekday(), 1) \
            for x in new_occurrences]
    
        # updating a generator should update other generators, in case their times clashed.
    def test_clashing_generators(self):
        """
        If two generators clash, and one is changed so that it doesn't clash,
        then the other should create occurrences.
        
        # in the fixture, these two generators are identical
        obj.weekly_generator = obj.bin_night.generators.create(start=datetime(2010,1,8,10,30), event_end=datetime(2010,1,8,11,30), rule=obj.weekly, repeat_until=date(2010,2,5))
        obj.dupe_weekly_generator = obj.bin_night.generators.create(start=datetime(2010,1,8,10,30), event_end=datetime(2010,1,8,11,30), rule=obj.weekly, repeat_until=date(2010,2,5))

        """
        
        weekly_count = self.weekly_generator.occurrences.count()
        dupe_weekly_count = self.dupe_weekly_generator.occurrences.count()
        
        
        self.assertTrue(weekly_count > 0)
        self.assertTrue(dupe_weekly_count == 0)

        #Shift the weekly start forward 30 mins.
        self.weekly_generator.start = datetime(2010,1,8,11,00)
        self.weekly_generator.save()
        #should no longer clash
        self.ae(self.weekly_generator.occurrences.count(), weekly_count)
        self.ae(self.dupe_weekly_generator.occurrences.count(), weekly_count)
        

    def test_regenerate_with_related_items(self):
        event = ExampleEvent.objects.create(title="Curator's Talk", slug="curators-talk-1")
        # is on every week for a year
        weekly = Rule.objects.create(frequency = "WEEKLY")
        generator = event.generators.create(start=datetime(2010,1,1, 9,00), _duration=60, rule=weekly, repeat_until=date(2010,12,31))

        # that means there are 53 occurrences generated
        self.ae(generator.occurrences.count(), 53)
        # and one of them is on a particular date
        ticketed_occurrence = event.occurrences.all().reverse()[0]
        # now I buy a ticket to the occurrence
        ticket = ExampleTicket.objects.create(occurrence=ticketed_occurrence)

        # oh wait, I made a data entry mistake! The talk is on every week only for 6 months
        generator.repeat_until = date(2010, 7, 1)
        generator.save()
        # that means there are 26 occurrences generated
        self.ae(generator.occurrences.count(), 26)

        # since I bought a ticket, the occurrence that has a ticket is now one-off
        self.assertTrue(ticket.occurrence)
        self.ae(event.occurrences.get(id=ticket.occurrence.id).generated_by, None)

        # but there are no other one-off occurrences, meaning 27 occurrences in total
        self.ae(event.occurrences.filter(generated_by__isnull=True).count(), 1)
        self.ae(event.occurrences.count(), 27)

    def test_delete_with_related_items(self):
        event = ExampleEvent.objects.create(title="Curator's Talk", slug="curators-talk-2")
        # is on every week for a year
        generator = event.generators.create(start=datetime(2010,1,1, 9,00), _duration=60, rule=self.weekly_generator.rule, repeat_until=date(2010,12,31))

        # that means there are 53 occurrences generated
        self.ae(generator.occurrences.count(), 53)
        # and one of them is on a particular date
        ticketed_occurrence = event.occurrences.all().reverse()[0]
        # now I buy a ticket to the occurrence
        ticket = ExampleTicket.objects.create(occurrence=ticketed_occurrence)

        # oh wait, I made a data entry mistake! Deleting the generator.
        generator.delete()

        # since I bought a ticket, the occurrence that has a ticket is now one-off.
        ticket = ExampleTicket.objects.get(pk=ticket.pk)
        self.assertTrue(ticket.occurrence)
        self.ae(ticket.occurrence.generated_by, None)

        # but there are no other one-off occurrences, meaning 1 occurrence in total
        self.ae(event.occurrences.filter(generated_by__isnull=True).count(), 1)
        self.ae(event.occurrences.count(), 1)

