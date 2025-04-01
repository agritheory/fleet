# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _

from fleet.fleet.traccar import add_traccar_geofence


# Should accept both location and address doctypes
def sync_traccar_geofence(doc, method=None):
	"""
	Logic:
	- must have sync_traccar_geofence checked
	- if there isn't a traccar_geofence_id -> look for valid feature(s) and add to Traccar
	  how to link new geofence to devices/groups?
	- if there is a traccar_geofence_id -> ignore? sync? Is ERPNext source of truth, or Traccar?
	"""
	if not doc.sync_traccar_geofence:
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
			# TODO: collect deviceId or groupId to link new geofence to devices?
			geofence_id = add_traccar_geofence(doc, feat_type, coords)
			# TODO: only stores 1 id, what to do if multiple valid shapes?
			doc.traccar_geofence_id = geofence_id
	elif doc.doctype == "Location":
		# TODO: what to do if has geofence id - sync?
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


def wkt_format_to_geojson(wkt_string):
	# TODO: needed to sync Traccar area string to Location GeoJSON
	pass
