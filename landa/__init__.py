"""Landa, a code review bot for github pull requests.

Usage: farcy.py [-D | --logging=LEVEL] [--limit-user=USER...]
                [options] [REPOSITORY]

Options:

  -s ID, --start=ID  The event id to start handling events from.
  -p ID, --pr=ID   Process only the provided pull request(s).
  -D, --debug        Enable debugging mode. Enables all logging output
                     and prevents the posting of comments.
  --logging=LEVEL    Specify the log level* to output.
  -h, --help         Show this screen.
  --version          Show the program's version.
  -u USER, --limit-user=USER          Limit processed pull requests to pull
                                      requests created by USER. This argument
                                      can be provided multiple times, and each
                                      USER token can contain a comma separated
                                      list of users.

* Available log levels:
    https://docs.python.org/3/library/logging.html#logging-levels

"""

from __future__ import print_function
from datetime import datetime
from docopt import docopt
from fnmatch import fnmatch
from requests import ConnectionError
from timeit import default_timer
import logging
import sys
import time

from github3.issues import Issue

from .const import VERSION_STR
from .exceptions import LandaException
from .objects import Config, UTC


def no_handler_debug_factory(duration=3600):
    """Return a function to cache 'No handler for...' messages for an hour."""
    last_logged = {}

    def log(obj, ext):
        now = default_timer()
        if now - last_logged.get(ext, 0) > duration:
            obj.log.debug('No handlers for extension {0}'.format(ext))
        last_logged[ext] = now
    return log


class Landa(object):

    """A bot to automate some code-review processes on GitHub pull requests."""

    EVENTS = {'PullRequestEvent', 'PushEvent'}

    def __init__(self, config):
        """Initialize an instance of Landa that monitors owner/repository."""
        # Configure logging
        self.config = config
        self.log = logging.getLogger(__name__)
        self.log.setLevel(config.log_level_int)

        # Prepare logging
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)8s %(message)s', '%Y/%m/%d %H:%M:%S'))
        self.log.addHandler(handler)
        self.log.info('Logging enabled at level {0}'.format(config.log_level))

        if config.start_event:
            self.start_time = None
            self.last_event_id = int(config.start_event) - 1
        else:
            self.start_time = datetime.now(UTC())
            self.last_event_id = None

        # Initialize the repository to monitor
        self.repo = config.session.repository(
            *self.config.repository.split('/'))
        if self.repo is None:
            raise LandaException('Invalid owner or repository name: {0}'
                                 .format(self.config.repository))

        # Keep track of open pull requests
        self.open_prs = {}
        for pr in self.repo.pull_requests(state='open'):
            self.open_prs[pr.head.ref] = pr

        self.running = False

    def _event_loop(self, itr, events):
        newest_id = None
        for event in itr:
            # Stop when we've already seen something
            if self.last_event_id and int(event.id) <= self.last_event_id \
               or self.start_time and event.created_at < self.start_time:
                break

            self.log.debug('EVENT {eid} {time} {etype} {user}'.format(
                eid=event.id, time=event.created_at, etype=event.type,
                user=event.actor.login))
            newest_id = newest_id or int(event.id)

            # Add relevent events in reverse order
            if event.type in self.EVENTS:
                events.insert(0, event)
        return newest_id

    def events(self):
        """Yield repository events in order."""
        if self.running:
            raise LandaException('Can only enter `events` once.')

        etag = None
        sleep_time = None  # This value will be overwritten.
        self.running = True
        while self.running:
            if sleep_time:  # Only sleep before we're about to make requests.
                time.sleep(sleep_time)

            # Fetch events
            events = []
            itr = self.repo.events(etag=etag)
            try:
                newest_id = self._event_loop(itr, events)
            except ConnectionError as exc:
                self.log.warning('ConnectionError {0}'.format(exc))
                sleep_time = 1
                continue

            etag = itr.etag
            self.last_event_id = newest_id or self.last_event_id

            # Yield events from oldest to newest
            for event in events:
                yield event

            sleep_time = int(itr.last_response.headers.get('X-Poll-Interval',
                                                           sleep_time))

    def handle_pr(self, pr):
        """Provide code review on pull request."""
        self.log.info('Handling PR#{0} by {1}'
                      .format(pr.number, pr.user.login))

        labels = set(team for team, users in self.config.author_team.items()
                     if pr.user.login in users)

        labels.update(
            key for key, pattern in self.config.label_pattern.items()
            for pfile in pr.files() if fnmatch(pfile.filename, pattern))

        if labels:
            self.log.debug('Applying labels to PR#{0}: {1}'.format(pr.number,
                                                                   labels))

            if not self.config.debug:
                # In future use pr.issue(), not released yet in a2
                issue = pr._instance_or_null(
                    Issue, pr._json(pr._get(pr.issue_url), 200))
                issue.add_labels(*labels)

    def PullRequestEvent(self, event):
        """Check commits on new pull requests."""
        pr = event.payload['pull_request']
        action = event.payload['action']
        self.log.debug('PullRequest #{num} {action} on branch {branch}'
                       .format(action=action, branch=pr.head.ref,
                               num=pr.number))
        if action == 'closed':
            if pr.head.ref in self.open_prs:
                del self.open_prs[pr.head.ref]
            else:
                self.log.warning('open_prs did not contain {0}'
                                 .format(pr.head.ref))
        elif action == 'opened':
            self.open_prs[pr.head.ref] = pr
            self.handle_pr(pr)
        elif action == 'reopened':
            self.open_prs[pr.head.ref] = pr

    def PushEvent(self, event):
        """Check push commits only to open pull requests."""
        ref = event.payload['ref']
        assert ref.startswith('refs/heads/')
        pull_request = self.open_prs.get(ref.rsplit('/', 1)[1])
        if pull_request:
            self.handle_pr(pull_request)

    def run(self):
        """Run the bot until ctrl+c is received."""
        if self.config.pull_requests is not None:
            for number in sorted(int(x) for x in self.config.pull_requests):
                # pr = self.repo.pull_request(number)
                # import IPython
                # IPython.embed()
                # if pr.id is None:
                #     print('WTF')
                # print(pr, pr.id, pr.user.login)
                self.handle_pr(self.repo.pull_request(number))
            return

        self.log.info('Monitoring {0}'.format(self.repo.html_url))
        for event in self.events():
            getattr(self, event.type)(event)


def main():
    """Provide an entry point into Landa."""
    args = docopt(__doc__, version=VERSION_STR)
    config = Config(args['REPOSITORY'], debug=args['--debug'],
                    log_level=args['--logging'],
                    pull_requests=args['--pr'],
                    start_event=args['--start'])
    if config.repository is None:
        sys.stderr.write('No repository specified\n')
        return 2

    try:
        Landa(config).run()
    except KeyboardInterrupt:
        sys.stderr.write('Landa shutting down. Goodbye!\n')
        return 0
    except LandaException as exc:
        sys.stderr.write('{0}\n'.format(exc))
        return 1
