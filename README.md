# landa: automatically label your GitHub pull requests

**Team labels**  
Landa can automatically apply a team label based on the author of the pull request.

**Review labels**  
Landa can automatically apply labels based on path matches against files changed. For example, apply a `db review` label whenever a pull request updates any file that matches the pattern `db/*`.

**Stub commit statuses**  
Landa can apply pending commit statuses to your commits. Use this if you use third party services that uses polling to test for changes and you want the commit status to show up right away.

**Python 2.7 AWS lambda function.**  
Landa runs on AWS Lambda using Python 2.7. It uses GitHub webhooks as triggers.

## Getting started

 - Create a Python 2.7 lambda function in AWS and enable the API gateway for this function.
 - For the Python 2.7 lambda function, set up the following environment variables GH_USER and GH_TOKEN ([create token here](https://github.com/settings/tokens)).
 - On GitHub, go to your repo settings -> Webhooks & Services -> Add webhook:
    - Payload URL: the URL of your lambda function
    - Content type: application/json
    - Secret: <empty>
    - Which events: click "Let me select individual events" and make sure only "Pull Requests" is selected.
    - Active: checked
 - Clone the repo and copy `config.example.py` to `config.py` and adjust appropriately.
 - Run `script/setup` to install the dependencies.
 - Adjust `script/deploy` to match your Lambda function name
 - Install AWS-cli: `pip install awscli`
 - Configure AWS-cli: `aws configure`
 - Deploy: `script/deploy`

You will have to redeploy after every configuration change. This can be done by running `script/deploy`.
