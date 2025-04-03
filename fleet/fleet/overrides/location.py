# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.utils import comma_and

from fleet.fleet.traccar import add_traccar_geofence


def validate_geofenced_vehicles_have_traccar_id(doc, method=None):
	if not doc.geofenced_vehicle:
		return
	errors = []
	for v in doc.geofenced_vehicle:
		traccar_id = frappe.get_value("Vehicle", v.vehicle, "traccar_id")
		if not traccar_id:
			errors.append(v.vehicle)
	if errors:
		frappe.throw(
			_(
				f"Missing Traccar ID for vehicle(s) {comma_and(errors)}. This is required to link a device to the geofence."
			)
		)


def sync_traccar_geofence(doc, method=None):
	"""
	Logic:
	- check if sync_traccar_geofence checked
	- TODO: check if modified, then update either geofence or devices to link
	- if there isn't a traccar_geofence_id -> look for valid feature(s) and add to Traccar,
	  link vehicles in Multiselect table to new geofence
	- if there is a traccar_geofence_id -> see if valid

	"""
	if not doc.sync_traccar_geofence:
		# TODO: handle modifications / delete geofence if uncheck this?
		return
	if doc.doctype == "Address":
		# TODO: Dynamic Link to Location? Need polygon/polyline coords for geofence
		return
	elif doc.doctype == "Location" and not doc.traccar_geofence_id:
		loc = json.loads(doc.location)
		if not has_valid_feature_type(loc):
			frappe.msgprint(
				_(
					"No valid geometry features (polyline, polygon, or rectangle) found on map to use as geofence."
				)
			)
			return
		for feature in loc["features"]:
			feat_type = feature.get("geometry", {}).get("type")
			if feat_type not in ["LineString", "Polygon"]:
				continue
			coords = []
			flatten_coordinates(coord_list=coords, item=feature["geometry"]["coordinates"])
			device_ids = []
			if doc.geofenced_vehicle:
				device_ids = [
					frappe.get_value("Vehicle", v.vehicle, "traccar_id") for v in doc.geofenced_vehicle
				]
			geofence_id = add_traccar_geofence(doc, feat_type, coords, device_ids=device_ids)
			doc.traccar_geofence_id = geofence_id
	elif doc.doctype == "Location":
		# TODO: what to do if has geofence id - check for modifications and push updates?
		return


def has_valid_feature_type(geojson):
	for feature in geojson.get("features", []):
		if feature.get("geometry", {}).get("type") in ["LineString", "Polygon"]:
			return True
	return False


def flatten_coordinates(coord_list, item, type=float):
	if isinstance(item, type):
		coord_list.append(item)
		return
	if all(isinstance(n, type) for n in item):
		# item is a list of [lon, lat] coordinates, reverse to lat, lon and extend list
		coord_list.append(item[-1::-1])
		return
	else:
		for i in item:
			flatten_coordinates(coord_list, i, type=type)
