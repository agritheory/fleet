# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt


import json
from datetime import datetime

import frappe
from croniter import croniter
from erpnext.setup.doctype.vehicle.vehicle import Vehicle
from frappe import _
from frappe.utils.data import get_datetime, now_datetime


class FleetVehicle(Vehicle):
	@property
	def gps_location(self):
		coords = frappe.db.get_value(
			"Vehicle Log",
			{"license_plate": self.name},
			["longitude", "latitude"],
			order_by="creation DESC",
		)
		if not coords:
			return None
		# encode to geojson, which uses (lon, lat) order
		geojson = {
			"type": "FeatureCollection",
			"features": [
				{"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": coords}}
			],
		}
		return json.dumps(geojson)

	@property
	def battery_level(self):
		return frappe.db.get_value(
			"Vehicle Log", {"license_plate": self.name}, "battery_level", order_by="creation DESC"
		)

	@property
	def most_recent_driver(self):
		driver_emp = frappe.db.get_value(
			"Vehicle Log",
			{"license_plate": self.name},
			["employee"],
			order_by="creation DESC",
		)
		driver_docname = frappe.get_value("Driver", {"employee": driver_emp})
		driver_emp_name = frappe.get_value("Employee", driver_emp, "employee_name")
		return driver_docname, driver_emp_name


def check_schedule_poll_frequency(doc, method=None):
	old_value = doc.get_db_value("poll_frequency")

	if old_value != doc.poll_frequency:
		schedule_poll_frequency(doc, update=True)


def schedule_poll_frequency(doc, update=False):
	current_time = now_datetime()
	last_execution = doc.poll_frequency_last_execution
	next_execution = doc.poll_frequency_next_execution

	if doc.poll_frequency_last_execution:
		last_execution = get_datetime(doc.poll_frequency_last_execution)
	else:
		last_execution = current_time
		doc.db_set("poll_frequency_last_execution", last_execution, update_modified=False)

	if doc.poll_frequency_next_execution and update is False:
		next_execution = get_datetime(doc.poll_frequency_next_execution)
	else:
		cron = croniter(doc.poll_frequency, last_execution)
		next_execution = cron.get_next(datetime)
		doc.db_set("poll_frequency_next_execution", next_execution, update_modified=False)

	if current_time >= next_execution:
		frappe.enqueue(
			method="fleet.fleet.traccar.sync_vehicle",
			queue="long",
			vehicle=doc.name,
		)
		cron = croniter(doc.poll_frequency, next_execution)
		next_execution = cron.get_next(datetime)
		doc.db_set("poll_frequency_last_execution", current_time, update_modified=False)
		doc.db_set("poll_frequency_next_execution", next_execution, update_modified=False)


def validate_poll_frequency_cron_format(doc, method=None):
	if not doc.poll_frequency:
		return

	if not croniter.is_valid(doc.poll_frequency):
		frappe.throw(
			_("{0} is not a valid Cron expression.").format(f"<code>{doc.poll_frequency}</code>"),
			title=_("Bad Cron Expression"),
		)
