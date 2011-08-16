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
    def setUp(self):
        super(TestExclusions, self).setUp()
        generator_fixture(self)
    
    def test_generation_then_exclusion(self):
        """
        If an Exclusion is saved, then:
        
        * Generated Occurrences that should be excluded are converted to manual.
        * Re-generating from generators will not re-generate that occurrence.
        """
        
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
        
        # no ecxluded occurrence is (re)generated
        self.ae(self.bin_night.occurrences.filter(start = clashingtime).count(), 0)

    def test_clash(self):
        """
        If we create a manual occurrence that clashes
            * event + start-time is unique, so it must be added as an exception
            first.
            * the manual occurrence shouldn't be generated.
        """
        
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
        be unhooked.
        """
        
        clashingtime = datetime(2010,1,8,11,00)
        self.exclusion = self.bin_night.exclusions.create(
            start = clashingtime
        )

        #update start time
        self.weekly_generator.event_start=datetime(2010,1,1,11,00)
        self.weekly_generator.save()
        
        self.assertTrue(
            self.bin_night.occurrences.get(
                start = clashingtime
            ).generated_by == None)
        