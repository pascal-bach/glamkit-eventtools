import datetime
import os
from django.core.urlresolvers import reverse
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import get_model
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from eventtools.tests.eventtools_testapp.models import *
from eventtools.tests.eventtools_testapp.forms import *
from datetime import date, datetime, time, timedelta
from _inject_app import TestCaseWithApp as TestCase
from eventtools.models import Rule

class TestModelMetaClass(TestCase):

    # def setUp(self):
    #     super(TestModelMetaClass, self).setUp()

    def test_model_metaclass_generation(self):
        """
        Test that when we create a subclass of EventBase, a corresponding subclass of OccurrenceBase is generated automatically
        """
        self.Occ1 = get_model('eventtools_testapp', 'lectureeventoccurrence')
        self.Occ2 = get_model('eventtools_testapp', 'broadcasteventoccurrence')
        self.Occ3 = get_model('eventtools_testapp', 'lessoneventoccurrence')
        self.occs = [self.Occ1, self.Occ2, self.Occ3]
        
        self.Gen1 = get_model('eventtools_testapp', 'lectureeventoccurrencegenerator')
        self.Gen2 = get_model('eventtools_testapp', 'broadcasteventoccurrencegenerator')
        self.Gen3 = get_model('eventtools_testapp', 'lessoneventoccurrencegenerator')
        self.gens = [self.Gen1, self.Gen2, self.Gen3]

        for (occ, gen,) in zip(self.occs, self.gens):
            #Check that for each EventBase model defined, an Occurrence and an OccurrenceGenerator are created.
            self.assertTrue((occ != None))
            self.assertTrue((gen != None))
            
            #...and that the right FKs are specified.
            self.assertTrue(isinstance(occ.generator, ReverseSingleRelatedObjectDescriptor)) #This is what ForeignKey becomes
            self.assertTrue(isinstance(gen.event, ReverseSingleRelatedObjectDescriptor))
            
            #...and that the occurrence model is linked properly to the generator
            self.assertEqual(gen._occurrence_model_name.lower(), occ.__name__.lower())

class TestModel(TestCase):
    def test_event_without_variation(self):
        """
        Events that have no variation class defined still work (and that it is not allowed to try to set a variation)
        """
        
        subject = 'Django testing for n00bs'
        lesson = LessonEvent.objects.create(subject=subject)
        gen = lesson.create_generator(first_start_date=date(2010, 1, 1), first_start_time=time(13, 0), first_end_date=None, first_end_time=time(14, 0))
        occ = lesson.get_one_occurrence()
        self.assertEqual(occ.varied_event, None)
        self.assertRaises(AttributeError, getattr, occ.varied_event, 'subject')
        self.assertRaises(AttributeError, setattr, occ, 'varied_event', 'foo')
        self.assertEqual(occ.unvaried_event.subject, subject)
        self.assertEqual(occ.merged_event.subject, subject)



    def test_event_occurrence_attributes(self):
        """Test that event occurrences can override (any) field of their parent event"""
        
        # Create an event, a generator, and get (the only possible) occurrence from the generator.
        te1 = LectureEvent.objects.create(location='The lecture hall', title='Lecture series on Butterflies')
        self.assertTrue(te1.wheelchair_access) # The original event has wheelchair access
        gen = te1.create_generator(first_start_date=date(2010, 1, 1), first_start_time=time(13, 0), first_end_date=None, first_end_time=time(14, 0))
        self.assertTrue(gen)
        occ = te1.get_one_occurrence()
        self.assertTrue(occ)
        
        #Test that the occurrence is the one we expect
        expected = LectureEvent.Occurrence(generator=gen, unvaried_start_date=date(2010, 1, 1), unvaried_start_time=time(13, 0), unvaried_end_time=time(14, 0))

        self.assertEqual(occ, expected)

        #and that the occurrence's unvaried event shares properties with te1
        self.assertTrue(isinstance(occ.unvaried_event, LectureEvent))
        self.assertTrue(occ.unvaried_event.wheelchair_access)
        #and that the merged event is what we expect
        self.assertTrue(occ.merged_event.wheelchair_access)
        self.assertEqual(occ.merged_event.location, 'The lecture hall')
        
        #When first generated, there is no varied event for an occurrence.
        self.assertEqual(occ.varied_event, None)
        #So accessing a property raises AttributeError
        self.assertRaises(AttributeError, getattr, occ.varied_event, 'location')
        
        #Now create a variation with a different location
        occ.varied_event = te1.create_variation(location='The foyer')
        
        #Check the properties of the varied event, and that the merged event uses those to override the unvaried event
        self.assertEqual(occ.varied_event.location, 'The foyer')
        self.assertEqual(occ.unvaried_event.location, 'The lecture hall')
        self.assertEqual(occ.varied_event.wheelchair_access, None)

        self.assertEqual(occ.merged_event.location, 'The foyer')
        self.assertEqual(occ.merged_event.title, 'Lecture series on Butterflies')

        #Check that we can't write to merged event.
        self.assertRaises(Exception, setattr, occ.merged_event.location, "shouldn't be writeable")

        #Now update the title, location and wheelchair access of the varied event, and save the result.
        occ.varied_event.title = 'Butterflies I have known'
        occ.varied_event.location = 'The meeting room'
        occ.varied_event.wheelchair_access = False
        occ.varied_event.save()
        occ.save()
        
        #Check that the update merges correctly with the unvaried event
        self.assertTrue((occ.unvaried_event.title == 'Lecture series on Butterflies'))
        self.assertTrue((occ.varied_event.title == 'Butterflies I have known'))
        self.assertTrue((occ.merged_event.title == 'Butterflies I have known'))


        self.assertTrue((occ.unvaried_event.location == 'The lecture hall'))
        self.assertTrue((occ.varied_event.location == 'The meeting room'))
        self.assertTrue((occ.merged_event.location == 'The meeting room'))

        self.assertEqual(occ.unvaried_event.wheelchair_access, True)
        self.assertEqual(occ.varied_event.wheelchair_access, False)
        self.assertEqual(occ.merged_event.wheelchair_access, False)

        #Now update the title of the original event. The changes in the variation should persist in the database.
        te1.title = 'Lecture series on Lepidoptera'
        te1.save()
        
        te1 = LectureEvent.objects.get(pk=te1.pk)
        occ = te1.get_one_occurrence() #from the database
        self.assertEqual(occ.unvaried_event.title, 'Lecture series on Lepidoptera')
        self.assertEqual(occ.merged_event.title, 'Butterflies I have known')
        self.assertEqual(occ.varied_event.title, 'Butterflies I have known')

    # not done yet
    # def test_operator(self):
    #     te1 = LectureEvent.objects.create(location='The lecture hall', title='Lecture series on Butterflies')
    #     gen = te1.create_generator(first_start_date=date(2010, 1, 1), first_start_time=time(13, 0), first_end_date=date(2010, 1, 4), first_end_time=time(14, 0))
    # 
    #     gen2 = gen + timedelta(days=1, hours=1)
    #     self.assertEqual(gen2.first_start_date, date(2010, 1, 2))
    #     self.assertEqual(gen2.first_end_date, date(2010, 1, 5))
    #     self.assertEqual(gen2.first_start_time, time(14,0))
    #     self.assertEqual(gen2.first_end_time, time(15,0))
    #     self.assertNotEqual(gen, gen2)
    #     
    #     occ = gen2.get_first_occurrence()
    #     occ2 = occ + timedelta(days=1, hours=1)
    #     self.assertEqual(occ2.unvaried_timespan.start_date, date(2010, 1, 2))
    #     self.assertEqual(occ2.unvaried_timespan.end_date, date(2010, 1, 5))
    #     self.assertEqual(occ2.unvaried_timespan.start_time, time(14,0))
    #     self.assertEqual(occ2.unvaried_timespan.end_time, time(15,0))
    #     self.assertEqual(occ2.varied_timespan.start_date, date(2010, 1, 3))
    #     self.assertEqual(occ2.varied_timespan.end_date, date(2010, 1, 6))
    #     self.assertEqual(occ2.varied_timespan.start_time, time(15,0))
    #     self.assertEqual(occ2.varied_timespan.end_time, time(16,0))
    #     self.assertNotEqual(occ, occ2)
        

    def test_saving(self):
        """
        A small check that saving occurrences without variations does not create a blank variation.
        TODO: expand this so to check changing the time of an exceptional occurrence works the same way.
        """
        te1 = LectureEvent.objects.create(location='The lecture hall', title='Lecture series on Butterflies')
        te1.create_generator(first_start_date=date(2010, 1, 1), first_start_time=time(13, 0), first_end_date=None, first_end_time=time(14, 0))
        occ = te1.get_one_occurrence()
        num_variations1 = int(LectureEventVariation.objects.count())
        occ.save()
        num_variations2 = int(LectureEventVariation.objects.count())
        self.assertEqual(num_variations1, num_variations2)
        
    def test_occurrence_and_occurrence_generator_validation(self):
        evt = LectureEvent.objects.create(location='The lecture hall', title='Lecture series on Amphibians')
        form = LectureEventOccurrenceGeneratorForm(dict(
                event=evt.pk,
                first_start_date=str(date(2010, 8, 1)),
                first_start_time=str(time(13, 0)),
                first_end_date=str(date(2010, 7, 1))))
        self.assertFalse(form.is_valid(), "end date cannot be later than start date")

        form = LectureEventOccurrenceGeneratorForm(dict(
                event=evt.pk,
                first_start_date=str(date(2010, 8, 1)),
                first_start_time=str(time(13, 0))))
        self.assertTrue(form.is_valid())

        # same as above, except first_end_date not specified
        form = LectureEventOccurrenceGeneratorForm(dict(
                event=evt.pk,
                first_start_date=str(date(2010, 8, 1)),
                first_start_time=str(time(13, 0)),
                first_end_time=str(time(13, 0))))
        self.assertTrue(form.is_valid())

        # same as above, except first_end_date not specified
        form = LectureEventOccurrenceGeneratorForm(dict(
                event=evt.pk,
                first_start_date=str(date(2010, 8, 1))
            ))
        self.assertTrue(form.is_valid())


        # first_end_date not specified
        form = LectureEventOccurrenceGeneratorForm(dict(
                event=evt.pk,
                first_start_date=str(date(2010, 8, 1)),
                first_start_time=str(time(13, 0)),
                first_end_date=str(date(2010, 8, 1))))
        self.assertTrue(form.is_valid())
        
        # Missing start time and date
        form = LectureEventOccurrenceGeneratorForm(dict(
                event=evt.pk,
                first_end_date=str(date(2010, 9, 1)),
                first_end_time=str(time(13, 0))))
        self.assertFalse(form.is_valid())

        # normal case
        form = LectureEventOccurrenceGeneratorForm(dict(
                event=evt.pk,
                first_start_date=str(date(2010, 8, 1)),
                first_start_time=str(time(13, 0)),
                first_end_date=str(date(2010, 9, 1))))
        self.assertTrue(form.is_valid(), "normal case, should have validated")
        form.save()

        occ = evt.get_one_occurrence()
        self.assertFalse(occ.is_varied)
        self.assert_(occ.clean() is None)

        occ.varied_end_date = occ.varied_start_date + timedelta(-1)
        self.assertRaises(AttributeError, getattr, occ, 'is_varied')
        self.assertRaises(ValidationError, occ.clean)

    
    def test_occurrence_generator_weirdness(self):
        evt = BroadcastEvent.objects.create(presenter = "Jimmy McBigmouth", studio=2)
        gen = evt.create_generator(first_start_date=date(2010, 1, 1), first_start_time=time(13, 0), first_end_date=None, first_end_time=time(14, 0))
        
        #This didn't always work. Testing prevents regressions!
        self.assertTrue(evt)
        self.assertTrue(gen)
        self.assertEqual(evt.generators.count(), 1)
        self.assertEqual(list(evt.generators.all()), [gen])
    
    def test_occurrences(self):
        """
        Are modified occurrences saved and retrieved properly?
        """
        evt = BroadcastEvent.objects.create(presenter = "Jimmy McBigmouth", studio=2)
        #Let's start with 1 occurrence
        gen = evt.create_generator(first_start_date=date(2010, 1, 1), first_start_time=time(13, 0), first_end_date=None, first_end_time=time(14, 0))
        occ = evt.get_one_occurrence()
    
        self.assertEqual(occ.varied_start_time, time(13,0))
        self.assertEqual(occ.unvaried_start_time, time(13,0))
        # deprecated
        # self.assertEqual(occ.start_time, time(13,0))
        self.assertEqual(occ.timespan.start_time, time(13,0))
        self.assertEqual(occ.generator, gen)
        
        self.assertEqual(occ.id, None)
        self.assertEqual(occ.is_varied, False)
        
        #What happens if we save it? It's persisted, but it's not varied.
        occ.save()
        
        self.assertTrue(occ.id != None)
        
        self.assertEqual(occ.is_varied, False)
        self.assertEqual(occ.cancelled, False)
        
        #and it doesn't have a variation event (but we could assign one if we wanted)
        self.assertEqual(occ.varied_event, None)
        
        #What happens when we change the timing?
        occ.varied_start_time = time(14,0)
        occ.save()
        
        self.assertEqual(occ.is_varied, True)
        self.assertEqual(occ.cancelled, False)
        self.assertEqual(occ.timespan.start_time, time(14,0))        
        #and let's check that re-querying returns the varied event
        
        occ = evt.get_one_occurrence()
        self.assertEqual(occ.is_varied, True)
        self.assertEqual(occ.cancelled, False)
        self.assertEqual(occ.timespan.start_time, time(14,0))        
        
    def test_cancellation(self):
        evt = BroadcastEvent.objects.create(presenter = "Jimmy McBigmouth", studio=2)
        #Let's start with 1 occurrence
        gen = evt.create_generator(first_start_date=date(2010, 1, 1), first_start_time=time(13, 0), first_end_date=None, first_end_time=time(14, 0))
        occ = evt.get_one_occurrence()

        self.assertEqual(occ.cancelled, False)

        occ.cancel()
        occ = evt.get_one_occurrence()
        self.assertEqual(occ.cancelled, True)
        
        occ.uncancel() 
        occ = evt.get_one_occurrence()
        self.assertEqual(occ.cancelled, False)
        
        
    def test_variation_model(self):
        evt = BroadcastEvent.objects.create(presenter = "Jimmy McBigmouth", studio=2) 
        
        #have we got the FKs in place
        self.assertTrue(hasattr(BroadcastEventVariation, 'unvaried_event'))
        self.assertTrue(hasattr(evt, 'variations'))
     
        # let's try it out
        var_event = evt.create_variation(presenter = "Amy Sub")
        self.assertEqual(list(evt.variations.all()), [var_event])
        
        # we can also do it this way
        
        var_event_2 = BroadcastEventVariation.objects.create(unvaried_event=evt, presenter = "Alan Loco")
        self.assertEqual(set(evt.variations.all()), set([var_event, var_event_2]))
        
        # but not on an event that doesn't have a varied_by
        lesson = LessonEvent.objects.create(subject="canons")
        self.assertRaises(AttributeError, lesson.create_variation, {'subject': 'cannons'})
        
class TestGeneratorChange(TestCase):
    def test_generator_resave(self):
        """
        If we change the times of a generator, then all of the persisted occurrences should be resaved accordingly.
        """
        weekly = Rule.objects.create(name="weekly", frequency="WEEKLY")
        subject = 'Django testing for n00bs'
        lecture = LectureEvent.objects.create(title=subject, location="The attic")
        new_year = date(2010, 1, 1)
        datetime_gen = lecture.create_generator(first_start_date=new_year, first_start_time=time(13, 0), first_end_time=time(13, 0), rule=weekly)
        
        # vary the 1st jan event to start at 13.30 and finish at 14.30
        same_day_diff_time = datetime_gen.get_occurrences(new_year).next()
        same_day_diff_time.varied_start_time = time(13,30)
        same_day_diff_time.varied_end_time = time(14,30)
        same_day_diff_time.save()

        # vary the 8th jan event to be on 6th Jan
        diff_day_same_time = datetime_gen.get_occurrences(new_year+timedelta(7)).next()
        diff_day_same_time.varied_start_date = new_year+timedelta(5)
        diff_day_same_time.varied_end_date = new_year+timedelta(5)
        diff_day_same_time.save()

        #vary the 15th jan event to have a different location
        diff_location = datetime_gen.get_occurrences(new_year+timedelta(14)).next()
        diff_location.create_varied_event(location = "The basement")

        #NOW let's change the original generator.
        datetime_gen.first_start_date += timedelta(1)
        datetime_gen.first_end_date += timedelta(1)
        datetime_gen.first_start_time = time(14,0)
        datetime_gen.first_end_time = time(14,0)
        datetime_gen.save()
        
        #Persisted occurrences with modified times should show updated unvaried times but the *same* varied times as before.
        same_day_diff_time = datetime_gen.get_occurrences(new_year).next()
        self.assertEqual(same_day_diff_time.unvaried_start_date, date(2010, 1, 2))
        self.assertEqual(same_day_diff_time.varied_start_date, date(2010, 1, 1))
        self.assertEqual(same_day_diff_time.unvaried_end_date, date(2010, 1, 2))
        self.assertEqual(same_day_diff_time.varied_end_date, date(2010, 1, 1))
        
        self.assertEqual(same_day_diff_time.unvaried_start_time, time(14,0))
        self.assertEqual(same_day_diff_time.varied_start_time, time(13,30))
        self.assertEqual(same_day_diff_time.unvaried_end_time, time(14,0))
        self.assertEqual(same_day_diff_time.varied_end_time, time(14,30))

        diff_day_same_time = datetime_gen.get_occurrences(new_year+timedelta(5)).next()
        self.assertEqual(diff_day_same_time.unvaried_start_date, date(2010, 1, 9))
        self.assertEqual(diff_day_same_time.varied_start_date, date(2010, 1, 6))
        self.assertEqual(diff_day_same_time.unvaried_end_date, date(2010, 1, 9))
        self.assertEqual(diff_day_same_time.varied_end_date, date(2010, 1, 6))
        
        self.assertEqual(diff_day_same_time.unvaried_start_time, time(14,0))
        self.assertEqual(diff_day_same_time.varied_start_time, time(13,0))
        self.assertEqual(diff_day_same_time.unvaried_end_time, time(14,0))
        self.assertEqual(diff_day_same_time.varied_end_time, time(13,0))

        #Persisted occurrences with UNmodified times should show updated unvaried times AND varied times.
        diff_location = datetime_gen.get_occurrences(new_year+timedelta(15)).next()
        self.assertEqual(diff_location.unvaried_start_date, date(2010, 1, 16))
        self.assertEqual(diff_location.varied_start_date, date(2010, 1, 16))
        self.assertEqual(diff_location.unvaried_end_date, date(2010, 1, 16))
        self.assertEqual(diff_location.varied_end_date, date(2010, 1, 16))
        
        self.assertEqual(diff_location.unvaried_start_time, time(14,0))
        self.assertEqual(diff_location.varied_start_time, time(14,0))
        self.assertEqual(diff_location.unvaried_end_time, time(14,0))
        self.assertEqual(diff_location.varied_end_time, time(14,0))

    def test_dateonly_generator_resave(self):
        """
        If we change the times of a generator, then all of the persisted occurrences should be resaved accordingly.
        """
        weekly = Rule.objects.create(name="weekly", frequency="WEEKLY")
        subject = 'Django testing for n00bs'
        lecture = LectureEvent.objects.create(title=subject, location="The attic")
        new_year = date(2010, 1, 1)
        date_gen = lecture.create_generator(first_start_date=new_year, rule=weekly)
        
        # vary the 1st jan event to start at 13.30 and finish at 14.30
        same_day_plus_time = date_gen.get_occurrences(new_year).next()
        same_day_plus_time.varied_start_time = time(13,30)
        same_day_plus_time.varied_end_time = time(14,30)
        same_day_plus_time.save()

        # vary the 8th jan event to be on 6th Jan
        diff_day = date_gen.get_occurrences(new_year+timedelta(7)).next()
        diff_day.varied_start_date = new_year+timedelta(5)
        diff_day.varied_end_date = new_year+timedelta(5)
        diff_day.save()

        #vary the 15th jan event to have a different location
        diff_location = date_gen.get_occurrences(new_year+timedelta(14)).next()
        diff_location.create_varied_event(location = "The basement")

        #NOW let's change the original generator.
        date_gen.first_start_date += timedelta(1)
        date_gen.first_end_date += timedelta(1)
        date_gen.save()
        
        #Persisted occurrences with modified times should show updated unvaried times but the *same* varied times as before.
        same_day_plus_time = date_gen.get_occurrences(new_year).next()
        self.assertEqual(same_day_plus_time.unvaried_start_date, date(2010, 1, 2))
        self.assertEqual(same_day_plus_time.varied_start_date, date(2010, 1, 1))
        self.assertEqual(same_day_plus_time.unvaried_end_date, date(2010, 1, 2))
        self.assertEqual(same_day_plus_time.varied_end_date, date(2010, 1, 1))
        
        self.assertEqual(same_day_plus_time.unvaried_start_time, None)
        self.assertEqual(same_day_plus_time.varied_start_time, time(13,30))
        self.assertEqual(same_day_plus_time.unvaried_end_time, None)
        self.assertEqual(same_day_plus_time.varied_end_time, time(14,30))

        diff_day = date_gen.get_occurrences(new_year+timedelta(5)).next()
        self.assertEqual(diff_day.unvaried_start_date, date(2010, 1, 9))
        self.assertEqual(diff_day.varied_start_date, date(2010, 1, 6))
        self.assertEqual(diff_day.unvaried_end_date, date(2010, 1, 9))
        self.assertEqual(diff_day.varied_end_date, date(2010, 1, 6))
        
        self.assertEqual(diff_day.unvaried_start_time, None)
        self.assertEqual(diff_day.varied_start_time, None)
        self.assertEqual(diff_day.unvaried_end_time, None)
        self.assertEqual(diff_day.varied_end_time, None)

        #Persisted occurrences with UNmodified times should show updated unvaried times AND varied times.
        diff_location = date_gen.get_occurrences(new_year+timedelta(15)).next()
        self.assertEqual(diff_location.unvaried_start_date, date(2010, 1, 16))
        self.assertEqual(diff_location.varied_start_date, date(2010, 1, 16))
        self.assertEqual(diff_location.unvaried_end_date, date(2010, 1, 16))
        self.assertEqual(diff_location.varied_end_date, date(2010, 1, 16))
        
        self.assertEqual(diff_location.unvaried_start_time, None)
        self.assertEqual(diff_location.varied_start_time, None)
        self.assertEqual(diff_location.unvaried_end_time, None)
        self.assertEqual(diff_location.varied_end_time, None)

        #NOW let's add a time to the generator!
        date_gen.first_start_time = time(14,0)
        date_gen.first_end_time = time(14,0)
        date_gen.save()
        
        #Persisted occurrences with modified times should show updated unvaried times but the *same* varied times as before.
        same_day_plus_time = date_gen.get_occurrences(new_year).next()
        self.assertEqual(same_day_plus_time.unvaried_start_date, date(2010, 1, 2))
        self.assertEqual(same_day_plus_time.varied_start_date, date(2010, 1, 1))
        self.assertEqual(same_day_plus_time.unvaried_end_date, date(2010, 1, 2))
        self.assertEqual(same_day_plus_time.varied_end_date, date(2010, 1, 1))
        
        self.assertEqual(same_day_plus_time.unvaried_start_time, time(14,0))
        self.assertEqual(same_day_plus_time.varied_start_time, time(13,30))
        self.assertEqual(same_day_plus_time.unvaried_end_time, time(14,0))
        self.assertEqual(same_day_plus_time.varied_end_time, time(14,30))

        diff_day = date_gen.get_occurrences(new_year+timedelta(5)).next()
        self.assertEqual(diff_day.unvaried_start_date, date(2010, 1, 9))
        self.assertEqual(diff_day.varied_start_date, date(2010, 1, 6))
        self.assertEqual(diff_day.unvaried_end_date, date(2010, 1, 9))
        self.assertEqual(diff_day.varied_end_date, date(2010, 1, 6))
        
        self.assertEqual(diff_day.unvaried_start_time, time(14,0))
        self.assertEqual(diff_day.varied_start_time, None)
        self.assertEqual(diff_day.unvaried_end_time, time(14,0))
        self.assertEqual(diff_day.varied_end_time, None)

        #Persisted occurrences with UNmodified times should show updated unvaried times AND varied times.
        diff_location = date_gen.get_occurrences(new_year+timedelta(15)).next()
        self.assertEqual(diff_location.unvaried_start_date, date(2010, 1, 16))
        self.assertEqual(diff_location.varied_start_date, date(2010, 1, 16))
        self.assertEqual(diff_location.unvaried_end_date, date(2010, 1, 16))
        self.assertEqual(diff_location.varied_end_date, date(2010, 1, 16))
        
        self.assertEqual(diff_location.unvaried_start_time, time(14,0))
        self.assertEqual(diff_location.varied_start_time, time(14,0))
        self.assertEqual(diff_location.unvaried_end_time, time(14,0))
        self.assertEqual(diff_location.varied_end_time, time(14,0))

        #NOW let's remove a time from the generator!
        date_gen.first_start_time = None
        date_gen.first_end_time = None
        date_gen.save(test=True)
        
        #Persisted occurrences with modified times should show updated unvaried times but the *same* varied times as before.
        same_day_plus_time = date_gen.get_occurrences(new_year).next()
        self.assertEqual(same_day_plus_time.unvaried_start_date, date(2010, 1, 2))
        self.assertEqual(same_day_plus_time.varied_start_date, date(2010, 1, 1))
        self.assertEqual(same_day_plus_time.unvaried_end_date, date(2010, 1, 2))
        self.assertEqual(same_day_plus_time.varied_end_date, date(2010, 1, 1))
        
        self.assertEqual(same_day_plus_time.unvaried_start_time, None)
        self.assertEqual(same_day_plus_time.varied_start_time, time(13,30))
        self.assertEqual(same_day_plus_time.unvaried_end_time, None)
        self.assertEqual(same_day_plus_time.varied_end_time, time(14,30))

        diff_day = date_gen.get_occurrences(new_year+timedelta(5)).next()
        self.assertEqual(diff_day.unvaried_start_date, date(2010, 1, 9))
        self.assertEqual(diff_day.varied_start_date, date(2010, 1, 6))
        self.assertEqual(diff_day.unvaried_end_date, date(2010, 1, 9))
        self.assertEqual(diff_day.varied_end_date, date(2010, 1, 6))
        
        self.assertEqual(diff_day.unvaried_start_time, None)
        self.assertEqual(diff_day.varied_start_time, None)
        self.assertEqual(diff_day.unvaried_end_time, None)
        self.assertEqual(diff_day.varied_end_time, None)

        #Persisted occurrences with UNmodified times should show updated unvaried times AND varied times.
        diff_location = date_gen.get_occurrences(new_year+timedelta(15)).next()
        self.assertEqual(diff_location.unvaried_start_date, date(2010, 1, 16))
        self.assertEqual(diff_location.varied_start_date, date(2010, 1, 16))
        self.assertEqual(diff_location.unvaried_end_date, date(2010, 1, 16))
        self.assertEqual(diff_location.varied_end_date, date(2010, 1, 16))
        
        self.assertEqual(diff_location.unvaried_start_time, None)
        self.assertEqual(diff_location.varied_start_time, None)
        self.assertEqual(diff_location.unvaried_end_time, None)
        self.assertEqual(diff_location.varied_end_time, None)

         
    # def test_the_occurrence_admin(self):
    #      assert False