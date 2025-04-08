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
	fleet_home_path = os.path.join(frappe.get_app_path("fleet"), "fleet_home.js")

	with open(fleet_home_path, "r") as fleet_home_file:
		script = fleet_home_file.read()
	vehicle_map = {
		"html": '<div class="tabbed">\n\t<input type="radio" id="tab1" name="css-tabs" checked>\n\t<input type="radio" id="tab2" name="css-tabs">\n\t<input type="radio" id="tab3" name="css-tabs">\n\t\n\t<ul class="tabs">\n\t\t<li class="tab"><label for="tab1">Vehicle Map</label></li>\n\t\t<li class="tab"><label for="tab2">Fleet Calendar</label></li>\n\t\t<li class="tab"><label for="tab3">ETA Tracker</label></li>\n\t</ul>\n\t\n\t<div class="tab-content">\n\t\t<div id="vehicles" style="height: 475px; width: 100%;"></div>\n\t</div>\n\t\n\t<div class="tab-content">\n\t\t<div id="fleet-calendar" style="height: 475x; width: 100%;"></div>\n\t</div>\n\t\n\t<div class="tab-content">\n\t\t<div id="eta-report" style="height: 475px; width: 100%;"></div>\n\t</div>\n</div>',
		"name": "Fleet Home",
		"style": '.tabbed {\n\toverflow-x: hidden;\n\tpadding-bottom: 16px;\n\tborder-bottom: 1px solid var(--border-color);\n}\n\n.tabbed [type="radio"] {\n\tdisplay: none;\n}\n\n.tabs {\n\tdisplay: flex;\n\talign-items: stretch;\n\tlist-style: none;\n\tpadding: 0;\n\tborder-bottom: 1px solid var(--border-color);\n}\n.tab > label {\n\tdisplay: block;\n\tmargin-bottom: -1px;\n\tpadding: 12px 15px;\n\tborder: 1px solid var(--border-color);\n\tfont-size: 12px; \n\tfont-weight: 600;\n\tletter-spacing: 1px;\n\tcursor: pointer;\t\n\ttransition: all 0.3s;\n}\n.tab:hover label {\n\tborder-top-color: black;\n\tcolor: black;\n}\n\n.tab-content {\n\tdisplay: none;\n\tcolor: black;\n}\n\n.tabbed [type="radio"]:nth-of-type(1):checked ~ .tabs .tab:nth-of-type(1) label,\n.tabbed [type="radio"]:nth-of-type(2):checked ~ .tabs .tab:nth-of-type(2) label,\n.tabbed [type="radio"]:nth-of-type(3):checked ~ .tabs .tab:nth-of-type(3) label\n{\n\tborder-bottom-color: var(--border-color);\n\tborder-top-color: black;\n\tbackground: #fff;\n}\n\n.tabbed [type="radio"]:nth-of-type(1):checked ~ .tab-content:nth-of-type(1),\n.tabbed [type="radio"]:nth-of-type(2):checked ~ .tab-content:nth-of-type(2),\n.tabbed [type="radio"]:nth-of-type(3):checked ~ .tab-content:nth-of-type(3)\n{\n\tdisplay: block;\n}\n\n.footnote-area {\n    display: none;\n}',
		"script": script,
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
