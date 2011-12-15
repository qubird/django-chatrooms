from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='chatrooms',
      version=version,
      description="A django app providing reverse-ajax chat rooms",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        ],
      keywords='django chat ajax',
      author='Vince E. Antignano (@qubird)',
      author_email='',
      url='https://github.com/qubird/django-chatrooms',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=[],
      include_package_data=True,
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
