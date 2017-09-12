import os
from setuptools import setup, find_packages


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

pkj_name = 'composable_views'


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
    test_suite="runtests.runtests",
    description="Composable class-based views for Django",
    long_description=open('README.rst', 'r').read(),
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
