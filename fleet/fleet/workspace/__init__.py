# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt

import frappe
import json
from typing import Any

from frappe.utils.data import flt


@frappe.whitelist()
def get_coords() -> dict[str, Any]:
	coords = frappe.get_all("Vehicle", fields=["name", "gps_location"])

	features = []
	bounds = {"minLat": 90, "maxLat": -90, "minLng": 180, "maxLng": -180}

	for vehicle in coords:
		if not vehicle.gps_location:
			continue

		try:
			location = json.loads(vehicle.gps_location)
			lng, lat = location["geometry"]["coordinates"]
			bounds["minLat"] = min(bounds["minLat"], lat)
			bounds["maxLat"] = max(bounds["maxLat"], lat)
			bounds["minLng"] = min(bounds["minLng"], lng)
			bounds["maxLng"] = max(bounds["maxLng"], lng)

			feature = {
				"type": "Feature",
				"geometry": location["geometry"],
				"properties": {
					"name": f'<a href="/app/vehicle/{vehicle.name}">{vehicle.name}</a>',
					# "driver": f'<a href="/app/vehicle/{vehicle.driver}">{vehicle.driver}</a>',
				},
			}
			features.append(feature)

		except (json.JSONDecodeError, KeyError, ValueError) as e:
			continue

	return {"features": {"type": "FeatureCollection", "features": features}, "bounds": bounds}


@frappe.whitelist()
def get_battery_voltage() -> str:
	# TODO: add enabled/disabled to vehicle
	battery_levels = frappe.get_all(
		"Vehicle",
		filters={"battery_voltage": ["is", "set"]},
		fields=["name", "battery_voltage"],
		order_by="battery_voltage ASC",
		limit=5,
	)
	output = '<table class="table table-hover table-compact"><tbody>'
	output += "<tr><th>Vehicle</th><th>Battery Voltage</th></tr>"
	for b in battery_levels:
		output += f'<tr><td><a href="/app/vehicle/{b.name}">{b.name}</a></td><td align="right">{flt(b.battery_voltage):2.2f}</td></tr>'
	output += "</tbody></table>"
	return output
