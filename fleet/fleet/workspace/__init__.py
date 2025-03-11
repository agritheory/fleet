# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt

import json
from typing import Any

import frappe
from frappe.utils.data import flt


@frappe.whitelist()
def get_coords() -> dict[str, Any]:
	vs = frappe.get_all("Vehicle")

	features = []
	bounds = {"minLat": 90, "maxLat": -90, "minLng": 180, "maxLng": -180}

	for vehicle in vs:
		gps_location = frappe.get_doc("Vehicle", vehicle).gps_location
		if not gps_location:
			continue

		try:
			location = json.loads(gps_location)
			lng, lat = location["features"][0]["geometry"]["coordinates"]
			bounds["minLat"] = min(bounds["minLat"], lat)
			bounds["maxLat"] = max(bounds["maxLat"], lat)
			bounds["minLng"] = min(bounds["minLng"], lng)
			bounds["maxLng"] = max(bounds["maxLng"], lng)

			feature = {
				"type": "Feature",
				"geometry": location["features"][0]["geometry"],
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


@frappe.whitelist()
def get_eta():
	dt = frappe.get_all("Delivery Trip", {"status": ["in", ["Scheduled", "In Transit"]]})
	# TODO: refactor to sort by estimated arrival from Delivery Stop and distance to that location
	output = '<table class="table table-hover table-compact" style="margin-bottom: 1rem"><tbody>'
	output += "<tr><th>Driver</th><th>Vehicle</th><th>Customer</th><th>Estimated Arrival</th></tr>"
	for row in dt:
		output += f"""
		<tr
			<td><a href="/app/driver/{row.driver}">{row.driver}</a></td>
			<td><a href="/app/vehicle/{row.vehicle}">{row.vehicle}</a></td>
			<td><a href="/app/customer/{row.customer}">{row.customer}</a></td>
			<td>{row.estimated_arrival}</td>
		</tr>
		"""
	if not dt:
		output += '<tr><td colspan=4 align="center">No Delivery Trips Found</td></tr>'
	output += "</tbody></table>"
	return output
