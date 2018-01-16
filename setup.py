import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.txt')
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
    'Detailed Documentation\n'
    '======================\n'
    + '\n' +
    read('src', 'hurry', 'workflow', 'workflow.txt')
    + '\n' +
    'Download\n'
    '========\n'
    )

setup(
    name="hurry.workflow",
    version='3.0.2',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['hurry'],
    package_data={
        '': ['*.txt', '*.zcml'],
    },
    zip_safe=False,
    author='Martijn Faassen (at Infrae)',
    author_email='faassen@startifact.com',
    description=(
        "hurry.workflow is a simple workflow system. It can be used to "
        "implement stateful multi-version workflows for Zope Toolkit "
        "applications."),
    long_description=long_description,
    license='ZPL2.1',
    keywords="zope zope3",
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Framework :: Zope3',
        ],
    extras_require=dict(
        test=[],
    ),
    install_requires=[
        'setuptools',
        'zope.interface',
        'zope.component',
        'zope.event',
        'zope.security',
        'zope.annotation',
        'zope.lifecycleevent'
    ],
    )
