# Copy this file to config.py

# Repo/branch to monitor
repo_owner = 'appfolio'
repo = 'landa'

# PRs from these users are ignored
ignore_login = ['example_user']

# PRs targetting these branches are ignored
ignore_target_branch = ['master']

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

commit_status = {
  'Farcy': 'To be done',
  'CI - Jest': 'To be done',
  'CI - Unit/Functional/Integration': 'To be done',
  'CI - Selenium': 'To be done',
}
