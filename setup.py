import os
from setuptools import setup


def requirements_getter(filename):
    result = []

    with open(filename) as f:
        requirements = map(lambda x: x.strip(), f.readlines())

        for requirement in requirements:
            if not requirement.startswith('-r'):
                result.append(requirement)
                continue

            result += requirements_getter(
                os.path.join(os.path.dirname(filename), requirement[2:].strip())
            )

    return result


here = os.path.abspath(os.path.dirname(__file__))


setup(
    name='django-composable-views',
    version='0.1.0',
    url='https://gitlab.com/preusx/django-composable-views',
    install_requires=requirements_getter(
        os.path.join(here, 'requirements.txt')
    ),
    tests_require=requirements_getter(
        os.path.join(here, 'requirements/test.txt')
    ),
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
