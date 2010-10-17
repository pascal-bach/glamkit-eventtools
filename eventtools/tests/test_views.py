"""
An occurrence has a pURL based on its id. Anything after a + sign is ignored, allowing eg. slug to be used in the URL.

You can view a page for an occurrence.

The page uses hCalendar microformat.

You can view an ical for an occurrence.

You can view a paginated list of occurrences for an event qs, following a given day, using ?startdate=2010-10-22&page=2.

Each page shows n=20 occurrences

The occurrences are grouped by day (and thus a day's occurrences may span several pages).

The occurrences are in chronological order.

If there are no events in a given day, the day is not shown.

You can show all occurrences between two days on one page, by adding ?enddate=2010-10-24. Pagination adds or subtracts the difference in days to the range.

If there are no events in a given page, a 'no events match' message is shown.

For some ranges, pagination is by a different amount:
Precisely a month (paginate by month)
Precisely a year (paginate by year)

You can view an ical for a collection of occurrences.
(TODO: do large icals perform well? If not we might have to make it a feed.)

You can view an RSS feed for an iterable of occurrences.

CALENDAR

A template tag shows a calendar of eventoccurrences in a given month.

Calendar's html gives classes for 'today', 'date selection', 'has_events', 'no_events', 'prev_month' 'next_month'.

Calendar optionally shows days.

Calendar optionally hides leading or trailing empty weeks.

Calendar can optionally navigate to prev/next months, which set a start_date to the 1st of the next month.



API (TODO)

"""