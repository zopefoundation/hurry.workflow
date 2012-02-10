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
    '**********************\n'
    + '\n' +
    read('src', 'hurry', 'workflow', 'workflow.txt')
    + '\n' +
    'Download\n'
    '********\n'
    )

setup(
    name="hurry.workflow",
    version='0.12',
    packages=find_packages('src'),
    
    package_dir= {'':'src'},
    
    namespace_packages=['hurry'],
    package_data = {
    '': ['*.txt', '*.zcml'],
    },

    zip_safe=False,
    author='Martijn Faassen (at Infrae)',
    author_email='faassen@startifact.com',
    description="""\
hurry.workflow is a simple workflow system. It can be used to
implement stateful multi-version workflows for Zope Toolkit applications.
""",
    long_description=long_description,
    license='ZPL 2.1',
    keywords="zope zope3",
    classifiers = ['Framework :: Zope3'],
    extras_require = dict(
        test = ['zope.testing'],
        ),
    install_requires=[
        'setuptools',
        'zope.interface',
        'zope.component',
        # this is an indirect dependency through zope.annotation, but
        # this at the time of working didn't yet declare this
        # dependency itself
        'ZODB3',
        'zope.event',
        'zope.security',
        'zope.annotation',
        'zope.lifecycleevent'],
    )
