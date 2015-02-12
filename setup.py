from distutils.core import setup

install_requires = [
    'requests',
]


setup(
  name = 'sloop',
  packages = ['sloop'], # this must be the same as the name above
  version = '0.2.1',
  description = 'Django package of the sloop push notification service',
  author = 'H. Yigit Guler',
  author_email = 'yigit@hipolbs.com',
  url = 'https://github.com/hipo/django-sloop', # use the URL to the github repo
  keywords='django, push',
  classifiers = [],
  install_requires=install_requires,

)

