__author__ = 'gturner'
from eventtools.tests._inject_app import TestCaseWithApp as AppTestCase
from eventtools.tests.eventtools_testapp.models import *
from eventtools.models import Rule
import datetime

class TestEventTree(AppTestCase):

    def setUp(self):
        super(TestEventTree, self).setUp()

        #SCENARIO 1: Variation
        #there is a daily tour on for 30 days in January, run by Anna, which is listed as an event.
        self.tour = ExampleEvent.tree.create(title="Daily Tour")
        daily = Rule.objects.create(frequency = "DAILY")
        self.tour_generator = ExampleGenerator.objects.create(event=self.tour, start=datetime.datetime(2011,1,1,10,0), _duration=60, rule=daily, repeat_until=datetime.date(2011,1,30))

        #when Anna is on holiday on the first day in May, Glen does the daily tour. These are not separately listed.
        self.glen_tour = ExampleEvent.tree.create(parent=self.tour, title="Glen's Daily Tour")
        occs = self.tour.occurrences.all()[6:10]
        for occ in occs:
            occ.event = self.glen_tour
            occ.save()

        #SCENARIO 2: Template/instance
        #there is a template for artist talks. Should not be listed as an event.
        self.talks = ExampleEvent.tree.create(title="Artist Talks")

        #one example is a talk by John Smith. Listed as an event.
        self.talk1 = ExampleEvent.tree.create(parent=self.talks, title="Artist Talk: John Smith")
        ExampleOccurrence.objects.create(event=self.talk1, start=datetime.datetime(2011,8,28, 19,0), _duration=30)
        ExampleOccurrence.objects.create(event=self.talk1, start=datetime.datetime(2011,8,29, 19,0), _duration=30)

        #another example is a talk by Jane Doe. Listed as an event.
        self.talk2 = ExampleEvent.tree.create(parent=self.talks, title="Artist Talk: Jane Doe")
        ExampleOccurrence.objects.create(event=self.talk2, start=datetime.datetime(2011,8,30, 19,0), _duration=30)

        #One of Jane's talks is with her husband Barry.
        self.talk2a = ExampleEvent.tree.create(parent=self.talk2, title="Artist Talk: Jane and Barry Doe")
        ExampleOccurrence.objects.create(event=self.talk2a, start=datetime.datetime(2011,8,31, 19,0), _duration=30)

        #have to reload stuff so that the mptt-inserted lft,rght values are given.
        self.talks = self.talks.reload()
        self.talk1 = self.talk1.reload()
        self.talk2 = self.talk2.reload()
        self.talk2a = self.talk2a.reload()


    def test_queries(self):
        #the private listing should show all events
        self.ae(ExampleEvent.tree.count(), 6)

        #the public events listing should only show the daily tour event, and the two artist talks.
        qs = ExampleEvent.eventobjects.in_listings()
        self.ae(qs.count(), 3)
        self.ae(set(list(qs.filter())), set([self.talk1, self.talk2, self.tour]))

        #the 'direct' occurrences of an event are default and direct
        self.ae(self.tour.occurrences.count(), 26)
        self.ae(self.glen_tour.occurrences.count(), 4)
        self.ae(self.talks.occurrences.count(), 0)
        self.ae(self.talk1.occurrences.count(), 2)
        self.ae(self.talk2.occurrences.count(), 1)
        self.ae(self.talk2a.occurrences.count(), 1)

        #the 'listing' occurrences are the occurrences of and event and those of its children.
        self.ae(self.tour.occurrences_in_listing().count(), 30)
        self.ae(self.glen_tour.occurrences_in_listing().count(), 4)
        self.ae(self.talks.occurrences_in_listing().count(), 4)
        self.ae(self.talk1.occurrences_in_listing().count(), 2)
        self.ae(self.talk2.occurrences_in_listing().count(), 2)
        self.ae(self.talk2a.occurrences_in_listing().count(), 1)

    def test_methods(self):
        #an event knows the event it is listed under
        self.ae(self.tour.listed_under(), self.tour)
        self.ae(self.glen_tour.listed_under(), self.tour)
        self.ae(self.talks.listed_under(), None) #isn't listed
        self.ae(self.talk1.listed_under(), self.talk1)
        self.ae(self.talk2.listed_under(), self.talk2)
        self.ae(self.talk2a.listed_under(), self.talk2)

    def test_generation(self):
        # updating the generator for an event should not cause the regenerated Occurrences to be reassigned to that event.
        # the occurrences should be updated though, since they are still attached to the generator
        self.tour_generator.start=datetime.datetime(2011,1,1,10,30)
        self.tour_generator.save()

        self.ae(self.tour.occurrences.count(), 26)
        self.ae(self.glen_tour.occurrences.count(), 4)

        [self.ae(o.start.time(), datetime.time(10,30)) for o in self.tour.occurrences.all()]
        [self.ae(o.start.time(), datetime.time(10,30)) for o in self.glen_tour.occurrences.all()]