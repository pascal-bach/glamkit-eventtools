=======================
GLAMkit-events Overview
=======================

Different institutions have event calendars of differing complexity. GLAMkit-events attempts to cover all the possible scenarios. Before developing with GLAMkit-events, you should spend some time determining what sort of events structure you need to model.


Events, Occurrences and OccurrenceGenerators
--------------------------------------------

GLAMkit-events draws a distinction between **events**, and **occurrences** of those events. **Events** contain all the information *except* for the times and dates. **Events** know where, why and how things happen, but not when. **Occurrences** contain all the *when* information. By combining the two, you can specify individual occurrences of an event.

Many institutions have repeating events, ie Occurrences that happen at the same time every day, or week, or according to some other rule. These Occurrences are created with a **Generator**. The best way to grasp this is with an example:

    Imagine a museum that has a tour for the blind every Sunday at 2pm. The tour always starts at the same place, costs the same amount etc. The only thing that changes is the date. You can define an event model which has field for storing all the non-time information. You can use a Generator to specify that the tour starts next Sunday at 2pm and repeats every week after. When you save the Generator, it generates an Occurrence instance for each specific instance of the tour.
    
This separation into three models allows us to do some very cool things:

* we can specify complex repetition rules (eg. every Sunday at 2pm, unless it happens to be Easter Sunday, or Christmas day);
* we can attach multiple Generators to the same event (eg. the same tour might also happen at 11am every weekday, except during December and January);
* we can specify an end date for these repetition rules, or have them repeat infinitely (although since we can't store an infinite number of occurrences, we only generate a year into the futue. This is a setting which can be changed);

Umbrella events and event variations
------------------------------------

Organisations which organise events are familiar with the notion of some events 'belonging to' other umbrella events. For example, a film night may contain several screenings. A film festival may contain several film nights.

Furthermore, some events may be special one-off variations of other events. For example, a monthly series of film screenings may have the same overall information every month, but different films. Or a film that shows every night in a month might have a directors' talk one night.

Both of these things can be modelled by arranging events in a tree. Events know about their parent events and child events, and this information can be used in a template.

An example arrangement might look like this:

    Australian film festival
    |---Mad Max Trilogy
        |---Screening: Mad Max
        |---Screening: Mad Max II
        |---Screening: Mad Max: Beyond Thunderdrome
    |---Red Curtain Trilogy
        |---Screening: Moulin Rouge
        |---Screening: Strictly Ballroom
        |---Screening: Romeo and Juliet
            |---Screening: Romeo and Juliet with Director's talk

Exclusions
----------

An Exclusion is a way to prevent an Occurrence from being created by a Generator. You might want to do this if there is a one-off exclusion to a repeating occurrence.

For example, if a film is on every night for a month, but on one night there is a director's talk, then the Event arrangement is:

    Film <-- has an Occurrence Generator that repeats daily for a month
    |---Film with director's talk <-- has a one-off Occurrence
    
This will result in two occurrences on the night of the director's talk, one for the Film, and one for the Film with director's talk. In this case, you'd add an Exclusion for the Film on that night.

If an Occurrence that should be excluded has already been generated, it is not deleted, because there may be other information (e.g. ticket sales) attached. Instead, it is converted into a 'manual' occurrence, so the events administrator can decide whether to delete or change the occurrence.