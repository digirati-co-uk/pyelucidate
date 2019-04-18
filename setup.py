#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    sys.exit()

readme = open("README.rst").read()
doclink = """
Documentation
-------------

The full documentation is at https://pyelucidate.readthedocs.io."""
history = open("HISTORY.rst").read().replace(".. :changelog:", "")

setup(
    name="pyelucidate",
    version="0.3.2",
    description="Open Source Python Tools for the Elucidate Annotation Server.",
    long_description=readme + "\n\n" + doclink + "\n\n" + history,
    author="Matt McGrattan",
    author_email="matt.mcgrattan@digirati.com",
    url="https://github.com/digirati-co-uk/pyelucidate",
    packages=["pyelucidate"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    package_dir={"pyelucidate": "pyelucidate"},
    include_package_data=True,
    install_requires=["aiohttp>=3.4.4", "requests>=2.20.1"],
    license="MIT",
    zip_safe=False,
    keywords="pyelucidate",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
