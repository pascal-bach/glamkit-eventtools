import datetime
import os
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import get_model
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from eventtools.tests.eventtools_testapp.models import *
from datetime import date, datetime, time, timedelta
from _inject_app import TestCaseWithApp as TestCase
from eventtools.models import Rule

class TestQueries(TestCase):
    
    def test_between_queries(self):
        weekly = Rule.objects.create(name="weekly", frequency="WEEKLY")
        
        start_date = date(2010, 03, 1) #it's a monday
        end_date = start_date+timedelta(28) # it's a monday (the 29th)
        
        gardeners_question_time = BroadcastEvent.objects.create(presenter = "Jim Appleface", studio=2)
        gardeners_answer_time = BroadcastEvent.objects.create(presenter = "Jim Appleface", studio=1)
        
        #questions on mondays and tuesdays
        gardeners_question_time.create_generator(
            first_start_date=start_date,
            first_start_time=time(10,00),
            first_end_time=time(12,00),
            rule=weekly,
        )
        gardeners_question_time.create_generator(
            first_start_date=start_date+timedelta(1),
            first_start_time=time(10,00),
            first_end_time=time(12,00),
            rule=weekly,
        )

        #answers on thursdays and fridays
        gardeners_answer_time.create_generator(
            first_start_date=start_date+timedelta(3),
            first_start_time=time(10,00),
            first_end_time=time(12,00),
            rule=weekly,
        )
        gardeners_answer_time.create_generator(
            first_start_date=start_date-timedelta(4),
            first_start_time=time(10,00),
            first_end_time=time(12,00),
            rule=weekly,
        )

        
        all_occurrences = BroadcastEvent.objects.occurrences_between(start_date, end_date)
        self.assertEqual(len(all_occurrences), 17)
        
        studio1_occurrences = BroadcastEvent.objects.filter(studio=1).occurrences_between(start_date, end_date)
        self.assertEqual(len(studio1_occurrences), 8)
        
        answer_occurrences = gardeners_answer_time.generators.occurrences_between(start_date, end_date)
        self.assertEqual(studio1_occurrences, answer_occurrences)

        #Now check we get the right events back, in the order of first forthcoming occurrence
        all_events_from_monday = BroadcastEvent.objects.between(start_date, end_date)
        self.assertEqual(list(all_events_from_monday), [gardeners_question_time, gardeners_answer_time])
        
        all_events_from_wednesday = BroadcastEvent.objects.between(start_date+timedelta(2), end_date)
        self.assertEqual(list(all_events_from_wednesday), [gardeners_answer_time, gardeners_question_time])
        
        studio1_events = BroadcastEvent.objects.filter(studio=1).between(start_date+timedelta(2), end_date)
        self.assertEqual(list(studio1_events), [gardeners_answer_time, ])
        
        

    def test_between_ranges(self):
        
        weekly = Rule.objects.create(name="weekly", frequency="WEEKLY")
        
        start_date = date(2010, 03, 1) #it's a monday
        end_date = start_date+timedelta(28) # it's a monday (the 29th)
        
        world_cup_match = BroadcastEvent.objects.create(presenter = "Jimmy McNarrator", studio=1)  
        gardeners_question_time = BroadcastEvent.objects.create(presenter = "Jim Appleface", studio=2)
        
        #starting before, ending within
        world_cup_match.create_generator(
            first_start_date=start_date-timedelta(7),
            first_start_time=time(10,00),
            first_end_time=time(12,00),
            rule=weekly,
            repeat_until=start_date+timedelta(7),
        )
        
        self.assertEqual(len(BroadcastEventOccurrenceGenerator.objects.occurrences_between(start_date, end_date)), 2)
        
        #starting within, ending after
        gardeners_question_time.create_generator(
            first_start_date=start_date+timedelta(7),
            first_start_time=time(10,00),
            first_end_time=time(12,00),
            rule=weekly,
            repeat_until=end_date+timedelta(7),
        )
        
        self.assertEqual(len(BroadcastEventOccurrenceGenerator.objects.occurrences_between(start_date, end_date)), 6)
        self.assertEqual(len(gardeners_question_time.generators.occurrences_between(start_date, end_date)), 4)
        
        #Now continue with the combinations of overlaps. We'll remove all generators inbetween.
        
        def _make_combo(first_start_date, repeat_until=None, rule=None):
            return gardeners_question_time.create_generator(
                first_start_date=first_start_date,
                first_start_time=time(10,00),
                first_end_time=time(12,00),
                rule=rule,
                repeat_until=repeat_until,
            )
        
        def _test_combo(result, first_start_date, repeat_until=None, rule=weekly):
            gardeners_question_time.generators.all().delete()
            _make_combo(first_start_date, repeat_until, rule)
            self.assertEqual(len(gardeners_question_time.generators.occurrences_between(start_date, end_date)), result)


        #both within
        _test_combo(
            first_start_date = start_date+timedelta(7),
            repeat_until= end_date-timedelta(7),
            result=3
        )

        #start before, end after
        _test_combo(
            first_start_date=start_date-timedelta(7),
            repeat_until=end_date+timedelta(7),
            result=5
        )

        #start before, end before
        _test_combo(
            first_start_date=start_date-timedelta(14),
            repeat_until=start_date-timedelta(7),
            result=0
        )

        #start after, end after
        _test_combo(
            first_start_date=end_date+timedelta(7),
            repeat_until=end_date+timedelta(14),
            result=0
        )

        #start before, end on start date
        _test_combo(
            first_start_date=start_date-timedelta(7),
            repeat_until=start_date,
            result=1
        )

        #start on end date, end after
        _test_combo(
            first_start_date=end_date,
            repeat_until=end_date + timedelta(7),
            result=1
        )
 
         #start on start date, end on end date
        _test_combo(
            first_start_date=start_date,
            repeat_until=end_date,
            result=5
        )
        
        #start before start date, no end
        _test_combo(
            first_start_date=start_date - timedelta(7),
            result=5
        )

        #start on start date, no end
        _test_combo(
            first_start_date=start_date,
            result=5
        )

        #start within, no end
        _test_combo(
            first_start_date=start_date + timedelta(7),
            result=4
        )
        #start on end date, no end
        _test_combo(
            first_start_date=end_date,
            result=1
        )

        #start after end date, no end
        _test_combo(
            first_start_date=end_date + timedelta(7),
            result=0
        )

        #start before, no repetition
        _test_combo(
            first_start_date=start_date - timedelta(7),
            rule=None,
            result=0
        )

        #start on start date, no repetition
        _test_combo(
            first_start_date=start_date,
            rule=None,
            result=1
        )

        #start within, no repetition
        _test_combo(
            first_start_date=start_date + timedelta(7),
            rule=None,
            result=1
        )

        #start on end date, no repetition
        _test_combo(
            first_start_date=end_date,
            rule=None,
            result=1
        )

        #start after end date, no repetition
        _test_combo(
            first_start_date=end_date + timedelta(7),
            rule=None,
            result=0
        )
    
    def test_multiday_events(self):
        """
        Test that if an event spans several days we can run queries on an interior range that
        excludes that event (should be making several 1-day events)
        """

        summercamp = CampEvent.objects.create(name = "Beach Camp!!", tent_required=True)
        
        start_date = date(2010, 11, 24) #it's a friday
        end_date = date(2010, 11, 27) #it's a monday

        summercamp.create_generator(
            first_start_date=start_date,
            first_end_date=end_date
        )
        
        summercamp.generators.occurrences_between(start_date, end_date)
        
    def test_date_only_events(self):
        pass
        """
        Test that:
        * can be saved
        * generated occurrences also use dates only, have date_only == True
        * saved occurrences can have time set (e.g. from unknown -> known)
        * in lists, date_only events appear first
        * in lists, occurrences with time set appear in the right order
        """