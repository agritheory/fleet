# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe


@frappe.whitelist()
def fetch_timesheet_from_vehicle_log(employee, start_date, end_date):
	# Fetch all vehicle logs for the employee with geofence entered, ordered by time
	vehicle_logs = frappe.get_all(
		"Vehicle Log",
		fields=["name", "employee", "creation", "geofences_entered", "geofences_exited"],
		filters={
			"employee": employee,
			"creation": ["between", [start_date, end_date]],
		},
		order_by="creation asc",
	)
	# Filter out logs where both geofences_entered and geofences_exited are empty or None
	vehicle_logs = [
		log
		for log in vehicle_logs
		if (
			log.get("geofences_entered") not in (None, "") or log.get("geofences_exited") not in (None, "")
		)
	]

	fmt = "%Y-%m-%d %H:%M:%S"
	results = []
	entered_dict = {}
	for log in vehicle_logs:
		location_entered = log.get("geofences_entered")
		location_exited = log.get("geofences_exited")
		creation = log.get("creation")
		# Track entered locations
		if location_entered:
			entered_dict[location_entered] = {
				"vehicle_log": log["name"],
				"entered_on": creation,
				"activity_type": frappe.db.get_value("Location", location_entered, "default_activity_type"),
			}
		# If exited and previously entered, pair and calculate hours
		if location_exited and location_exited in entered_dict:
			entered_data = entered_dict.pop(location_exited)
			entered_on = entered_data["entered_on"]
			exited_on = creation
			hours = None
			entered = entered_on if isinstance(entered_on, str) else entered_on.strftime(fmt)
			exited = exited_on if isinstance(exited_on, str) else exited_on.strftime(fmt)
			try:
				entered_dt = datetime.strptime(entered, fmt)
				exited_dt = datetime.strptime(exited, fmt)
				hours = (exited_dt - entered_dt).total_seconds() / 3600.0
			except Exception:
				hours = None
			results.append(
				{
					"vehicle_log": entered_data["vehicle_log"],
					"location": location_exited,
					"activity_type": entered_data["activity_type"],
					"entered_on": entered_on,
					"exited_on": exited_on,
					"hours": hours,
				}
			)
	return results
