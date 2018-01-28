import os
from setuptools import setup, find_packages


pkj_name = 'composable_views'


setup(
    name='django-composable-views',
    version='1.0.0',
    url='https://gitlab.com/preusx/django-composable-views',
    install_requires=['django>=1.9'],
    tests_require=['django-nose', 'coverage'],
    test_suite="runtests.runtests",
    description="Composable class-based views for Django",
    long_description=open('README.md', 'r').read(),
    license="MIT",
    author="Alex Tkachenko",
    author_email="preusx@gmail.com",
    packages=[pkj_name] + [pkj_name + '.' + x for x in find_packages(pkj_name)],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ]
)
