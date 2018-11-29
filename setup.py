#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
doclink = """
Documentation
-------------

The full documentation is at http://pyelucidate.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='pyelucidate',
    version='0.1.0',
    description='Open Source Python Tools for the Elucidate Annotation Server.',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='Matt McGrattan',
    author_email='matt.mcgrattan@digirati.com',
    url='https://github.com/mattmcgrattan/pyelucidate',
    packages=[
        'pyelucidate',
    ],
    package_dir={'pyelucidate': 'pyelucidate'},
    include_package_data=True,
    install_requires=[
    ],
    license='MIT',
    zip_safe=False,
    keywords='pyelucidate',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
