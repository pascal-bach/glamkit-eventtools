from django.test import TestCase
from _inject_app import TestCaseWithApp as AppTestCase
from eventtools_testapp.models import *
from datetime import date, time, datetime, timedelta
from _fixture import bigfixture, reload_films
from eventtools.utils import dateranges

class TestEvents(AppTestCase):
    
    def test_creation(self):

        """
        When you create an EventModel, you need to create an Occurrence class with a field 'event' that FKs to event.
        
        Occurrences are sorted by start (then end) by default.

        """
        self.assertTrue(hasattr(Event, 'occurrences'))
        self.assertTrue(hasattr(Occurrence, 'event'))
        
        #test sorting
        occs = Occurrence.objects.all()
        x = occs[0].start
        for o in occs:
            self.assertTrue(o.start >= x)
            x= o.start

        #test utils:
        e = Event.objects.all()[0]
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
        
        #and this way:
        o = Occurrence.objects.create(event=e, start=date.today())
        self.ae(o.start.time(), time.min)
        self.ae(o.end.date(), date.today())
        self.ae(o.end.time(), time.max)

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
        
        TODO: start queries are covered; ends and entirely queries are not.
        
        """
        all_occs = Event.objects.occurrences()
        self.ae(list(all_occs), list(Occurrence.objects.all()))
       
        gallery_occs = Event.objects.filter(venue=self.gallery).occurrences()
        self.ae(len(gallery_occs), 3)
        self.assertTrue(self.talk_morning in gallery_occs)
        self.assertTrue(self.talk_afternoon in gallery_occs)
        self.assertTrue(self.talk_tomorrow_morning_cancelled in gallery_occs)
        
        #two similar syntaxes
        cancelled_gallery_occs1 = Event.objects.filter(venue=self.gallery).occurrences(status='cancelled')
        cancelled_gallery_occs2 = Event.objects.filter(venue=self.gallery).occurrences().filter(status='cancelled')
        self.ae(list(cancelled_gallery_occs1), list(cancelled_gallery_occs2))
        self.ae(list(cancelled_gallery_occs2), [self.talk_tomorrow_morning_cancelled])
        
        # just checking a queryset is returned and can be further refined
        gallery_occs = Event.objects.filter(venue=self.gallery).occurrences().after(self.day2)
        self.ae(list(gallery_occs), [self.talk_tomorrow_morning_cancelled])

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

    def test_open_close(self):
        """
        You can query Event to find only those events that are opening or closing.
        
        A closing event is defined as the last occurrence start (NOT the last occurrence end, which would be less intuitive for users)
        
        TODO: in trees of events, what are the opening and closing occurrences?
        It should be that only occurrences that are the earliest/latest in their direct family are opening/closing.
        For now every event in the tree can have opens and closes.
        
        """
        
        o = Event.objects.opening_before(self.day1)
        self.ae(list(o), [self.talk, self.performance, self.film])
        o = Event.objects.opening_after(self.day1)
        self.ae(list(o), [self.talk, self.performance, self.film, self.film_with_popcorn, self.film_with_talk, self.film_with_talk_and_popcorn])
        o = Event.objects.opening_between(self.day1, self.day2)
        self.ae(list(o), [self.talk, self.performance, self.film, self.film_with_popcorn])
        o = Event.objects.opening_on(self.day1)
        self.ae(list(o), [self.talk, self.performance, self.film])
        o = Event.objects.opening_on(self.day2)
        self.ae(list(o), [self.film_with_popcorn])
        
        c = Event.objects.closing_before(self.day2)
        self.ae(list(c), [self.talk, self.film, self.film_with_popcorn])
        c = Event.objects.closing_after(self.day2)
        self.ae(list(c), [self.talk, self.performance, self.film_with_popcorn, self.film_with_talk, self.film_with_talk_and_popcorn])
        c = Event.objects.closing_between(self.day1, self.day2)
        self.ae(list(c), [self.talk, self.film, self.film_with_popcorn])
        c = Event.objects.closing_on(self.day2)
        self.ae(list(c), [self.talk, self.film_with_popcorn])
        c = Event.objects.closing_on(self.day1)
        self.ae(list(c), [self.film])
        
    def test_GET(self):
        """        
        a (GET) dictionary, containing date(time) from and to parameters can be passed.
           Event.objects.filter(venue=the_library, cancelled=True).occurrences_from_GET_params(request.GET, 'from', 'to')
        """
        self.ae(list(Occurrence.objects.from_GET()), list(Occurrence.objects.forthcoming()))        
        self.ae(list(Occurrence.objects.from_GET({'startdate': '2010-10-10'})), list(Occurrence.objects.after(self.day1)))
        self.ae(list(Occurrence.objects.from_GET({'enddate': '2010-10-11'})), list(Occurrence.objects.before(self.day2)))
        self.ae(list(Occurrence.objects.from_GET({'startdate': '2010-10-10', 'enddate': '2010-10-11'})), list(Occurrence.objects.between(self.day1, self.day2)))
    
    def test_change_cascade(self):       
        """
        Events are in an mptt tree, which indicates parents (more general) and children (more specific).
        When you save a parent event, every changed field cascades to all children events (and not to parent events).
        If the child event has a different value to the original, then the change doesn't cascade.
        """
        self.ae(self.film.get_descendant_count(), 3)
        self.ae(list(self.film.get_descendants(include_self=True)), [self.film, self.film_with_talk, self.film_with_talk_and_popcorn, self.film_with_popcorn])

        self.film.name = "Irish fillum night"
        self.film.save()

        # reload everything
        reload_films(self)
        
        self.ae(self.film_with_talk.name, "Irish fillum night")
        self.ae(self.film_with_talk_and_popcorn.name, "Irish fillum night")
        self.ae(self.film_with_popcorn.name, "Irish fillum night")
        
        self.film_with_talk.name = "Ireland's best films (with free talk)"
        self.film_with_talk.save()
        # reload everything
        reload_films(self)
        
        self.ae(self.film.name, "Irish fillum night")
        self.ae(self.film_with_talk_and_popcorn.name, "Ireland's best films (with free talk)")
        
        #put it all back
        self.film.name = self.film_with_talk.name = "Film Night"
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
    #     self.new_film = Event()
    #     self.ae(self.new_film.slug, 'the-slug')
    #     
    #     #object instantiation
    #     self.new_film = Event(parent=self.film)
    #     self.ae(self.new_film.name, self.film.name)
    #     self.ae(self.new_film.slug, 'the-slug')        
    # 
    #     #creation (saving)
    #     self.new_film = Event.objects.create(parent=self.film)
    #     self.ae(self.new_film.name, self.film.name)
    # 
    #     #get_or_create
    #     self.next_new_film, created = Event.objects.get_or_create(parent=self.film, slug="new-slug")
    #     self.ae(self.next_new_film.name, self.film.name)
    #     self.ae(self.next_new_film.slug, 'new-slug')        
        
    def test_diffs(self):
        self.ae(unicode(self.film), u'Film Night')
        self.ae(unicode(self.film_with_talk), u'Film Night (director\'s talk)')
        
    """
    DONE BUT NO TESTS: When you view an event, the diff between itself and its parent is shown, or fields are highlighted, etc, see django-moderation.
    """