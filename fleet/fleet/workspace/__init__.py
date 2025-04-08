# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt

import json
import requests
from typing import Any

import frappe
from frappe.utils.data import flt


@frappe.whitelist()
def get_coords() -> dict[str, Any]:
	vs = frappe.get_all("Vehicle")
	default_company = frappe.get_value("Global Defaults", None, "default_company")
	address_doc = None
	bounds = {"minLat": 90, "maxLat": -90, "minLng": 180, "maxLng": -180}
	features = []

	address_link = frappe.get_all("Dynamic Link",
		filters={"link_doctype": "Company", "link_name": default_company},
		fields=["parent"],
		order_by="creation desc",
		limit=1
	)
	if address_link:
		address_doc = frappe.get_doc("Address", address_link[0]["parent"])
		address_str = ", ".join(filter(None, [
			address_doc.address_line1,
			address_doc.city,
			address_doc.state,
			address_doc.country,
			address_doc.pincode
		]))
		lat, lng = geocode_address(address_str)

		if lat and lng:
			bounds["minLat"] = min(bounds["minLat"], lat)
			bounds["maxLat"] = max(bounds["maxLat"], lat)
			bounds["minLng"] = min(bounds["minLng"], lng)
			bounds["maxLng"] = max(bounds["maxLng"], lng)
			features.append({
				"type": "Feature",
				"geometry": {
					"type": "Point",
					"coordinates": [lng, lat]
				},
				"properties": {
					"name": "Company Headquarters",
					"is_headquarters": True,
				}
			})

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

	return {
		"features": {"type": "FeatureCollection", "features": features},
		"bounds": bounds,
	}


@frappe.whitelist()
def get_battery_voltage() -> str:
	battery_levels = []
	for v in frappe.get_all("Vehicle", {"disabled": 0}, pluck="name"):
		v_doc = frappe.get_doc("Vehicle", v)
		bl = v_doc.battery_level
		if bl:
			battery_levels.append((v, bl))
	battery_levels = sorted(battery_levels, key=lambda b: b[1])
	output = '<table class="table table-hover table-compact"><tbody>'
	output += "<tr><th>Vehicle</th><th>Battery Voltage</th></tr>"
	for name, bl in battery_levels:
		output += f'<tr><td><a href="/app/vehicle/{name}">{name}</a></td><td align="right">{flt(bl):2.2f}</td></tr>'
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

def geocode_address(address_str):
	#address_str = "3 Canterbury Rd, Concord, Nuevo Hampshire"
	address_str = "45 Hancock St, Rochester, NH 03867, Estados Unidos"
	url = "https://nominatim.openstreetmap.org/search"
	params = {
		"q": address_str,
		"format": "json",
		"limit": 1
	}
	response = requests.get(url, params=params, headers={"User-Agent": "Frappe Fleet App"})

	if response.ok and response.json():
		lat = float(response.json()[0]["lat"])
		lon = float(response.json()[0]["lon"])
		return lat, lon
	return None, None