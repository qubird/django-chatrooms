from setuptools import setup, find_packages
import os

setup(name='django-chatrooms',
      version=__import__('chatrooms').__version__,
      description="A django app providing reverse-ajax chat rooms",
      long_description=open("README.rst").read(),
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        ],
      keywords='django chat ajax',
      author='Vincenzo E. Antignano (@qubird)',
      author_email='',
      url='https://github.com/qubird/django-chatrooms',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      namespace_packages=[],
      zip_safe=False,
      install_requires=[
          'setuptools',
          'gevent',
          'django_load>=1.0',
          'django_polymorphic>=0.2',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
