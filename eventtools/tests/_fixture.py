from dateutil.relativedelta import *
from eventtools.models import Rule
from eventtools_testapp.models import *
from eventtools.utils.dateranges import *
from datetime import datetime, date, timedelta

def fixture(obj):
    obj.gallery = ExampleVenue.objects.create(name="Gallery A", slug="gallery-A")
    obj.auditorium = ExampleVenue.objects.create(name="Auditorium", slug="auditorium")
    obj.cinema_1 = ExampleVenue.objects.create(name="Cinema 1", slug="cinema-1")
    obj.cinema_2 = ExampleVenue.objects.create(name="Cinema 2", slug="cinema-2")
    
    #some simple events
    obj.talk = ExampleEvent.eventobjects.create(title="Curator's Talk", slug="curators-talk", venue=obj.gallery)
    obj.performance = ExampleEvent.eventobjects.create(title="A performance", slug="performance", venue=obj.auditorium)
    
    #some useful dates
    obj.day1 = date(2010,10,10)
    obj.day2 = obj.day1+timedelta(1)

    #some simple occurrences
    obj.talk_morning = ExampleOccurrence.objects.create(event=obj.talk, start=datetime(2010,10,10,10,00))
    obj.talk_afternoon = ExampleOccurrence.objects.create(event=obj.talk, start=datetime(2010,10,10,14,00))
    obj.talk_tomorrow_morning_cancelled = ExampleOccurrence.objects.create(event=obj.talk, start=datetime(2010,10,11,10,00), status='cancelled')

    obj.performance_evening = ExampleOccurrence.objects.create(event=obj.performance, start=datetime(2010,10,10,20,00))
    obj.performance_tomorrow = ExampleOccurrence.objects.create(event=obj.performance, start=datetime(2010,10,11,20,00))
    obj.performance_day_after_tomorrow = ExampleOccurrence.objects.create(event=obj.performance, start=datetime(2010,10,12,20,00))

    #an event with many occurrences
    # deleting the 2nd jan, because we want to test it isn't displayed
    obj.daily_tour = ExampleEvent.eventobjects.create(title="Daily Tour", slug="daily-tour")
    for day in range(50):
        if day !=1: #2nd of month.
            d = date(2010,1,1) + timedelta(day)
            obj.daily_tour.occurrences.create(start=d)


    obj.weekly_talk = ExampleEvent.eventobjects.create(title="Weekly Talk", slug="weekly-talk")
    for day in range(50):
        d = date(2010,1,1) + timedelta(day*7)
        obj.weekly_talk.occurrences.create(start=datetime.combine(d, time(10,00)), _duration=240)


    #an event with some variations
    obj.film = ExampleEvent.eventobjects.create(title="Film Night", slug="film-night", venue=obj.cinema_1)
    obj.film_with_popcorn = ExampleEvent.eventobjects.create(parent=obj.film, title="Film Night", slug="film-night-2", difference_from_parent="free popcorn", venue=obj.cinema_1)
    obj.film_with_talk = ExampleEvent.eventobjects.create(parent=obj.film, title="Film Night", slug="film-night-talk", difference_from_parent="director's talk", venue=obj.auditorium)
    obj.film_with_talk_and_popcorn = ExampleEvent.eventobjects.create(parent=obj.film_with_talk, title="Film Night", slug="film-with-talk-and-popcorn", difference_from_parent="popcorn and director's talk", venue=obj.cinema_2)
    
    # obj.film_with_popcorn.move_to(obj.film, position='first-child')
    # obj.film_with_talk.move_to(obj.film, position='first-child')
    # obj.film_with_talk_and_popcorn.move_to(obj.film_with_talk, position='first-child')
    # the mptt gotcha. reload the parents
    reload_films(obj)
    
    obj.film_occ = obj.film.occurrences.create(start=datetime(2010,10,10,18,30))
    obj.film_occ.save()
    obj.film_with_popcorn_occ = obj.film_with_popcorn.occurrences.create(start=datetime(2010,10,11,18,30))
    obj.film_with_talk_occ = obj.film_with_talk.occurrences.create(start=datetime(2010,10,12,18,30))
    obj.film_with_talk_and_popcorn_occ = obj.film_with_talk_and_popcorn.occurrences.create(start=datetime(2010,10,13,18,30))

def generator_fixture(obj):
    #TestEvents with generators (separate models to test well)
    obj.weekly = Rule.objects.create(frequency = "WEEKLY")
    obj.daily = Rule.objects.create(frequency = "DAILY")
    obj.yearly = Rule.objects.create(frequency = "YEARLY")
    obj.bin_night = ExampleEvent.eventobjects.create(title='Bin Night')
    
    obj.weekly_generator = obj.bin_night.generators.create(start=datetime(2010,1,8,10,30), _duration=60, rule=obj.weekly, repeat_until=date(2010,2,5))
    #this should create 0 occurrences, since it is a duplicate of weekly.
    obj.dupe_weekly_generator = obj.bin_night.generators.create(start=datetime(2010,1,8,10,30), _duration=60, rule=obj.weekly, repeat_until=date(2010,2,5))

    obj.endless_generator = obj.bin_night.generators.create(start=datetime(2010,1,2,10,30), _duration=60, rule=obj.weekly)

    obj.all_day_generator = obj.bin_night.generators.create(start=datetime(2010,1,4,0,0), rule=obj.weekly, repeat_until=date(2010,1,25))
    
def reload_films(obj):
    obj.film = obj.film.reload()
    obj.film_with_popcorn = obj.film_with_popcorn.reload()
    obj.film_with_talk = obj.film_with_talk.reload()
    obj.film_with_talk_and_popcorn = obj.film_with_talk_and_popcorn.reload()
    

def bigfixture(obj):
    # have to create some more events since we are working from 'today'.
    obj.pe = ExampleEvent.eventobjects.create(title="proliferating event")

    obj.todaynow = datetime.now()

    obj.today = date.today()
    obj.tomorrow = obj.today + timedelta(1)
    obj.yesterday = obj.today - timedelta(1)
    
    obj.this_week = dates_in_week_of(obj.today)
    obj.last_week = dates_in_week_of(obj.today-timedelta(7))
    obj.next_week = dates_in_week_of(obj.today+timedelta(7))

    obj.this_weekend = dates_in_weekend_of(obj.today)
    obj.last_weekend = dates_in_weekend_of(obj.today-timedelta(7))
    obj.next_weekend = dates_in_weekend_of(obj.today+timedelta(7))

    obj.this_fortnight = dates_in_fortnight_of(obj.today)
    obj.last_fortnight = dates_in_fortnight_of(obj.today-timedelta(14))
    obj.next_fortnight = dates_in_fortnight_of(obj.today+timedelta(14))

    obj.this_month = dates_in_month_of(obj.today)
    obj.last_month = dates_in_month_of(obj.today+relativedelta(months=-1))
    obj.next_month = dates_in_month_of(obj.today+relativedelta(months=+1))

    obj.this_year = dates_in_year_of(obj.today)
    obj.last_year = dates_in_year_of(obj.today+relativedelta(years=-1))
    obj.next_year = dates_in_year_of(obj.today+relativedelta(years=+1))
    
    obj.now = datetime.now().time()
    obj.hence1 = (datetime.now() + timedelta(seconds=600)).time()
    obj.hence2 = (datetime.now() + timedelta(seconds=1200)).time()
    obj.earlier1 = (datetime.now() - timedelta(seconds=600)).time()
    obj.earlier2 = (datetime.now() - timedelta(seconds=1200)).time()
    
    #on each of the given days, we'll create 5 occurrences:
    #    all day
    #    earlier
    #    hence
    #    current
    #    multiday
    
    present_days = \
        obj.this_week + \
        obj.this_weekend + \
        obj.this_fortnight + \
        obj.this_month + \
        obj.this_year + \
        [obj.today]
        
    past_days = \
        obj.last_week + \
        obj.last_weekend + \
        obj.last_fortnight + \
        obj.last_month + \
        obj.last_year + \
        [obj.yesterday]

    future_days = \
        obj.next_week + \
        obj.next_weekend + \
        obj.next_fortnight + \
        obj.next_month + \
        obj.next_year + \
        [obj.tomorrow]

    for day in present_days + past_days + future_days:
        #all day
        obj.pe.occurrences.create(start=day)
        # earlier
        obj.pe.occurrences.create(start=datetime.combine(day, obj.earlier2), end=datetime.combine(day, obj.earlier1))
        # later
        obj.pe.occurrences.create(start=datetime.combine(day, obj.hence1), end=datetime.combine(day, obj.hence2))
        # now-ish
        obj.pe.occurrences.create(start=datetime.combine(day, obj.earlier1), end=datetime.combine(day, obj.hence1))
        # multiday
        obj.pe.occurrences.create(start=datetime.combine(day, obj.earlier1), end=datetime.combine(day+timedelta(1), obj.hence1))