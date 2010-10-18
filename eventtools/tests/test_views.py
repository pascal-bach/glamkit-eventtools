# -*- coding: utf-8“ -*-
from django.test import TestCase
from _inject_app import TestCaseWithApp as AppTestCase
from eventtools_testapp.models import *
from datetime import date, time, datetime, timedelta
from _fixture import bigfixture, reload_films
from eventtools.utils import datetimeify
from dateutil.relativedelta import relativedelta
from django.core.urlresolvers import reverse

class TestViews(AppTestCase):
    
    def test_purls(self):
        """
        An occurrence has a pURL based on its id. Anything after a + sign is ignored, allowing eg. slug to be used in the URL.
        You can view a page for an occurrence.
        """
        
        e = self.daily_tour
        o = e.occurrences.all()[0]
        
        #occurrence page
        ourl = reverse('event_occurrence', o.id)
        self.assertTrue(str(o.id) in ourl)
        r1 = self.client.get(ourl)
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.get("%s+ignored-stuff" % ourl)
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2.content, "Daily Tour")       
        self.assertEqual(r1.content, r2.content)
        self.assertContains(r2.content, "Friday, 1 January, 2010")
        self.assertNotContains(r2.content, "00:00")
        self.assertNotContains(r2.content, "12am")
        self.assertNotContains(r2.content, "midnight")
        
        e2 = self.weekly_talk
        ourl = reverse('event_occurrence', e2.occurrences.all()[0].id)
        r1 = self.client.get(ourl)
        self.assertContains(r1.content, "Weekly Talk")
        self.assertContains(r1.content, "Friday, 1 Janualy, 2010")
        self.assertContains(r1.content, "10am&ndash;noon")
        
    
    def test_list_view(self):
        """
        You can view a paginated list of occurrences for an event qs, following a given day, using ?startdate=2010-10-22&page=2.
        Each page shows n=20 occurrences.
        The occurrences are in chronological order.
        The times of all-day events do not appear.
        If there are no events in a given day, the day is not shown.
        The occurrences are grouped by day (and thus a day's occurrences may span several pages - this makes computation easier). TODO if a day is unfinished, show 'more on page n+1'..
        If there are no events in a given page, a 'no events match' message is shown.
        """
        url = reverse('event_list',)
        r = self.client.get(url,  {'startdate':'2010-01-01'})
        self.assertEqual(r.context.occurrence_list.count(), 20)
        self.assertEqual(r.context.occurrence_list[0].start.date(), date(2010,1,1))
            
        #chrono order
        d = r.context.occurrence_list[0].start
        for occ in r.context.occurrence_list:
            self.assertTrue(occ.start >= d)
            d = occ.start
        
        self.assertContains(r.content, "Friday, 1 January 2010", 1) #only print the date once
        self.assertNotContains(r.content, "Saturday, 2 January 2010") #there are no events
        
        self.assertContains(r.content, "10am&ndash;noon")
        self.assertNotContains(r.content, "12am")# these are all-day
        self.assertNotContains(r.content, "00:00")# these are all-day
        self.assertNotContains(r.content, "midnight") # these are all-day

        #doesn't matter how far back you go.
        r2 = self.client.get(url,  {'startdate':'2000-01-01'})
        self.assertEqual(r.content, r2.content)

        #show an 'not found' message
        r = self.client.get(url,  {'startdate':'2020-01-01'})
        self.assertEqual(r.context.occurrence_list.count(), 0)
        self.assertContains(r.content, "Sorry, no events were found")
        self.assertNotContains(r.content, "Earlier")
        self.assertNotContains(r.content, "Later")
        self.assertEqual(r.status_code, 200) #not 404
        
    def test_date_range_view(self):
        """
        You can show all occurrences between two days on one page, by adding ?enddate=2010-10-24. Pagination adds or subtracts the difference in days (+1 - consider a single day) to the range.
        For some ranges, pagination is by a different amount:
        Precisely a month (paginate by month)
        Precisely a year (paginate by year)
        """
        
    def test_event_view(self):
        """
        You can view a paginated list of occurrences for an event.
        """
        #event page
        eurl = reverse('event', e.slug)
        r3 = self.client.get(eurl, {'page': 2})
        self.assertEqual(r3.status_code, 200)
        self.assertTrue(ourl in r3.response)
    
        #should have some pagination (3 pages)
        self.assertEqual(r3.context.occurrence_list.count(), 20)
        self.assertContains(r3.response, "Earlier")
        self.assertContains(r3.response, "Later")
        self.assertContains(r3.response, "1")
        self.assertContains(r3.response, "2")
        self.assertContains(r3.response, "3")

    def test_hcal(self):
        """
        The page uses hCalendar microformat.
        """

    def test_ical(self):
        """
        You can view an ical for an occurrence.
        The ical is linked from the occurrence page.
        You can view an ical for a collection of occurrences.
        (TODO: do large icals perform well? If not we might have to make it a feed.)
        """

    def test_feeds(self):
        """
        You can view an RSS feed for an iterable of occurrences.
        """

        """
        CALENDAR

        A template tag shows a calendar of eventoccurrences in a given month.

        Calendar's html gives classes for 'today', 'date selection', 'has_events', 'no_events', 'prev_month' 'next_month'.

        Calendar optionally shows days.

        Calendar optionally hides leading or trailing empty weeks.

        Calendar can optionally navigate to prev/next months, which set a start_date to the 1st of the next month.



        API (TODO)

        """