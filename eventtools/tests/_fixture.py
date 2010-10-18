from eventtools_testapp.models import *
from datetime import datetime, date, timedelta
from dateutil.relativedelta import *
from eventtools.utils.dateranges import *

def fixture(self):
    self.gallery = Venue.objects.create(name="Gallery A", slug="gallery-A")
    self.auditorium = Venue.objects.create(name="Auditorium", slug="auditorium")
    self.cinema_1 = Venue.objects.create(name="Cinema 1", slug="cinema-1")
    self.cinema_2 = Venue.objects.create(name="Cinema 2", slug="cinema-2")
    
    #some simple events
    self.talk = Event.objects.create(name="Curator's Talk", venue=self.gallery)
    self.performance = Event.objects.create(name="A performance", venue=self.auditorium)
    
    #some useful dates
    self.day1 = date(2010,10,10)
    self.day2 = self.day1+timedelta(1)

    #some simple occurrences
    self.talk_morning = Occurrence.objects.create(event=self.talk, start=datetime(2010,10,10,10,00))
    self.talk_afternoon = Occurrence.objects.create(event=self.talk, start=datetime(2010,10,10,14,00))
    self.talk_tomorrow_morning_cancelled = Occurrence.objects.create(event=self.talk, start=datetime(2010,10,11,10,00), status='cancelled')

    self.performance_evening = Occurrence.objects.create(event=self.performance, start=datetime(2010,10,10,20,00))
    self.performance_tomorrow = Occurrence.objects.create(event=self.performance, start=datetime(2010,10,11,20,00))
    self.performance_day_after_tomorrow = Occurrence.objects.create(event=self.performance, start=datetime(2010,10,12,20,00))

    #an event with many occurrences
    # deleting the 2nd jan, because we want to test it isn't displayed
    self.daily_tour = Event.objects.create(name="Daily Tour", slug="daily-tour")
    for day in range(50):
        if day !=2:
            d = date(2010,1,1) + timedelta(day)
            self.daily_tour.occurrences.create(start=d)


    self.weekly_talk = Event.objects.create(name="Weekly Talk", slug="weekly-talk")
    for day in range(50):
        d = date(2010,1,1) + timedelta(day*7)
        self.daily_tour.occurrences.create(start=datetime.combine(d, time(10,00)), end=datetime.combine(d, time(12,00)))


    #an event with some variations
    self.film = Event.objects.create(name="Film Night", venue=self.cinema_1)
    self.film_with_popcorn = Event.objects.create(parent=self.film, name="Film Night", difference_from_parent="free popcorn", venue=self.cinema_1)
    self.film_with_talk = Event.objects.create(parent=self.film, name="Film Night", difference_from_parent="director's talk", venue=self.auditorium)
    self.film_with_talk_and_popcorn = Event.objects.create(parent=self.film_with_talk, name="Film Night", difference_from_parent="popcorn and director's talk", venue=self.cinema_2)
    
    # self.film_with_popcorn.move_to(self.film, position='first-child')
    # self.film_with_talk.move_to(self.film, position='first-child')
    # self.film_with_talk_and_popcorn.move_to(self.film_with_talk, position='first-child')
    # the mptt gotcha. reload the parents
    reload_films(self)
    
    self.film_occ = self.film.occurrences.create(start=datetime(2010,10,10,18,30))
    self.film_occ.save()
    self.film_with_popcorn_occ = self.film_with_popcorn.occurrences.create(start=datetime(2010,10,11,18,30))
    self.film_with_talk_occ = self.film_with_talk.occurrences.create(start=datetime(2010,10,12,18,30))
    self.film_with_talk_and_popcorn_occ = self.film_with_talk_and_popcorn.occurrences.create(start=datetime(2010,10,13,18,30))

def reload_films(self):
    self.film = self.film.reload()
    self.film_with_popcorn = self.film_with_popcorn.reload()
    self.film_with_talk = self.film_with_talk.reload()
    self.film_with_talk_and_popcorn = self.film_with_talk_and_popcorn.reload()
    

def bigfixture(self):
    # have to create some more events since we are working from 'today'.
    self.pe = Event.objects.create(name="proliferating event")

    self.todaynow = datetime.now()

    self.today = date.today()
    self.tomorrow = self.today + timedelta(1)
    self.yesterday = self.today - timedelta(1)
    
    self.this_week = dates_in_week_of(self.today)
    self.last_week = dates_in_week_of(self.today-timedelta(7))
    self.next_week = dates_in_week_of(self.today+timedelta(7))

    self.this_weekend = dates_in_weekend_of(self.today)
    self.last_weekend = dates_in_weekend_of(self.today-timedelta(7))
    self.next_weekend = dates_in_weekend_of(self.today+timedelta(7))

    self.this_fortnight = dates_in_fortnight_of(self.today)
    self.last_fortnight = dates_in_fortnight_of(self.today-timedelta(14))
    self.next_fortnight = dates_in_fortnight_of(self.today+timedelta(14))

    self.this_month = dates_in_month_of(self.today)
    self.last_month = dates_in_month_of(self.today+relativedelta(months=-1))
    self.next_month = dates_in_month_of(self.today+relativedelta(months=+1))

    self.this_year = dates_in_year_of(self.today)
    self.last_year = dates_in_year_of(self.today+relativedelta(years=-1))
    self.next_year = dates_in_year_of(self.today+relativedelta(years=+1))
    
    self.now = datetime.now().time()
    self.hence1 = (datetime.now() + timedelta(seconds=600)).time()
    self.hence2 = (datetime.now() + timedelta(seconds=1200)).time()
    self.earlier1 = (datetime.now() - timedelta(seconds=600)).time()
    self.earlier2 = (datetime.now() - timedelta(seconds=1200)).time()
    
    #on each of the given days, we'll create 5 occurrences:
    #    all day
    #    earlier
    #    hence
    #    current
    #    multiday
    
    present_days = \
        self.this_week + \
        self.this_weekend + \
        self.this_fortnight + \
        self.this_month + \
        self.this_year + \
        [self.today]
        
    past_days = \
        self.last_week + \
        self.last_weekend + \
        self.last_fortnight + \
        self.last_month + \
        self.last_year + \
        [self.yesterday]

    future_days = \
        self.next_week + \
        self.next_weekend + \
        self.next_fortnight + \
        self.next_month + \
        self.next_year + \
        [self.tomorrow]

    for day in present_days + past_days + future_days:
        #all day
        self.pe.occurrences.create(start=day)
        # earlier
        self.pe.occurrences.create(start=datetime.combine(day, self.earlier2), end=datetime.combine(day, self.earlier1))
        # later
        self.pe.occurrences.create(start=datetime.combine(day, self.hence1), end=datetime.combine(day, self.hence2))
        # now-ish
        self.pe.occurrences.create(start=datetime.combine(day, self.earlier1), end=datetime.combine(day, self.hence1))
        # multiday
        self.pe.occurrences.create(start=datetime.combine(day, self.earlier1), end=datetime.combine(day+timedelta(1), self.hence1))