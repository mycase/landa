# Copy this file to config.py

# Repo/branch to monitor
repo_owner = 'appfolio'
repo = 'landa'
branch = 'master'

ignore_login = ['example_user']

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
