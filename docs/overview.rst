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

Event variations
----------------

Organisations which organise events are familiar with the notion of some events  being special one-off variations of other events. For example, a monthly series of film screenings may have the same overall information, but different films each month. Or a film that shows every night in a month might have a directors' talk one night.

(Note: it might be tempting to use the tree arrangement for 'parent events' e.g. Festivals, and events which are part of the festival. In our experience, events and their 'parents' are rarely in a strict tree arrangement, so we use another many-to-many relation between a model which represents Events, and a model which represents parent events, or event series. Depending on your arrangement, an umbrella event may be another Event, or another model entirely.)

In Eventtools, Event variations are modelled by arranging events in a tree, with 'template' events (with no occurrences) higher in the tree, and 'actual' events (with occurrences) lower in the tree.

An example arrangement might look like this:

    Screening
    |---Outdoor Screening
        |---Mad Max
            |---Mad Max II
        |---Red Curtain
            |---Moulin Rouge
            |---Strictly Ballroom
            |---Romeo and Juliet
                |---Romeo and Juliet with Director's talk

Variation events can automatically inherit some attributes from template events.

To define inherited fields, declare an EventMeta class in your Event model:

    class Event(EventModel):
        ...
    
        class EventMeta:
            fields_to_inherit = ('description', 'price', 'booking_info')
        ...     

This results in the following:

    * Changes to the parent model 'cascade' to child models, unless the child model already has a different value.
    * When you view an event, it shows the 'diff' of the child event from its parent
    * When you create a child event by clicking 'create child event', the values in the admin form are pre-populated.


Exclusions
----------

An Exclusion is a way to prevent an Occurrence from being created by a Generator. You might want to do this if there is a one-off exclusion to a repeating occurrence.

For example, if a film is on every night for a month, but on one night there is a director's talk, then the Event arrangement is:

    Film    <-- has an Occurrence Generator that repeats daily for a month
    |---Film with director's talk   <-- has a one-off Occurrence
    
This will result in two occurrences on the night of the director's talk, one for the Film, and one for the Film with director's talk. In this case, you'd add an Exclusion for the Film on that night.

If an Occurrence that should be excluded has already been generated, it is not deleted, because there may be other information (e.g. ticket sales) attached. Instead, it is converted into a 'manual' occurrence, so the events administrator can decide whether to delete or change the occurrence.