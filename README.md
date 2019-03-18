# pyHookDeploy
A simple Python Flask Server for automated deployment of code via GitHub and GitLab Webhook push events.

## Setup
Install the required pip packages. Using a virtual environment is highy recommended.
```bash
$ virtualenv --python=python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## Usage
pyHookDeploy is served using Gunicorn and can be set up to run as a daemon/ service. It is recommended to run pyHookDeploy behind a reverse proxy with TLS support.
<br /><br />
However, the script "start.sh" allows one to quickly run pyHookDeploy on the console.
```bash
$ ./start.sh
```

## Configuration
### local_repos.txt
This file contains the information of repositories to deploy on the local system. Each line follows the following format:
```
repo_name;path_to_repo;path_to_key;secret
```
Breakdown of the components:

|Name			|Description														|
|:--------------|:------------------------------------------------------------------|
|repo_name		|The full name of the repository.									|
|path_to_repo	|The absolute path to the repository directory on the local system.	|
|path_to_key	|The absolute path to the deployment key of the repository.			|
|secret			|(Optional) The secret token for verification.						|

Examples:
```
# Comment lines start with a hash and will be ignored.

# Configuration for a repository called "repo1".
zxlim/repo1;/opt/ext/repo1;/var/private/.ssh/repo1_deployment_key

# Repository "repo2" requires a secret.
zxlim/repo2;/opt/ext/repo2;/var/private/.ssh/repo2_deployment_key;a1b2c3d4e5
```

# License
This project is licensed under the [Apache License 2.0](LICENSE).