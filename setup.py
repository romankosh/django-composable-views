from setuptools import setup

setup(
    name='django-composable-views',
    version='0.1.0',
    url='https://gitlab.com/preusx/django-composable-views',
    install_requires=[
        'Django >=1.9',
    ],
    description="Composable class-based views for Django",
    long_description=open('README.rst', 'r').read(),
    license="MIT",
    author="Alex Tkachenko",
    author_email="preusx@gmail.com",
    packages=['composable_views'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ]
)
