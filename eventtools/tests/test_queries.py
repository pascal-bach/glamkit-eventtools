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
        
        self.assertEqual(len(BroadcastEvent.OccurrenceGenerator.objects.occurrences_between(start_date, end_date)), 2)
        
        #starting within, ending after
        gardeners_question_time.create_generator(
            first_start_date=start_date+timedelta(7),
            first_start_time=time(10,00),
            first_end_time=time(12,00),
            rule=weekly,
            repeat_until=end_date+timedelta(7),
        )
        
        self.assertEqual(len(BroadcastEvent.OccurrenceGenerator.objects.occurrences_between(start_date, end_date)), 6)
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

        Test that date-only eventss can be saved, and when occurrences are queried, just return dates

        """

        summercamp = CampEvent.objects.create(name = "Beach Camp!!", tent_required=True)
        
        start_date = date(2010, 11, 24) #it's a friday
        end_date = date(2010, 11, 27) #it's a monday

        before_date = start_date - timedelta(1)
        after_date = end_date + timedelta(1)
        
        inside_date_1 = start_date + timedelta(1) 
        inside_date_2 = end_date - timedelta(1) 

        summercamp.create_generator(
            first_start_date=start_date,
            first_end_date=end_date
        )
        
        for occs in [
            summercamp.occurrences_between(start_date, end_date),
            summercamp.occurrences_between(start_date, start_date),
            summercamp.occurrences_between(before_date, after_date),
            summercamp.occurrences_between(before_date, start_date),
            summercamp.occurrences_between(before_date, inside_date_1),
            summercamp.occurrences_between(start_date, inside_date_1),
        ]:
            self.assertEqual(len(occs), 1)

        for occs in [
            summercamp.occurrences_between(inside_date_1, end_date),
            summercamp.occurrences_between(inside_date_1, inside_date_2),
            summercamp.occurrences_between(inside_date_2, after_date),
        ]:
            self.assertEqual(len(occs), 0)


        this_week = summercamp.occurrences_between(start_date, start_date)
        self.assertEqual(len(this_week), 1)
        self.assertEqual(this_week[0].timespan.duration(), timedelta(3))
        self.assertEqual(this_week[0].timespan.start_date, start_date)
        self.assertEqual(this_week[0].timespan.end_date, end_date)
        self.assertEqual(this_week[0].timespan.start_time, None)
        self.assertEqual(this_week[0].timespan.end_time, None)

        
    def test_multiday_repetition(self):
        """
        Test that repeated multidates can be saved, and when occurrences are queried, just return dates
        """
        
        summercamp = CampEvent.objects.create(name = "Beach Camp!!", tent_required=True)        
        start_date = date(2010, 11, 24) #it's a friday
        end_date = date(2010, 11, 27) #it's a monday
        weekly = Rule.objects.create(name="weekly", frequency="WEEKLY")
        summercamp.create_generator(
            first_start_date=start_date,
            first_end_date=end_date,
            rule=weekly,        
        )
         
        this_week = summercamp.occurrences_between(start_date, start_date)
        
        self.assertEqual(len(this_week), 1)
        self.assertEqual(this_week[0].timespan.duration(), timedelta(3))
        self.assertEqual(this_week[0].timespan.start_date, start_date)
        self.assertEqual(this_week[0].timespan.end_date, end_date)
        self.assertEqual(this_week[0].timespan.start_time, None)
        self.assertEqual(this_week[0].timespan.end_time, None)
        
        next_week = summercamp.occurrences_between(start_date+timedelta(7), start_date+timedelta(7))
        self.assertEqual(len(next_week), 1)
        self.assertEqual(next_week[0].timespan.duration(), timedelta(3))
        self.assertEqual(next_week[0].timespan.start_date, start_date+timedelta(7))
        self.assertEqual(next_week[0].timespan.end_date, end_date+timedelta(7))
        self.assertEqual(next_week[0].timespan.start_time, None)
        self.assertEqual(next_week[0].timespan.end_time, None)
        
    def test_date_only_queries(self):
        """
        Test that:
        * can be saved, and when queried, just return dates
        * can be varied to other things that are just dates
        * generated occurrences also use dates only, have dates_only == True
        * in lists, date_only events appear first
        * in lists, occurrences with times appear after those without
        * saved occurrences can have time added later (e.g. from unknown -> known)
        """
        busy_day = date(2010, 11, 24)
    
        weekly = Rule.objects.create(name="weekly", frequency="WEEKLY")
        weeklycamp = CampEvent.objects.create(name = "Weekly Camp!!", tent_required=False)        
        weeklycamp.create_generator(
            first_start_date=busy_day,
            rule=weekly,
        )
        # get from db
        weeklycamp = CampEvent.objects.get(id=weeklycamp.id)
        
        occs = weeklycamp.occurrences_between(busy_day, busy_day+timedelta(1))
        self.assertEqual(len(occs), 1)
        occ = occs[0]
        self.assertEqual(occ.timespan.dates_only, True)
        self.assertEqual(occ.timespan.start, busy_day)
        self.assertEqual(occ.timespan.start_date, busy_day)
        self.assertEqual(occ.timespan.end_date, busy_day)
        self.assertEqual(occ.timespan.start_time, None)
        self.assertEqual(occ.timespan.end_time, None)
        self.assertEqual(occ.timespan.start_datetime, datetime.combine(busy_day, time.min))
        self.assertEqual(occ.timespan.end_datetime, datetime.combine(busy_day, time.max))
        
        
        hourly = Rule.objects.create(name="hourly", frequency="HOURLY")
        hourlytour = CampEvent.objects.create(name = "Not really a camp!!", tent_required=False)
        hourlytour.create_generator(
            first_start_date=busy_day,
            first_start_time=time(10,00),
            rule=hourly,
        )
        
        occs = CampEvent.objects.occurrences_between(busy_day, busy_day)
        
        self.assertEqual(len(occs), 15) # every hour from 10am to 11pm, plus the Weekly event.
        self.assertEqual(occs[0].timespan.start_date, busy_day)
        self.assertEqual(occs[0].timespan.end_date, busy_day)
        self.assertEqual(occs[0].timespan.start_time, None)
        self.assertEqual(occs[0].timespan.end_time, None)
        self.assertEqual(occs[0].event, weeklycamp) # events without a time come first

        self.assertEqual(occs[1].timespan.start_date, busy_day)
        self.assertEqual(occs[1].timespan.end_date, busy_day)
        self.assertEqual(occs[1].timespan.start_time, time(10,00))
        self.assertEqual(occs[1].timespan.end_time, None) #if end time is omitted, use None
        self.assertEqual(occs[1].event, hourlytour) # events without a time come first
        
        #let's say we know the time for next't week's camp
        
        next_week = busy_day + timedelta(7)
        nwcamp = weeklycamp.occurrences_between(next_week, next_week)[0]
        
        nwcamp.varied_start_time = time(10,30)
        nwcamp.save()
        
        camps = weeklycamp.occurrences_between(busy_day, next_week)
        
        self.assertEqual(unicode(camps[0].timespan), "24 November 2010")
        self.assertEqual(unicode(camps[1].timespan), "1 December 2010, 10:30am")
            
    def test_weird_cases(self):        
        """
        so what happens when you want an event with no time to repeat hourly??
        It doesn't really matter since it's such an edge case, but it turns out 24 Occurrences are generated, each with no time!
        """
        
        strange_day = date(2010, 11, 24)
        hourly = Rule.objects.create(name="hourly", frequency="HOURLY")
        hourlycamp = CampEvent.objects.create(name = "Hourly Camp!!", tent_required=False)
        hourlycamp.create_generator(
            first_start_date=strange_day,
            rule=hourly,
        )
        
        occs = hourlycamp.occurrences_between(strange_day, strange_day)
        
        self.assertEqual(len(occs), 24)
        self.assertEqual(occs[0], occs[23])
        
            
