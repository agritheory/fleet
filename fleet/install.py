# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt

import os
import subprocess
import types

import frappe
import pycountry
from frappe.installer import update_site_config


def after_install():
	install_states_and_provinces()
	install_custom_html_blocks()
	install_driver_role()
	create_traccar_user()
	add_custom_queue()


def install_states_and_provinces():
	for state in list(pycountry.subdivisions.get(country_code="US")) + list(
		pycountry.subdivisions.get(country_code="CA")
	):
		if frappe.db.exists("State", {"state": state.name}):
			continue
		s = frappe.new_doc("State")
		s.state = state.name
		s.abbr = state.code.replace(f"{state.country_code}-", "")
		s.save()


def install_custom_html_blocks():
	app_path = frappe.get_app_path("fleet")

	with open(os.path.join(app_path, "fleet_home.html")) as f:
		fleet_home_html = f.read()

	with open(os.path.join(app_path, "fleet_home.css")) as f:
		fleet_home_css = f.read()

	vehicle_map = {
		"html": fleet_home_html,
		"name": "Fleet Home",
		"script": "const mapContainer = root_element.querySelector('#vehicles')\nif (!mapContainer) {\n    console.error(\"Map container not found in DOM\");\n}\n\nlet map = L.map(mapContainer).setView([51.505, -0.09], 13);\nL.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {\n    attribution: '© OpenStreetMap contributors'\n}).addTo(map);\n\nfrappe.xcall('fleet.fleet.workspace.get_coords').then(response => {\n    if (!response.features.features.length) {\n        console.log(\"No vehicle coordinates found\");\n        return;\n    }\n\n    // Add markers for each vehicle\n    response.features.features.forEach(feature => {\n        const [lng, lat] = feature.geometry.coordinates;\n        const marker = L.marker([lat, lng])\n            .bindPopup(`\n                <b>Vehicle:</b> ${feature.properties.name}<br>\n                <b>Driver:</b> ${feature.properties.driver}\n            `)\n            .addTo(map);\n    });\n\n    // Fit map to show all markers with padding\n    const bounds = L.latLngBounds([\n        [response.bounds.minLat, response.bounds.minLng],\n        [response.bounds.maxLat, response.bounds.maxLng]\n    ]);\n    map.fitBounds(bounds, {\n        padding: [50, 50] // Add 50px padding around the bounds\n    });\n}).catch(error => {\n    console.error(\"Error fetching vehicle coordinates:\", error);\n});\n\n\nconst calendarContainer = $(root_element).find('#fleet-calendar');\ncalendarContainer.prepend(`\n  <link rel=\"stylesheet\" href=\"/assets/frappe/js/lib/fullcalendar/fullcalendar.min.css\">\n`);\n\nfrappe.require([\n    \"assets/frappe/js/lib/fullcalendar/fullcalendar.min.js\",\n], \n    () => {\n    let calendar = new frappe.views.Calendar({\n        doctype: 'Vehicle',\n        parent: calendarContainer,\n        page: {\n            clear_user_actions: () => {},\n            add_menu_item: () => {}\n        },\n        list_view: {\n            filter_area: {\n                get: () => []\n            }\n        },\n        field_map: {\n\t\tstart: 'date',\n\t\tend: 'date',\n\t\tid: 'name',\n\t\ttitle: 'description',\n\t\tallDay: 'allDay',\n\t\tprogress: 'progress',\n\t},\n\tfilters: [\n\t\t{\n\t\t\tfieldtype: 'Link',\n\t\t\tfieldname: 'vehicle',\n\t\t\toptions: 'Vehicle',\n\t\t\tlabel: __('Vehicle'),\n\t\t},\n\t\t{\n\t\t\tfieldtype: 'Driver',\n\t\t\tfieldname: 'driver',\n\t\t\toptions: 'Driver',\n\t\t\tlabel: __('Driver'),\n\t\t},\n\t],\n\tget_events_method: 'fleet.fleet.calendar.get_events',\n\tget_css_class: data => {\n\t\tcalendar.color_map['purple'] = 'purple'\n\t\tcalendar.color_map['pink'] = 'pink'\n\t\tif (data.type === 'Holiday') {\n\t\t\treturn 'success'\n\t\t} else if (data.type === 'License') {\n\t\t\treturn 'purple'\n\t\t} else if (data.type === 'Registration') {\n\t\t\treturn 'danger'\n\t\t} else if (data.type === 'Insurance') {\n\t\t\treturn 'pink'\n\t\t} else if (data.type === 'Inspection') {\n\t\t\treturn 'warning'\n\t\t}\n\t},\n\tgantt: false,\n\toptions: {\n\t\teditable: false,\n\t\tselectable: false,\n\t},\n    })\n})\n\nconst etaTracker = root_element.querySelector('#eta-report')\nfrappe.xcall('fleet.fleet.workspace.get_eta').then(response => {\n    etaTracker.innerHTML = response\n})\n",
		"style": fleet_home_css,
	}
	if not frappe.db.exists("Custom HTML Block", {"name": vehicle_map.get("name")}):
		vm = frappe.new_doc("Custom HTML Block")
		vm.update(vehicle_map)
		vm.save()

	battery_voltage = {
		"html": '<div id="vehicle-battery-voltage"></div>\n',
		"name": "Vehicle Battery Voltage",
		"script": "const batteryLevels = root_element.querySelector('#vehicle-battery-voltage')\nfrappe.xcall('fleet.fleet.workspace.get_battery_voltage').then(response => {\n    batteryLevels.innerHTML = response\n})",
	}
	if not frappe.db.exists("Custom HTML Block", {"name": battery_voltage.get("name")}):
		bv = frappe.new_doc("Custom HTML Block")
		bv.update(battery_voltage)
		bv.save()


def create_traccar_user():
	def _bypass(*args, **kwargs):
		return

	if not frappe.db.exists("User", "Traccar"):
		u = frappe.new_doc("User")
		u.email = "Traccar@agritheory.dev"
		u.username = "traccar"
		u.first_name = "Traccar"
		u.send_welcome_email = 0
		u._validate_data_fields = types.MethodType(_bypass, u)
		u.save()
		frappe.model.rename_doc.rename_doc(
			"User", "Traccar@agritheory.dev", "Traccar", force=1, validate=False
		)
		frappe.db.set_value("User", "Traccar", "email", "Traccar", update_modified=False)


def get_user_confirmation():
	while True:
		user_input = (
			input(
				"Adding custom queue for Traccar. This requires to run 'bench setup supervisor', do you want to run it? (yes/no): "
			)
			.strip()
			.lower()
		)
		if user_input in ["yes", "y"]:
			return True
		elif user_input in ["no", "n"]:
			return False
		else:
			print("Please enter 'yes' or 'no'.")


def add_custom_queue():
	sites_path = os.getcwd()
	common_site_config_path = os.path.join(sites_path, "common_site_config.json")
	workers = frappe.conf.workers

	if workers and "traccar" in workers.keys():
		return

	if workers:
		workers["traccar"] = {"timeout": 8000}
	else:
		workers = {"traccar": {"timeout": 8000}}

	update_site_config("workers", workers, validate=False, site_config_path=common_site_config_path)

	# skip supervisor setup on development setups
	if not (frappe.conf.restart_supervisor_on_update or frappe.conf.restart_systemd_on_update):
		return

	if not get_user_confirmation():
		print("Please run 'bench setup supervisor' manually.")
		return

	process = subprocess.Popen(
		"bench setup supervisor --yes",
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True,
	)
	stdout, stderr = process.communicate()

	if process.returncode != 0:
		if "INFO: A newer version of bench is available" not in stderr:
			print(f"Command failed: {stderr}.")
		else:
			print(f"Command failed: {stdout}.")


def install_driver_role():
	if not frappe.db.exists("Role", "Driver"):
		role = frappe.new_doc("Role")
		role.update(
			{
				"name": "Driver",
				"role_name": "Driver",
				"desk_access": True,
				"home_page": "/app/fleet",
			}
		)
		role.save()
