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
from django.db import IntegrityError

class TestExclusions(AppTestCase):

    def test_generation_then_exclusion(self):
        """
        If an Exclusion is saved, then:
        
        * Generated Occurrences that should be excluded are converted to manual.
        * Re-generating from generators will not re-generate that occurrence.
        """

        generator_fixture(self)

        clashingtime = datetime(2010,1,8,10,30)
        
        # Check we're starting the occurrence with a generator
        self.existing_occurrence = self.bin_night.occurrences.get(start = clashingtime)
        self.existing_occurrence_id = self.existing_occurrence.id
        self.assertTrue(self.existing_occurrence.generated_by is not None)
        
        #exclude the second occurrence of the weekly_ and endless_generators.
        self.exclusion = self.bin_night.exclusions.create(
            start = clashingtime
        )
        
        # Assert that the clashing occurrence has the same ID, but
        # now has no generator (ie is manual)
        self.existing_occurrence = self.bin_night.occurrences.get(start = clashingtime)
        self.ae(self.existing_occurrence_id, self.existing_occurrence.id)
        self.assertTrue(self.existing_occurrence.generated_by is None)
        
        # delete the clashing occurrence
        self.existing_occurrence.delete()
        
        # Let's re-save the generators
        self.weekly_generator.save()
        self.dupe_weekly_generator.save()
        
        # no excluded occurrence is (re)generated
        self.ae(self.bin_night.occurrences.filter(start = clashingtime).count(), 0)

    def test_clash(self):
        """
        If we create a manual occurrence that clashes
            * event + start-time is unique, so it must be added as an exception
            first.
            * the manual occurrence shouldn't be generated.
        """
        
        generator_fixture(self)

        # Check there is an auto occurrence
        clashingtime = datetime(2010,1,8,10,30)
        auto_occs = self.bin_night.occurrences.filter(start = clashingtime)
        self.ae(auto_occs.count(), 1)
        self.assertTrue(auto_occs[0].generated_by is not None)

        # we can't add another occurrence with a clashing start time.
        self.assertRaises(
            IntegrityError,
            self.bin_night.occurrences.create,
            start = clashingtime
        )
        
        # let's add the Exclusions
        self.exclusion = self.bin_night.exclusions.create(
            start = clashingtime
        )

        # now we should have a manual occurrence
        manual_occ = self.bin_night.occurrences.get(start = clashingtime)
        self.assertTrue(manual_occ.generated_by is None)
        
        # let's delete it:
        manual_occ.delete()
        
        # and now it's OK to create a manual one:
        self.bin_night.occurrences.create(start=clashingtime)
        
        # and if we remove the Exclusion, the generators don't try to generate
        # anything clashing with the manual occurrence
        self.exclusion.delete()
        
        self.weekly_generator.save()
        self.endless_generator.save()
        
        manual_occs = self.bin_night.occurrences.filter(start = clashingtime)
        self.ae(manual_occs.count(), 1)
        self.assertTrue(manual_occs[0].generated_by is None)
        
    def test_timeshift_into_exclusion(self):
        """
        If a generator is modified such that occurrences are timeshifted such
        that an occurrence matches an exclusion, then the occurrence should
        be deleted (or unhooked).
        """
        event = ExampleEvent.objects.create(title="Curator's Talk", slug="curators-talk-1")
        # is on every week for a year
        weekly = Rule.objects.create(frequency = "WEEKLY")
        generator = event.generators.create(start=datetime(2010,1,1, 9,00), _duration=60, rule=weekly, repeat_until=date(2010,12,31))

        # now I buy a ticket to the first occurrence
        ticket = ExampleTicket.objects.create(occurrence=generator.occurrences.all()[0])

        #here is an exclusion (to clash with the ticketed occurrence)
        clashingtime = datetime(2010,1,1,9,05)
        self.exclusion = event.exclusions.create(start = clashingtime)
        #and another to clash with an unticketed occurrence
        clashingtime2 = datetime(2010,1,8,9,05)
        self.exclusion = event.exclusions.create(start = clashingtime2)

        self.ae(event.occurrences.count(), 53)

        #update start time of generator 5 mins
        generator.start=datetime(2010,1,1,9,05)
        generator.save()

        # the first clashing occurrence should still exist, as there are tickets attached
        self.ae(event.occurrences.filter(start = clashingtime).count(), 1)
        self.ae(event.occurrences.get(start = clashingtime).generated_by, None)

        # the second clashing occurrence should no longer exist
        self.ae(event.occurrences.filter(start = clashingtime2).count(), 0)

        # overall, there is one less occurrence
        self.ae(event.occurrences.count(), 52)