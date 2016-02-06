from __future__ import print_function

from fnmatch import fnmatch
import json

import auth
import config

VERBOSE = False


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

    action = message.get('action')

    if 'pull_request' not in message or action not in ('opened',
                                                       'synchronize'):
        print('Action: {}. Contains pull_request object: {}'.format(
            action, 'pull_request' in message))
        return

    pr_id = message['number']
    author = message['pull_request']['user']['login']

    target_repo_owner = message['pull_request']['base']['repo']['owner']['login']
    target_repo = message['pull_request']['base']['repo']['name']
    target_branch = message['pull_request']['base']['ref']

    if target_repo_owner != config.repo_owner or target_repo != config.repo:
        print("Got event for unexpected repo {}/{}".format(
            target_repo_owner, target_repo))
        return

    if target_branch != config.branch:
        print('PR is targetting {} branch, aborting'.format(target_branch))
        return

    if author in config.ignore_login:
        print('Ignoring pull requests from {}'.format(author))
        return

    gh = login(auth.user, password=auth.token)

    issue = gh.issue(target_repo_owner, target_repo, pr_id)
    pr = gh.pull_request(target_repo_owner, target_repo, pr_id)
    files_changed = pr.files()
    current_labels = set(str(l) for l in issue.original_labels)

    # Calculate which labels to add and remove
    label_tests = {label: (author in users) for label, users
                   in config.team_labels.items()}
    label_tests.update(
        {label: any(fnmatch(pfile.filename, pattern) for pfile
                    in files_changed)
         for label, pattern in config.file_pattern_labels.items()})

    # Find labels to remove:
    remove_labels = current_labels & set(label for label, to_add
                                         in label_tests.items() if not to_add)

    # Labels to add:
    add_labels = (set(lab for lab, to_add in label_tests.items() if to_add) -
                  current_labels)

    # new set of labels:
    new_labels = (current_labels - remove_labels) | add_labels

    if new_labels:
        print('Changing labels on PR#{0} from {1} to {2}'.format(
            pr.number, ', '.join(current_labels), ', '.join(new_labels)))

        if not debug:
            issue.replace_labels(list(new_labels))

    print('Handled pull request {}'.format(pr_id))
