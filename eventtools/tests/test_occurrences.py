# -*- coding: utf-8“ -*-
from django.test import TestCase
from _inject_app import TestCaseWithApp as AppTestCase
from eventtools_testapp.models import *
from datetime import date, time, datetime, timedelta
from _fixture import bigfixture, reload_films
from eventtools.utils import datetimeify
from dateutil.relativedelta import relativedelta

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
    def test_occurrence_create(self):
        e = ExampleEvent.eventobjects.create(name="event with occurrences")
        
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
        o = e.occurrences.create(start=dt1, end=dt2)
        self.ae(o.start, dt1)
        self.ae(o.end, dt2)

        o = e.occurrences.create(start=dt1)
        self.ae(o.start, dt1)
        self.ae(o.end, dt1)

        o = e.occurrences.create(start=d1min)
        self.ae(o.start, d1min)
        self.ae(o.end, d1max)

        
        #dates
        o = e.occurrences.create(start=d1)
        self.ae(o.start, d1min)
        self.ae(o.end, d1max)

        o = e.occurrences.create(start=d1, end=d2)
        self.ae(o.start, d1min)
        self.ae(o.end, d2max)

        #combos
        o = e.occurrences.create(start=dt1, end=d2)
        self.ae(o.start, dt1)
        self.ae(o.end, d2max)
        
        o = e.occurrences.create(start=d1, end=dt2)
        self.ae(o.start, d1min)
        self.ae(o.end, dt2)
        
        #missing start date
        self.assertRaises(TypeError, e.occurrences.create, **{'end':dt1})
        self.assertRaises(TypeError, e.occurrences.create, **{'end':d1})
        
        #invalid start value
        self.assertRaises(TypeError, e.occurrences.create, **{'start':t1})
        self.assertRaises(TypeError, e.occurrences.create, **{'start':t1, 'end':d1})
        self.assertRaises(TypeError, e.occurrences.create, **{'start':t1, 'end':dt1})

        #invalid end values
        self.assertRaises(TypeError, e.occurrences.create, **{'end':t1})
        self.assertRaises(TypeError, e.occurrences.create, **{'start':d1, 'end':t1})
        self.assertRaises(TypeError, e.occurrences.create, **{'start':dt1, 'end':t2})
        
        #start date later than end date
        self.assertRaises(AttributeError, e.occurrences.create, **{'start':dt2, 'end':dt1})
        self.assertRaises(AttributeError, e.occurrences.create, **{'start':d2, 'end':dt1})
        self.assertRaises(AttributeError, e.occurrences.create, **{'start':d2, 'end':d1})
    
    def test_occurrence_properties(self):
        """
        Occurrences have a duration.

        Occurrences have a robot description.
        
        Occurrences that are currently taking place return true for now_on.

        Occurrences that finish in the past return True for has_finished.

        We can find out how long we have to wait until an occurrence starts.
        We can find out how long it has been since an occurrence finished.
        """
        e = ExampleEvent.eventobjects.create(name="event with occurrences")
        
        now = datetime.now()
        earlier = now - timedelta(seconds=600)
        later = now + timedelta(seconds=600)
        
        d1 = date(2010,1,1)
        d2 = date(2010,1,2)
        t1 = time(9,00)
        t2 = time(10,00)        
        dt1 = datetime.combine(d1, t1)
        dt2 = datetime.combine(d2, t2)
        
        o = e.occurrences.create(start=dt1, end=dt2)
        o2 = e.occurrences.create(start=earlier, end=later)

        self.ae(o.duration, timedelta(days=1, seconds=3600))
        self.ae(o.relative_duration, relativedelta(days=1, hours=1))
        self.ae(o.timespan_description(), "1 January 2010, 9am until 10am on 2 January 2010")

        self.ae(o.has_finished, True)
        self.ae(o.has_started, True)
        self.ae(o.now_on, False)
        self.ae(o2.has_finished, False)
        self.ae(o2.has_started, True)
        self.ae(o2.now_on, True)

        self.assertTrue(o.time_to_go() < timedelta(0))
        self.ae(o2.time_to_go(), None)
        self.assertTrue(o.relative_time_to_go().months < 0)
        self.ae(o2.relative_time_to_go(), None)

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
