"""
From http://fragmentsofcode.wordpress.com/2009/02/24/django-fully-qualified-url/

This is used by eventtools to get absolute URLs for ics files

- to go into glamkit-convenient someday?
"""

from django.conf import settings

def current_site_url():
    """Returns fully qualified URL (no trailing slash) for the current site."""
    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()
    protocol = getattr(settings, 'SITE_PROTOCOL', 'http')
    port     = getattr(settings, 'SITE_PORT', '')
    url = '%s://%s' % (protocol, current_site.domain)
    if port:
        url += ':%s' % port
    return url
    
def django_root_url(fq=True):
    """Returns base URL (no trailing slash) for the current project.

    Setting fq parameter to a true value will prepend the base URL
    of the current site to create a fully qualified URL.

    The name django_root_url is used in favor of alternatives
    (such as project_url) because it corresponds to the mod_python
    PythonOption django.root setting used in Apache.
    """
    url = getattr(settings, 'DJANGO_URL_PATH', '')
    if fq:
        url = current_site_url() + url
    return url