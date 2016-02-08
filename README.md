Landa: Lambda function to label PRs
===================================

A Python 2.7 lambda function to automatically process pull requests:
 - Team labels: apply labels based on the author of the pull request
 - Review labels: apply labels based on path matches against files changed.
 - Stub CI status for commits while waiting for CI to pick it up

## Getting started

Copy `auth.example.py` to `auth.py` and `config.example.py` to `config.py` and adjust appropriately.

Before being able to run tests or deploy to lambda, run `script/setup`. Once this is done you can deploy your lambda function using `script/deploy`.

Deployment requires you to have AWS-cli installed (`pip install awscli`) and configured (`aws configure`). You will have to update `script/deploy` with the correct function name.
