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
    base_branch = message['pull_request']['base']['ref']
    head_branch = message['pull_request']['head']['ref']

    if base_repo_owner != config.repo_owner or base_repo != config.repo:
        print("Got event for unexpected repo {}/{}".format(
            base_repo_owner, base_repo))
        return

    if base_branch in config.ignore_base_branch:
        print('PR is targetting {} branch, aborting'.format(base_branch))
        return

    if author in config.ignore_login:
        print('Ignoring pull requests from {}'.format(author))
        return

    gh = login(auth.user, password=auth.token)

    issue = gh.issue(base_repo_owner, base_repo, pr_id)
    pr = gh.pull_request(base_repo_owner, base_repo, pr_id)
    files_changed = pr.files()
    current_labels = set(str(l) for l in issue.original_labels)

    # Calculate which labels to add and remove
    # Team Labels
    label_tests = {label: (author in users) for label, users
                   in config.team_labels.items()}
    # File Pattern Labels
    label_tests.update(
        {label: any(fnmatch(pfile.filename, pattern) for pfile
                    in files_changed) or label_tests.get(label, False)
         for label, pattern in config.file_pattern_labels.items()})
    # Base Branch Labels
    label_tests.update(
        {label: fnmatch(base_branch, pattern) or label_tests.get(label, False)
         for label, pattern in config.base_branch_labels.items()})
    # Head Branch Labels
    label_tests.update(
        {label: fnmatch(head_branch, pattern) or label_tests.get(label, False)
         for label, pattern in config.head_branch_labels.items()})

    # Find labels to remove:
    remove_labels = current_labels & set(label for label, to_add
                                         in label_tests.items() if not to_add)

    # Labels to add:
    add_labels = (set(lab for lab, to_add in label_tests.items() if to_add) -
                  current_labels)

    # new set of labels:
    new_labels = (current_labels - remove_labels) | add_labels

    if new_labels != current_labels:
        print('Changing labels on PR#{0} from {1} to {2}'.format(
            pr.number, ', '.join(current_labels), ', '.join(new_labels)))

        if not debug:
            issue.replace_labels(list(new_labels))

    if config.commit_status:
        repo = gh.repository(base_repo_owner, base_repo)
        sha = list(pr.commits())[-1].sha

        for context, description in config.commit_status.items():
            if debug:
                print('Settting {} status {} to {}: {}'.format(
                    sha, context, 'pending', description))
            else:
                repo.create_status(sha, 'pending', context=context,
                                   description=description)

    print('Handled pull request {}'.format(pr_id))
