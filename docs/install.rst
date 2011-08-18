.. _ref-install:

================
Getting The Code
================

The project is available through `Github <http://github.com/glamkit/glamkit-eventtools/>`_.

.. _ref-configure:

=============
Configuration
=============

Installation
------------

0. Download the code; put it into your project's directory or run ``python setup.py install`` to install to your envirnoment.

1. Install the requirements (using pip).

    pip install -e REQUIREMENTS.txt

2. Create an `events` app, where you will define what Events look like for your project.

    ./manage.py startapp events

The app doesn't have to be called `events`, but it will make the rest of these
instructions easier to follow.

Settings.py
-----------

3. List the required applications in the ``INSTALLED_APPS`` portion of your settings
   file.  Your settings file might look something like::
   
       INSTALLED_APPS = (
           # ...
           'mptt'
           'eventtools',
           'events', # the name of your app.
       )

4. Install the pagination middleware.  Your settings file might look something
   like::
   
       MIDDLEWARE_CLASSES = (
           # ...
           'pagination.middleware.PaginationMiddleware',
       )

Models Definition
-----------------

5. Define models in your new app. We suggest calling the Event model 'Event'
to easily use the provided templates. In ``events/models.py``:

    from django.db import models
    from eventtools.models import EventModel, OccurrenceModel, GeneratorModel #, ExclusionModel

    class Event(EventModel):
        teaser = models.TextField(blank=True)
        image = models.ImageField(upload_to="events_uploads", blank=True)
        #etc

    class Generator(GeneratorModel):
        event = models.ForeignKey(Event, related_name="generators")

    class Occurrence(OccurrenceModel):
        event = models.ForeignKey(Event, related_name="occurrences")
        generated_by = models.ForeignKey(Generator, blank=True, null=True, related_name="occurrences")

    class Exclusion(ExclusionModel):
        event = models.ForeignKey(Event, related_name="exclusions")

Admin
-----

6. Set up admin. In ``events/admin.py``:

    from django.contrib import admin
    from eventtools.admin import EventAdmin
    from .models import Event

    admin.site.register(Event, EventAdmin(Event))
    
Views and URLs
--------------
    
7. Set up view URLs. In ``events/urls.py``

    from django.conf.urls.defaults import *
    from eventtools.views import EventViews
    from .models import Event

    views = EventViews(event_qs=Event.eventobjects.all())

    urlpatterns = patterns('',
        url(r'^', include(views.urls)),
    )
    
8. In your main ``urls.py``:

    urlpatterns += patterns('',
        url(r'^events/', include('events.urls')),    
    )
   
Nearly there
------------
    
8. syncdb/migrate, then collectstatic

9. try it! Visit http://yourserver/events/