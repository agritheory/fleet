# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe


@frappe.whitelist()
def fetch_timesheet_from_vehicle_log(employee, start_date, end_date):
	# Fetch all vehicle logs for the employee with geofence entered, ordered by time
	vehicle_logs = frappe.db.sql(
		"""
        SELECT name, employee, creation, geofences_entered, geofences_exited
        FROM `tabVehicle Log`
        WHERE employee = %s
            AND (geofences_entered IS NOT NULL AND geofences_entered!=''
          OR geofences_exited IS NOT NULL AND geofences_exited !='')
          AND creation BETWEEN %s AND %s
        ORDER BY creation ASC
    """,
		(employee, start_date, end_date),
		as_dict=1,
	)

	fmt = "%Y-%m-%d %H:%M:%S"
	results = []
	i = 0
	n = len(vehicle_logs)
	while i < n:
		log = vehicle_logs[i]
		location = log["geofences_entered"]
		entered_on = log["creation"]
		if location:
			j = i + 1
			exited_on = None
			while j < n:
				next_log = vehicle_logs[j]
				if next_log["geofences_exited"] == location and next_log["creation"] is not None:
					exited_on = next_log["creation"]
					break
				j += 1
			hours = None
			if exited_on:
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
					"vehicle_log": log["name"],
					"location": location,
					"activity_type": frappe.db.get_value("Location", location, "default_activity_type"),
					"entered_on": entered_on,
					"exited_on": exited_on,
					"hours": hours,
				}
			)
			i = j if exited_on else i + 1
		else:
			i += 1
	return results
