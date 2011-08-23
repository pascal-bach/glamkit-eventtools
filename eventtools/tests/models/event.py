from django.test import TestCase
from eventtools.tests._inject_app import TestCaseWithApp as AppTestCase
from eventtools.tests.eventtools_testapp.models import *
from datetime import date, time, datetime, timedelta
from eventtools.tests._fixture import bigfixture, reload_films
from eventtools.utils import dateranges

class TestTestEvents(AppTestCase):
    
    def test_creation(self):

        """
        When you create an TestEventModel,
        you need to create an ExampleOccurrence class with a field 'event' that FKs to event.
        
        TestOccurrences are sorted by start (then end) by default.

        """
        self.assertTrue(hasattr(ExampleEvent, 'occurrences'))
        self.assertTrue(hasattr(ExampleOccurrence, 'event'))
        
        #test sorting
        occs = ExampleOccurrence.objects.all()
        x = occs[0].start
        for o in occs:
            self.assertTrue(o.start >= x)
            x= o.start

        #test utils:
        e = ExampleEvent.eventobjects.all()[0]
        occ_count = e.occurrences.count()
        e.occurrences.create(start=datetime.now())
        self.ae(occ_count+1, e.occurrences.count())

        #want to add just days too
        o = e.occurrences.create(start=date.today())
        self.ae(type(o.start), datetime)
        self.ae(type(o.end), datetime)
                
        self.ae(occ_count+2, e.occurrences.count())
        self.ae(o.start.time(), time.min)
        self.ae(o.end.date(), date.today())
        self.ae(o.end.time(), time.max)
        o.delete()
       
        #and this way:
        o = ExampleOccurrence.objects.create(event=e, start=date.today())
        self.ae(o.start.time(), time.min)
        self.ae(o.end.date(), date.today())
        self.ae(o.end.time(), time.max)
        o.delete()

    def test_occurrence_relation(self):
        """
        You can query the occurrences for a single event by date(datetime) range etc.
           e.occurrences.filter(status='cancelled')
           e.occurrences.all().between(dt1, dt2)
        """
        talks = self.talk.occurrences.all()
        self.ae(len(talks), 3)

        talks = self.talk.occurrences.filter(status='cancelled')
        self.ae(len(talks), 1)

        #day range
        talks = self.talk.occurrences.between(self.day1, self.day2)
        self.ae(len(talks), 3)
    
        #before and after
        talks = self.talk.occurrences.before(self.day1)
        self.ae(len(talks), 2)
        talks = self.talk.occurrences.after(self.day2)
        self.ae(len(talks), 1)

        #one day is allowed
        talks1 = self.talk.occurrences.on(self.day1)
        self.ae(len(talks1), 2)
        # and it's the same as passing the same day into the range.
        talks2 = self.talk.occurrences.between(self.day1, self.day1)
        self.ae(list(talks1), list(talks2))

        #combining queries
        talks = self.talk.occurrences.filter(status='cancelled').between(self.day1, self.day2)
        self.ae(len(talks), 1)
        
        # hour range
        morningstart = datetime.combine(self.day1, time.min)
        morningend = datetime.combine(self.day1, time(12,00))
        talks = self.talk.occurrences.between(morningstart, morningend)
        self.ae(len(talks), 1)
        
    def test_occurrences_from_events(self):
        """
        You can query occurrences for an event queryset, including by date range etc.
        
        TODO: start queries are covered in tests; ends and entirely queries are not.
        
        You can get the opening and closing occurrence for an event:
        
        """
        all_occs = ExampleEvent.eventobjects.occurrences()
        self.ae(list(all_occs), list(ExampleOccurrence.objects.all()))
       
        gallery_occs = ExampleEvent.eventobjects.filter(venue=self.gallery).occurrences()
        self.ae(len(gallery_occs), 3)
        self.assertTrue(self.talk_morning in gallery_occs)
        self.assertTrue(self.talk_afternoon in gallery_occs)
        self.assertTrue(self.talk_tomorrow_morning_cancelled in gallery_occs)
        
        #two similar syntaxes
        cancelled_gallery_occs1 = ExampleEvent.eventobjects.filter(venue=self.gallery).occurrences(status='cancelled')
        cancelled_gallery_occs2 = ExampleEvent.eventobjects.filter(venue=self.gallery).occurrences().filter(status='cancelled')
        self.ae(list(cancelled_gallery_occs1), list(cancelled_gallery_occs2))
        self.ae(list(cancelled_gallery_occs2), [self.talk_tomorrow_morning_cancelled])
        
        # just checking a queryset is returned and can be further refined
        gallery_occs = ExampleEvent.eventobjects.filter(venue=self.gallery).occurrences().after(self.day2)
        self.ae(list(gallery_occs), [self.talk_tomorrow_morning_cancelled])
        
        #opening and closing
        self.ae(self.performance.opening_occurrence(), self.performance_evening)
        self.ae(self.performance.closing_occurrence(), self.performance_day_after_tomorrow)

    # The bigfixture takes ages.
    # def test_advanced_queries(self):
    #     """
    #     There are shortcut occurrence queries, which define date range relative to the current day.
    #     
    #     Weeks can start on sunday (6), monday (0), etc. Weekends can be any set of days (some sites include fridays). These are defined in settings.
    #     """
    #     
    #     #create a huge fixture of occurrences for event self.pe
    #     bigfixture(self)
    #     
    #     num_per_day = 5 #how many events we generate each day
    #             
    #     peo = self.pe.occurrences
    #     
    #     #forthcoming and recent
    #     forthcoming = peo.forthcoming()
    #     recent = peo.recent()
    # 
    #     # self.ae(recent.count(), 4696)
    #     # self.ae(forthcoming.count(), 1514)
    #     
    #     dtnow = datetime.now()
    #     
    #     for o in forthcoming:
    #         self.assertTrue(o.start > dtnow)
    # 
    #     for o in recent:
    #         self.assertTrue(o.end < dtnow)
    # 
    #     on = peo.starts_on(self.todaynow)
    #     # 5 events * 5 or 6 ranges
    #     if dateranges.is_weekend(self.todaynow):
    #         self.ae(on.count(), 30)
    #     else:
    #         self.ae(on.count(), 25)
    #         
    #     # test in a few days when it prob won't be the weekend
    #     on = peo.starts_on(self.todaynow+timedelta(5))
    #     # 5 events * 4 or 5 ranges (no today)
    #     if dateranges.is_weekend(self.todaynow+timedelta(5)):
    #         self.ae(on.count(), 25)
    #     else:
    #         self.ae(on.count(), 20)
    # 
    #     week = peo.starts_in_week_of(self.todaynow+timedelta(365))
    #     # in next year. Only 7 * 5 event
    #     self.ae(week.count(), 35)        

    def test_qs_occurrences(self):
        """
        You can query ExampleEvent to find only those events that are opening or closing.
        
        A closing event is defined as the last occurrence start (NOT the last occurrence end, which would be less intuitive for users)
        
        In trees of events, the latest/earliest in an occurrence's children are
        the opening/closing event.
        
        """
        
        o = ExampleEvent.eventobjects.opening_occurrences()
        o2 = [a.opening_occurrence() for a in ExampleEvent.eventobjects.all()]
        self.ae(set(o), set(o2))

        o = ExampleEvent.eventobjects.closing_occurrences()
        o2 = [a.closing_occurrence() for a in ExampleEvent.eventobjects.all()]
        self.ae(set(o), set(o2))

        
    def test_GET(self):
        """        
        a (GET) dictionary, containing date(time) from and to parameters can be passed.
           ExampleEvent.eventobjects.filter(venue=the_library, cancelled=True).occurrences_from_GET_params(request.GET, 'from', 'to')
        This returns a tuple of the parsed dates, too.
        """
        self.ae(list(ExampleOccurrence.objects.from_GET()[0]), list(ExampleOccurrence.objects.forthcoming()))        
        self.ae(list(ExampleOccurrence.objects.from_GET({'startdate': '2010-10-10'})[0]), list(ExampleOccurrence.objects.after(self.day1)))
        self.ae(list(ExampleOccurrence.objects.from_GET({'enddate': '2010-10-11'})[0]), list(ExampleOccurrence.objects.before(self.day2).reverse()))
        self.ae(list(ExampleOccurrence.objects.from_GET({'startdate': '2010-10-10', 'enddate': '2010-10-11'})[0]), list(ExampleOccurrence.objects.between(self.day1, self.day2)))
    
    def test_change_cascade(self):       
        """
        TestEvents are in an mptt tree, which indicates parents (more general) and children (more specific).
        When you save a parent event, every changed field cascades to all children events (and not to parent events).
        If the child event has a different value to the original, then the change doesn't cascade.
        """
        self.ae(self.film.get_descendant_count(), 3)
        self.ae(list(self.film.get_descendants(include_self=True)), [self.film, self.film_with_talk, self.film_with_talk_and_popcorn, self.film_with_popcorn])

        self.film.title = "Irish fillum night"
        self.film.save()

        # reload everything
        reload_films(self)
                
        self.ae(self.film_with_talk.title, "Irish fillum night")
        self.ae(self.film_with_talk_and_popcorn.title, "Irish fillum night")
        self.ae(self.film_with_popcorn.title, "Irish fillum night")
        
        self.film_with_talk.title = "Ireland's best films (with free talk)"
        self.film_with_talk.save()
        # reload everything
        reload_films(self)
        
        self.ae(self.film.title, "Irish fillum night")
        self.ae(self.film_with_talk_and_popcorn.title, "Ireland's best films (with free talk)")
        
        #put it all back
        self.film.title = self.film_with_talk.title = "Film Night"
        self.film.save()
        self.film_with_talk.save()
        
        # reload everything
        reload_films(self)

    # come back to this one (works in admin!)
    # def test_tree_creation(self):
    #     """
    #     If we create a new child, it can take all of its parents' fields (but not occurrences or generators).
    #     """
    # 
    #     self.new_film = ExampleEvent()
    #     self.ae(self.new_film.slug, 'the-slug')
    #     
    #     #object instantiation
    #     self.new_film = ExampleEvent(parent=self.film)
    #     self.ae(self.new_film.title, self.film.title)
    #     self.ae(self.new_film.slug, 'the-slug')        
    # 
    #     #creation (saving)
    #     self.new_film = ExampleEvent.eventobjects.create(parent=self.film)
    #     self.ae(self.new_film.title, self.film.title)
    # 
    #     #get_or_create
    #     self.next_new_film, created = ExampleEvent.eventobjects.get_or_create(parent=self.film, slug="new-slug")
    #     self.ae(self.next_new_film.title, self.film.title)
    #     self.ae(self.next_new_film.slug, 'new-slug')        

    def test_tree_queries(self):
        """
        Sometimes you really do want to list of events, not occurrences, (e.g. events by tag, in alpha order).
        The specific mechanism for this is implementation-specific, but since events are variations in a tree,
        you might not want to show all the variations in such a list - especially not the events with no occurrences.
        
        If you choose a rule like 'use only events with a slug (or title) different to its parent', then that is implementation-specific.
        
        However, if you want 
        only the most top-level events that have occurrences,
        or only events that have occurrences,
        or only events without occurrences that have children with occurrences,
        or only events without occurrences that have descendants that have occurrences,
        or only events that differ from their parents in inherited fields,
        or combinations of these querysets,
        then these utilities will help.
        
        Fundamentally, we want to be able to run queries that return events based on properties of their relatives:
        
        ExampleEvent.eventobjects.with_children_having(*args, *kwargs)
        ExampleEvent.eventobjects.with_descendants_having(*args, *kwargs)
        ExampleEvent.eventobjects.with_parent_having(*args, *kwargs)
        ExampleEvent.eventobjects.with_ancestors_having(*args, *kwargs)
        ExampleEvent.eventobjects.without_children_having(*args, *kwargs)
        ExampleEvent.eventobjects.without_descendants_having(*args, *kwargs)
        ExampleEvent.eventobjects.without_parent_having(*args, *kwargs)
        ExampleEvent.eventobjects.without_ancestors_having(*args, *kwargs)
        
        (This should go into mptt some day)
        """
        
        self.has_no_occurrences = ExampleEvent.eventobjects.create(title="no occurrences", slug="no-occurrences")
        self.has_some_occurrences = ExampleEvent.eventobjects.create(parent=self.has_no_occurrences, title="some occurrences", slug="some-occurrences")
        self.has_some_occurrences.occurrences.create(start=date.today())
        self.has_some_more_occurrences = ExampleEvent.eventobjects.create(parent=self.has_some_occurrences, title="more occurrences", slug="more-occurrences")
        self.has_some_more_occurrences.occurrences.create(start=date.today())
        
        #reload!
        self.has_no_occurrences = self.has_no_occurrences.reload()
        self.has_some_occurrences = self.has_some_occurrences.reload() 
        self.has_some_more_occurrences = self.has_some_more_occurrences.reload() 
        
        tree = self.has_no_occurrences.get_descendants(include_self=True)
        
        #fundamentals
        wch = tree.with_children_having(title__contains="occurrences")
        wdh = tree.with_descendants_having(title__contains="occurrences")
        #include self applies to the query for 'descendants'
        wdh2 = tree.with_descendants_having(title__contains="occurrences", include_self=False)
        wph = tree.with_parent_having(title__contains="no")
        wah = tree.with_ancestors_having(title__contains="no")
        
        woch = tree.without_children_having(title__contains="more")
        wodh = tree.without_descendants_having(title__contains="some")
        wodh2 = tree.without_descendants_having(title__contains="some", include_self=False)
        woph = tree.without_parent_having(title__contains="some")
        woah = tree.without_ancestors_having(title__contains="some")

        self.assertEqual(list(wch), [self.has_no_occurrences, self.has_some_occurrences])
        self.assertEqual(list(wdh), [self.has_no_occurrences, self.has_some_occurrences, self.has_some_more_occurrences])
        self.assertEqual(list(wdh2), [self.has_no_occurrences, self.has_some_occurrences])
        self.assertEqual(list(wph), [self.has_some_occurrences])
        self.assertEqual(list(wah), [self.has_some_occurrences, self.has_some_more_occurrences])
        
        self.assertEqual(list(woch), [self.has_no_occurrences, self.has_some_more_occurrences])
        self.assertEqual(list(wodh), [self.has_some_more_occurrences])
        self.assertEqual(list(wodh2), [self.has_some_occurrences, self.has_some_more_occurrences])
        self.assertEqual(list(woph), [self.has_no_occurrences, self.has_some_occurrences])
        self.assertEqual(list(woah), [self.has_no_occurrences, self.has_some_occurrences])

        objects_having_occurrences = tree.having_occurrences()
        objects_having_no_occurrences = tree.having_no_occurrences()
        
        self.assertEqual(list(objects_having_occurrences), [self.has_some_occurrences, self.has_some_more_occurrences])
        self.assertEqual(list(objects_having_no_occurrences), [self.has_no_occurrences])        
        
        #a useful derivative
        highest_having_occurrences = tree.highest_having_occurrences()
        self.assertEqual(list(highest_having_occurrences), [self.has_some_occurrences])
        
        # self.ae(self.has_some_more_occurrences.highest_descendant_having_occurrences(), self.has_some_occurrences)
        # self.ae(self.has_some_occurrences.highest_descendant_having_occurrences(), self.has_some_occurrences)
        # self.ae(self.has_some_occurrences.highest_descendant_having_occurrences(include_self=False), None)
        # self.ae(self.has_no_occurrences.highest_descendant_having_occurrences(), None)
        # self.ae(self.has_no_occurrences.highest_descendant_having_occurrences(include_self=False), None)

                
    def test_event_family(self):
        """
        Utils:
        
        Given an event, get all the events that are descendant. Optionally exclude self.        
        Given an event, get all the events that are either descendants or ancestors. Optionally exclude self.        
        Given an event, get occurrences for all descendants. Optionally exclude self.
        Given an event, get occurrences for all descendants and ancestors. Optionally exclude self.
        (Inclusion of self by default is different to mptt)       
        """
        
        #descendants (this is an mptt function)
        self.ae(list(self.film.get_descendants()), [self.film_with_talk, self.film_with_talk_and_popcorn, self.film_with_popcorn])
        self.ae(list(self.film_with_talk.get_descendants()), [self.film_with_talk_and_popcorn])
        self.ae(list(self.film_with_talk.get_descendants(include_self=True)), [self.film_with_talk, self.film_with_talk_and_popcorn])
        
        # occurrence equivalents
        self.ae(list(self.film.get_descendants(include_self=True).occurrences()), [self.film_occ, self.film_with_popcorn_occ, self.film_with_talk_occ, self.film_with_talk_and_popcorn_occ])
        self.ae(list(self.film.get_descendants(include_self=False).occurrences()), [self.film_with_popcorn_occ, self.film_with_talk_occ, self.film_with_talk_and_popcorn_occ])
        self.ae(list(self.film_with_talk.get_descendants(include_self=True).occurrences()), [self.film_with_talk_occ, self.film_with_talk_and_popcorn_occ])
        self.ae(list(self.film_with_talk.get_descendants(include_self=False).occurrences()), [self.film_with_talk_and_popcorn_occ])
        
        #proxies
        self.ae(list(self.film.get_descendants(include_self=True).occurrences()), list(self.film.complete_occurrences()))
        self.ae(list(self.film_with_talk.get_descendants(include_self=True).occurrences()), list(self.film_with_talk.complete_occurrences()))

    def test_diffs(self):
        self.ae(unicode(self.film), u'Film Night')
        self.ae(unicode(self.film_with_talk), u'Film Night (director\'s talk)')
        
    """
    DONE BUT NO TESTS: When you view an event, the diff between itself and its parent is shown, or fields are highlighted, etc, see django-moderation.
    """