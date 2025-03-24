<!-- Copyright (c) 2024, AgriTheory and contributors
For license information, please see license.txt-->

## Fleet

Fleet Integration for ERPNext

## Install Instructions

Set up a new bench, substitute a path to the python version to use, which should 3.10 latest

```
# for linux development
bench init --frappe-branch version-15 {{ bench name }} --python ~/.pyenv/versions/3.10.10/bin/python3
```
Create a new site in that bench
```
cd {{ bench name }}
bench new-site {{ site name }} --force --db-name {{ site name }}
bench use {{ site name }}
```
Download all required applications, including this one
```
bench get-app erpnext --branch version-15
bench get-app hrms --branch version-15
bench get-app fleet --branch version-15 git@github.com:AgriTheory/fleet.git
```
Install all apps
```
bench install-app erpnext hrms fleet
```
Set developer mode in `site_config.json`
```
cd {{ site name }}
nano site_config.json

 "developer_mode": 1,
```
Update and get the site ready
```
bench start
```
In a new terminal window
```
bench update
bench migrate
bench build
```
To run mypy
```shell
source env/bin/activate
mypy ./apps/fleet/fleet --ignore-missing-imports
```
To run pytest
```shell
source env/bin/activate
pytest ./apps/fleet/fleet/tests -s --disable-warnings
```
To install test data and simulate GPS data pushing to a development Traccar server, follow these steps:
1) Start a local Traccar instance using their Docker image (Mac users don't need both port mapping `-p` arguments). Navigate to the local Traccar server via `http://localhost:PORT_NUMBER` (where the `PORT_NUMBER` is the first one before the colon in the command below), register an account with a username and password, then log in.
```shell
docker run -d   --name traccar-test   -p 8082:8082   -p 5000-5150:5000-5150   traccar/traccar:latest

# If the port is already available as an environment variable (see step 2):
docker run -d   --name traccar-test   -p $TRACCAR_PORT:$TRACCAR_PORT   traccar/traccar:latest
```
2) Save the username and password along with the Docker port mapping value as local environment variables. With these variables present, the test data script will automatically create the Traccar Integration document and add vehicle devices to the Docker instance. The test script needs the Traccar Integration in place to properly create vehicles. 
```shell
# In your shell profile/rc file
export TRACCAR_USERNAME='<account username>'
export TRACCAR_PASSWORD='<account password>'
# Optional: if the port number is different than the simulate default of 5055
export TRACCAR_PORT=<port number>
```
3) With the docker instance running, install the demo data into your local site:
```shell
bench execute 'fleet.tests.setup.before_test'
```
4) Simulate GPS data:
```shell
bench execute 'fleet.tests.simulate_gps_data.simulate'
```
