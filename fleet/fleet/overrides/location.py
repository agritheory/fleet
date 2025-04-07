# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import comma_and

from fleet.fleet.traccar import (
	add_traccar_geofence,
	coords_list_to_wkt_format,
	delete_traccar_geofence,
	link_traccar_object,
	unlink_traccar_object,
	update_traccar_geofence,
)


def validate_geofence_geometry(doc, method=None):
	# check for at least one valid geofence geometry, and no more than one
	if not doc.sync_traccar_geofence:
		return
	loc = json.loads(doc.location)
	if not has_valid_feature_type(loc):
		frappe.throw(
			_(
				"No valid geometry features (polyline, polygon, or rectangle) found on map to use as geofence. Note that Traccar no longer supports the circle shape to create a new geofence."
			)
		)

	gf_feature_count = 0
	for feature in loc["features"]:
		feat_type = feature.get("geometry", {}).get("type")
		gf_feature_count += 1 if feat_type in ["LineString", "Polygon"] else 0
	if gf_feature_count > 1:
		frappe.throw(
			_(
				"Multiple valid features found to create a geofence in the location field - please limit to one polygon, rectangle, or polyline."
			)
		)


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
	Syncs geofences and links vehicles to geofence if "sync_traccar_geofence" box checked.

	If there's an existing synced geofence and "sync_traccar_geofence" is unchecked, deletes
	geofence from Traccar.
	If it's a synced geofence and the geometry changed in the "location" field, updates in Traccar
	If it's a synced geofence and the vehicles changed, updates links in Traccar
	If it's a new geofence, creates it in Traccar and links vehicles
	"""
	if doc.doctype not in ["Address", "Location"]:
		return

	if doc.doctype == "Address":
		for link in doc.links:
			if link.link_doctype == "Location":
				doc = frappe.get_doc("Location", link.link_name)
	old_doc = doc.get_doc_before_save()
	loc = json.loads(doc.location)

	if not doc.sync_traccar_geofence:
		if old_doc and old_doc.sync_traccar_geofence and old_doc.traccar_geofence_id:
			# user un-checked a geofence that was synced with Traccar -> delete from Traccar
			try:
				delete_traccar_geofence(old_doc.traccar_geofence_id)
				doc.traccar_geofence_id = ""
				doc.geofenced_vehicle = []
			except ValidationError as e:
				frappe.log_error(
					title=_(
						f"Error deleting geofence from Traccar with ID {old_doc.traccar_geofence_id} for {doc.doctype} {doc.name}."
					),
					message=_(f"{e}\n\n{frappe.get_traceback()}"),
					reference_doctype=doc.doctype,
					reference_name=doc.name,
				)

	elif doc.traccar_geofence_id:
		if doc.has_value_changed("location"):
			# geometry in Location changed, update geofence
			for feature in loc["features"]:
				feat_type = feature.get("geometry", {}).get("type")
				if feat_type not in ["LineString", "Polygon"]:
					continue
				coords = []
				flatten_coordinates(coord_list=coords, item=feature["geometry"]["coordinates"])
				new_area = coords_list_to_wkt_format(feat_type, coords)
				data = {"area": new_area}
				update_traccar_geofence(doc.traccar_geofence_id, data)

		if not doc.is_child_table_same("geofenced_vehicle") and old_doc:
			# vehicles to link geofence to changed, update Traccar links
			old_vehicles = [v.vehicle for v in old_doc.geofenced_vehicle]
			new_vehicles = [v.vehicle for v in doc.geofenced_vehicle]
			added = set(new_vehicles) - set(old_vehicles)
			removed = set(old_vehicles) - set(new_vehicles)
			for added_v in added:
				did = frappe.get_value("Vehicle", added_v, "traccar_id")
				link_traccar_object("deviceId", did, "geofenceId", doc.traccar_geofence_id)
			for removed_v in removed:
				did = frappe.get_value("Vehicle", removed_v, "traccar_id")
				unlink_traccar_object("deviceId", did, "geofenceId", doc.traccar_geofence_id)

	elif not doc.traccar_geofence_id:
		# new geofence, create in Traccar and link vehicles
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
