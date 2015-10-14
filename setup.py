"""Farcy setup.py."""

import os
import re
from setuptools import setup

PACKAGE_NAME = 'landa'

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, PACKAGE_NAME, 'const.py')) as fp:
    VERSION = re.search("__version__ = '([^']+)'", fp.read()).group(1)


setup(name=PACKAGE_NAME,
      author='Paulus Schoutsen',
      author_email='paulus@paulusschoutsen.nl',
      classifiers=['Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4'],
      description='Label impactful github pull requests',
      entry_points={'console_scripts':
                    ['{0} = {0}:main'.format(PACKAGE_NAME)]},
      install_requires=['docopt >= 0.6.2',
                        'github3.py >= 1.0.0a2'],
      keywords=['code review', 'pull request'],
      license='Simplified BSD License',
      packages=[PACKAGE_NAME],
      tests_require=['mock >= 1.0.1'],
      test_suite='test',
      url='https://github.com/balloob/landa',
      version=VERSION)
