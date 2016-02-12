# Copy this file to config.py
# Base branch is the targetted branch
# Head branch is the branch with changes

# Repo/branch to monitor
repo_owner = 'appfolio'
repo = 'landa'

# PRs from these users are ignored
ignore_login = ['example_user']

# PRs targetting these branches are ignored
ignore_base_branch = ['master']

team_labels = {
  '#Awesome': [
    'balloob'
    'balloobbot',
  ],
  'TeamMOM': [
    'farcy',
  ]
}

file_pattern_labels = {
  'db_review': 'db/*',
  'css_review': 'app/assets/stylesheets/global/*',
  'js_review': 'node_modules/*',
}

base_branch_labels = {
  'release/*': 'trolololol',
}

head_branch_labels = {
  'release': 'release/*',
}

commit_status = {
  'Farcy': 'To be done',
  'CI - Jest': 'To be done',
  'CI - Unit/Functional/Integration': 'To be done',
  'CI - Selenium': 'To be done',
}
