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
To start local Traccar instance
```
docker run -d   --name traccar-test   -p 8082:8082   -p 5000-5150:5000-5150   traccar/traccar:latest
```
To simulate GPS data:
```
bench execute 'fleet.tests.simulate_gps_data.simulate'
```
