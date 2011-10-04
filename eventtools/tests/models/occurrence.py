# -*- coding: utf-8“ -*-
from django.db import IntegrityError
from django.test import TestCase
from eventtools.tests._fixture import fixture
from eventtools.tests._inject_app import TestCaseWithApp as AppTestCase
from eventtools.tests.eventtools_testapp.models import *
from datetime import date, time, datetime, timedelta
from eventtools.utils import datetimeify

class TestOccurrences(AppTestCase):
    """
    Occurrences must have a start datetime and end datetime. (We might have to make a widget to support entry of all-day events).

    If start.time is 'ommitted', it is set to time.min.
    If end is omitted, then:
        end.date = start.date, then apply rule below for time.
    
    If end.time is 'ommitted' it is set to start.time, unless start.time is time.min in which case end.time is set to time.max.

    If an occurrence's times are min and max, then it is an all-day event.

    End datetime must be >= start datetime.
    """
    def setUp(self):
        super(TestOccurrences, self).setUp()
        fixture(self)

    def test_occurrence_create(self):
        e = ExampleEvent.eventobjects.create(title="event with occurrences")
        
        d1 = date(2010,1,1)
        d2 = date(2010,1,2)
        d1min = datetimeify(d1, clamp='min')
        d2min = datetimeify(d2, clamp='min')
        t1 = time(9,00)
        t2 = time(10,00) 
        dt1 = datetime.combine(d1, t1)
        dt2 = datetime.combine(d2, t2)
        
        #datetimes
        o = e.occurrences.create(start=dt1, _duration=24*60+60)
        self.ae(o.start, dt1)
        self.ae(o.end(), dt2)
        o.delete()

        o = e.occurrences.create(start=dt1)
        self.ae(o.start, dt1)
        self.ae(o.end(), dt1)
        o.delete()

        o = e.occurrences.create(start=d1min)
        self.ae(o.start, d1min)
        self.ae(o.end(), d1min)
        o.delete()

        #missing start date
        self.assertRaises(Exception, e.occurrences.create, **{'_duration': 60})

        #invalid start value
        self.assertRaises(Exception, e.occurrences.create, **{'start':t1})
        self.assertRaises(Exception, e.occurrences.create, **{'start':t1, '_duration':60})

    def test_occurrence_duration(self):
        e = ExampleEvent.eventobjects.create(title="event with occurrences")
        d1 = date(2010,1,1)

        # Occurrences with no duration have duration 0
        o = e.occurrences.create(start=d1)
        self.ae(o._duration, None)
        self.ae(o.duration, timedelta(0))
        o._duration = 0
        self.ae(o.duration, timedelta(0))

        # Occurrences with a given _duration in minutes have a corresponding timedelta duration property
        o._duration = 60
        self.ae(o.duration, timedelta(seconds=60*60))

        # - even if it's more than a day
        o._duration = 60 * 25
        self.ae(o.duration, timedelta(days=1, seconds=60*60))

        # Can set duration property with a timedelta
        o.duration = timedelta(days=1, seconds=60*60)
        self.ae(o._duration, 25 * 60)
        self.ae(o.duration, timedelta(days=1, seconds=60*60))

        # Can set duration property with a literal
        o.duration = 25*60
        self.ae(o._duration, 25 * 60)
        self.ae(o.duration, timedelta(days=1, seconds=60*60))

        # Can't have <0 duration
        self.assertRaises(IntegrityError, e.occurrences.create, **{'_duration': -60})




    def test_timespan_properties(self):
        """
        Occurrences have a robot description.
        
        Occurrences that are currently taking place return true for now_on.

        Occurrences that finish in the past return True for has_finished.

        We can find out how long we have to wait until an occurrence starts.
        We can find out how long it has been since an occurrence finished.
        """
        e = ExampleEvent.eventobjects.create(title="event with occurrences")
        
        now = datetime.now()
        earlier = now - timedelta(seconds=600)

        d1 = date(2010,1,1)
        t1 = time(9,00)
        dt1 = datetime.combine(d1, t1)
        
        o = e.occurrences.create(start=dt1, _duration=25*60)
        o2 = e.occurrences.create(start=earlier, _duration = 20)

        self.ae(o.duration, timedelta(days=1, seconds=3600))
        self.ae(o.timespan_description(), "1 January 2010, 9am until 10am on 2 January 2010")

        self.ae(o.has_finished(), True)
        self.ae(o.has_started(), True)
        self.ae(o.now_on(), False)
        self.ae(o2.has_finished(), False)
        self.ae(o2.has_started(), True)
        self.ae(o2.now_on(), True)

        self.assertTrue(o.time_to_go() < timedelta(0))
        self.ae(o2.time_to_go(), timedelta(0))

"""
TODO

Occurrences know if they are the opening or closing occurrences for their event.

You can filter an Occurrence queryset to show only those occurrences that are opening or closing.

The custom admin occurrence view lists the occurrences of an event and all its children. Each occurrence shows which event it is linked to.

The custom admin view can be used to assign a different event to an occurrence. The drop-down list only shows the given event and its children.

    
Warning
The “delete selected objects” action uses QuerySet.delete() for efficiency reasons, which has an important caveat: your model’s delete() method will not be called.

If you wish to override this behavior, simply write a custom action which accomplishes deletion in your preferred manner – for example, by calling Model.delete() for each of the selected items.

For more background on bulk deletion, see the documentation on object deletion.
"""
