from __future__ import print_function

from fnmatch import fnmatch
from chainmap import ChainMap
import json

import auth
import config

config.repos = {key.lower(): value for key, value in config.repos.items()}

VERBOSE = False
EMPTY_REPO_CONFIG = {
    'ignore_login': [],
    'ignore_base_branch': [],
    'team_labels': {},
    'file_pattern_labels': {},
    'base_branch_labels': {},
    'head_branch_labels': {},
    'commit_status': {}
}


def lambda_handler(event, context, debug=False):
    if debug:
        import os
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                        'dependencies'))
        print(os.path.join(os.path.dirname(__file__), 'dependencies'))

    from github3 import login

    if 'Records' in event:
        # SNS
        if VERBOSE:
            event_type = event['Records'][0]['Sns']['MessageAttributes']['X-Github-Event']['Value']
            print(event_type + ': ' + event['Records'][0]['Sns']['Message'])
        message = json.loads(event['Records'][0]['Sns']['Message'])
    else:
        # API
        message = event
        if VERBOSE:
            print('API: ' + json.dumps(event, indent=2))

    if 'pull_request' not in message:
        print('Not a PR event. Aborting')
        return

    action = message.get('action')
    pr_id = message.get('number')

    if action not in ('opened', 'synchronize'):
        print('Not handling {} action for Pull Request {}'.format(action,
                                                                  pr_id))
        return

    author = message['pull_request']['user']['login']

    base_repo_owner = message['pull_request']['base']['repo']['owner']['login']
    base_repo = message['pull_request']['base']['repo']['name']
    base_repo_full_name = message['pull_request']['base']['repo']['full_name']

    head_repo_owner = message['pull_request']['head']['repo']['owner']['login']
    head_repo = message['pull_request']['head']['repo']['name']
    head_sha = message['pull_request']['head']['sha']

    base_branch = message['pull_request']['base']['ref']
    head_branch = message['pull_request']['head']['ref']

    if base_repo_full_name.lower() not in config.repos:
        print("Got event for unexpected repo {}".format(base_repo_full_name))
        return

    repo_config = ChainMap(
        config.repos[base_repo_full_name.lower()],
        config.default,
        EMPTY_REPO_CONFIG
    )

    if base_branch in repo_config['ignore_base_branch']:
        print('PR {} is targetting {} branch, aborting'.format(pr_id,
                                                               base_branch))
        return

    if author in repo_config['ignore_login']:
        print('Ignoring pull request {} from {}'.format(pr_id, author))
        return

    gh = login(auth.user, password=auth.token)

    issue = gh.issue(base_repo_owner, base_repo, pr_id)
    pr = gh.pull_request(base_repo_owner, base_repo, pr_id)
    head_repo = gh.repository(head_repo_owner, head_repo)
    head_commit = head_repo.commit(head_sha)

    files_changed = pr.files()
    current_labels = set(str(l) for l in issue.original_labels)

    # Calculate which labels to add and remove
    # Team Labels
    label_tests = {label: (author in users) for label, users
                   in repo_config['team_labels'].items()}

    # File Pattern Labels
    for label, patterns in repo_config['file_pattern_labels'].items():
        label_tests[label] = False

        if isinstance(patterns, str):
            patterns = [patterns]

        for pattern in patterns:
            if isinstance(pattern, str):
                match = any(fnmatch(pfile.filename, pattern) for pfile
                            in files_changed)
            else:
                match = any(pattern.match(pfile.filename) is not None for pfile
                            in files_changed)

            if match:
                label_tests[label] = True
                break

        if label_tests[label]:
            continue

    # Base Branch Labels
    label_tests.update(
        {label: fnmatch(base_branch, pattern) or label_tests.get(label, False)
         for label, pattern in repo_config['base_branch_labels'].items()})
    # Head Branch Labels
    label_tests.update(
        {label: fnmatch(head_branch, pattern) or label_tests.get(label, False)
         for label, pattern in repo_config['head_branch_labels'].items()})

    # Find labels to remove:
    remove_labels = current_labels & set(label for label, to_add
                                         in label_tests.items() if not to_add)

    # Labels to add:
    add_labels = (set(lab for lab, to_add in label_tests.items() if to_add) -
                  current_labels)

    # new set of labels:
    new_labels = (current_labels - remove_labels) | add_labels

    if new_labels != current_labels:
        print('Changing labels on PR#{0}.'.format(pr.number))
        if add_labels:
            print('Adding {0}'.format(', '.join(add_labels)))
        if remove_labels:
            print('Removing {0}'.format(','.join(remove_labels)))

        if not debug:
            if add_labels:
                issue.add_labels(*add_labels)
            for label in remove_labels:
                issue.remove_label(label)
            issue.replace_labels(list(new_labels))

    if repo_config['commit_status']:
        repo = gh.repository(base_repo_owner, base_repo)
        current_statuses = set(status.context for status
                               in head_commit.statuses())

        for context, description in repo_config['commit_status'].items():
            if context in current_statuses:
                print('Skipping setting commit status {}, already set.'.format(
                    context))
            elif debug:
                print('Settting {} status {} to {}: {}'.format(
                    head_commit.sha, context, 'pending', description))
            else:
                repo.create_status(head_commit.sha, 'pending', context=context,
                                   description=description)

    print('Handled pull request {}'.format(pr_id))
