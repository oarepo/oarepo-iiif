# -*- coding: utf-8 -*-
"""Setup module for elasticsearch mapping includes."""
import os

from setuptools import setup

readme = open('README.md').read()
OAREPO_VERSION = os.environ.get('OAREPO_VERSION', '3.3.0')

install_requires = [
    'invenio-iiif'
]

tests_require = [
    'oarepo[tests]~={version}'.format(version=OAREPO_VERSION)
]

g = {}
with open(os.path.join('oarepo_iiif', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name="oarepo-iiif",
    version=version,
    url="https://github.com/oarepo/oarepo-iiif",
    license="MIT",
    author="Miroslav Simek",
    author_email="miroslav.simek@vscht.cz",
    description="Extra sources for IIIF server, not only images",
    long_description=readme,
    long_description_content_type='text/markdown',
    zip_safe=False,
    packages=['oarepo_iiif'],
    entry_points={
        'invenio_base.apps': [
            'oarepo_iiif = oarepo_iiif.ext:OARepoIIIFExt'
        ],
        'invenio_base.api_apps': [
            'oarepo_iiif = oarepo_iiif.ext:OARepoIIIFExt'
        ]
    },
    include_package_data=True,
    setup_requires=install_requires,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'tests': tests_require
    },
    platforms='any',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Development Status :: 4 - Beta',
    ],
)
