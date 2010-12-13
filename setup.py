#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
 
setup(
    name='glamkit-eventtools',
    version='2.0.0a1',
    description='An event management app for Django.',
    author='Thomas Ashelford',
    author_email='thomas@interaction.net.au',
    url='http://github.com/glamkit/glamkit-eventtools',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Utilities'],
    install_requires=['setuptools', 'vobject', 'python-dateutil', 'django-mptt'],
    license='BSD',
    test_suite = "eventtools.tests",
)

# also requires glamkit-convenient
# pip install -e git+git://github.com/glamkit/glamkit-convenient.git#egg=convenient
# JSONfield
# pip install -e git+git://github.com/ixc/django-jsonfield.git#egg=jsonfield
