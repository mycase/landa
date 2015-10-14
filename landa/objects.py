"""Defines the standard objects used by Farcy."""

try:
    from configparser import ConfigParser  # PY3
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser  # PY2

from datetime import timedelta, tzinfo
import logging
import os
from .const import CONFIG_DIR
from .exceptions import LandaException
from .helpers import get_session, parse_bool, parse_set


class Config(object):

    """Holds configuration for Farcy."""

    ATTRIBUTES = {'debug', 'log_level', 'author_team', 'label_pattern', 'pull_requests'}
    INT_ATTRS = {'start_event'}
    LOG_LEVELS = {'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'}
    PATH = os.path.join(CONFIG_DIR, 'landa.conf')

    @property
    def log_level_int(self):
        """Int value of the log level."""
        return getattr(logging, self.log_level)

    @property
    def session(self):
        """Return GitHub session. Create if necessary."""
        if self._session is None:
            self._session = get_session()
        return self._session

    def __init__(self, repository, **overrides):
        """Initialize a config with default values."""
        self._session = None
        self.repository = repository
        self.set_defaults()
        self.load_config_file()
        self.override(**overrides)

    def __repr__(self):
        """String representation of the config."""
        keys = sorted(x for x in self.__dict__ if not x.startswith('_')
                      and x != 'repository')
        arg_fmt = ', '.join(['{0}={1!r}'.format(key, getattr(self, key))
                             for key in keys])
        return 'Config({0!r}, {1})'.format(self.repository, arg_fmt)

    def __setattr__(self, attr, value):
        """
        Set new config attribute.

        Validates new attribute values and tracks if changed from default.

        """
        if attr == 'debug' and parse_bool(value):
            # Force log level when in debug mode
            setattr(self, 'log_level', 'DEBUG')
        elif attr == 'pull_requests':
            if value is not None:
                value = parse_set(value)
        elif attr == 'log_level' and self.debug:
            return  # Don't change level in debug mode
        elif attr == 'log_level' and value is not None:
            value = value.upper()
            if value not in self.LOG_LEVELS:
                raise LandaException('Invalid log level: {0}'.format(value))
        elif attr == 'repository' and value is not None:
            repo_parts = value.split('/')
            if len(repo_parts) != 2:
                raise LandaException('Invalid repository: {0}'.format(value))
        elif attr in self.INT_ATTRS:
            if value is not None:
                value = int(value)
        super(Config, self).__setattr__(attr, value)

    def load_config_file(self):
        """Load value overrides from configuration file."""
        if not os.path.isfile(self.PATH):
            return

        config_file = ConfigParser()
        config_file.read(self.PATH)

        if config_file.has_section('author_team'):
            self.author_team = {team: parse_set(authors, normalize=True)
                                for team, authors
                                in config_file.items('author_team')}

        if config_file.has_section('label_pattern'):
            self.label_pattern = {label: pattern for label, pattern
                                  in config_file.items('label_pattern')}

    def override(self, **overrides):
        """Override the config values passed as keyword arguments."""
        for attr, value in overrides.items():
            if attr in self.ATTRIBUTES and value:
                setattr(self, attr, value)

    def set_defaults(self):
        """Set the default config values."""
        self.author_team = {}
        self.debug = False
        self.label_pattern = {}
        self.log_level = 'ERROR'
        self.start_event = None
        self.pull_requests = None


class UTC(tzinfo):

    """Provides a simple UTC timezone class.

    Source: http://docs.python.org/release/2.4.2/lib/datetime-tzinfo.html

    """

    dst = lambda x, y: timedelta(0)
    tzname = lambda x, y: 'UTC'
    utcoffset = lambda x, y: timedelta(0)
