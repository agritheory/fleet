# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt


import base64
import datetime
import json
import time
from urllib.parse import urljoin

import frappe
import requests
from dateutil import parser
from frappe import _
from frappe.utils.safe_exec import is_job_queued

from fleet.fleet.overrides.vehicle import schedule_poll_frequency


def sync_vehicles(traccar_settings=None):
	if not traccar_settings:
		traccar_settings = frappe.get_cached_doc("Traccar Integration", "Traccar Integration")

	if not traccar_settings or not traccar_settings.enable_traccar:
		return

	custom_cron_vehicles = frappe.get_all(
		"Vehicle",
		{"disabled": 0, "traccar_imei": ["is", "set"], "poll_frequency": ["is", "set"]},
		pluck="name",
	)

	other_vehicles = frappe.get_all(
		"Vehicle",
		{"disabled": 0, "traccar_imei": ["is", "set"], "poll_frequency": ["is", "not set"]},
		pluck="name",
	)

	for v in custom_cron_vehicles:
		v_doc = frappe.get_doc("Vehicle", v)
		schedule_poll_frequency(v_doc, update=True)

	for v in other_vehicles:
		sync_vehicle(v, traccar_settings=traccar_settings)


def sync_vehicle(vehicle, traccar_settings=None):
	if not traccar_settings:
		traccar_settings = frappe.get_cached_doc("Traccar Integration", "Traccar Integration")

	if not traccar_settings or not traccar_settings.enable_traccar:
		return

	vehicle_doc = frappe.get_doc("Vehicle", vehicle)
	try:
		position = get_vehicle_position(vehicle_doc)
		if not position:
			frappe.log_error(
				_("No position data found for vehicle {0}").format(vehicle), "Traccar Integration Error"
			)
		log = create_vehicle_log(vehicle_doc, position)

	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(), _("Failed to sync vehicle {0} with Traccar").format(vehicle)
		)


def get_vehicle_position(vehicle_doc):
	"""
	Collects last known position of vehicle_doc's Vehicle from Traccar.

	:param vehicle_doc: Vehicle doctype
	:return: position JSON object if successful, None with raised error if not
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	device_id = vehicle_doc.get("traccar_id")
	if not device_id:
		return

	try:
		response = requests.get(
			urljoin(traccar_server_url, f"/api/positions?deviceId={device_id}"),
			headers=headers,
			timeout=10,
		)
		response.raise_for_status()
		positions = response.json()
		return positions[-1] if positions else None

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Failed to connect to Traccar server: {0}").format(str(e)))


def create_vehicle_log(vehicle_doc, position):
	prior_vl = frappe.get_all(
		"Vehicle Log",
		filters={"license_plate": vehicle_doc.name, "docstatus": 1},
		fields=["employee", "geofence_ids"],
		order_by="modified desc",
		limit=1,
	)
	last_emp = prior_vl[0].employee if prior_vl else None
	prior_gf_id_str = (prior_vl[0].geofence_ids or "") if prior_vl else ""
	prior_geofence_ids = [int(s.strip()) for s in prior_gf_id_str.split(",") if s]
	gf_ids = position.get("geofenceIds") or []
	gf_changes = get_geofence_change(prior_geofence_ids, gf_ids)

	timestamp = get_datetime_from_timestamp_string(
		position.get("fixTime") or get_now_timestamp_string()
	)
	attributes = position.get("attributes", {})
	distance_cf = get_distance_conversion_factor()
	frappe.set_user("Traccar")
	if attributes.get("driverUniqueId"):
		driver_emp = frappe.get_value("Driver", attributes.get("driverUniqueId"), "employee")
	elif last_emp:
		driver_emp = last_emp
	else:
		vd = vehicle_doc.drivers[-1].driver if vehicle_doc.drivers else ""
		driver_emp = frappe.get_value("Driver", vd, "employee")

	log = frappe.new_doc("Vehicle Log")
	log.update(
		{
			"doctype": "Vehicle Log",
			"license_plate": vehicle_doc.name,
			"date": timestamp.date(),
			"employee": driver_emp,
			"odometer": int(position.get("attributes", {}).get("totalDistance", 0) * distance_cf) + 1,
			"last_odometer": vehicle_doc.last_odometer or 0,
			"latitude": position.get("latitude"),
			"longitude": position.get("longitude"),
			"battery_level": position.get("attributes", {}).get("batteryLevel"),
			"fuel_qty": attributes.get("fuel"),
			"hours": attributes.get("hours") or attributes.get("engineHours"),
			"engine_temperature": attributes.get("engineTemp") or attributes.get("temp"),
			"speed": position.get("speed"),
			"diagnostic": attributes.get("diagnostic", "")[:140],
			"rpm": attributes.get("rpm"),
			"geofence_ids": ",".join([str(id) for id in gf_ids]),
			"geofences_entered": ",".join([gf for gf in gf_changes.entered]),
			"geofences_exited": ",".join([gf for gf in gf_changes.exited]),
		}
	)
	log.save(ignore_permissions=True)
	log.submit()

	if log.diagnostic:
		asset_name = frappe.get_value("Asset", {"asset_name": vehicle_doc.name})
		if asset_name and not frappe.db.exists(
			"Asset Repair", {"asset": asset_name, "description": ["like", f"%{log.diagnostic}%"]}
		):
			job_name = f"{asset_name}-{log.diagnostic[:25]}"
			queue = "traccar"
			if not is_job_queued(job_name, queue=queue):
				frappe.enqueue(
					method=create_draft_asset_repair,
					queue=queue,
					timeout=3600,
					job_name=job_name,
					asset_name=asset_name,
					description=log.diagnostic,
				)


def get_traccar_device(device_uniqid):
	"""
	Collects device data from Traccar.

	:param device_uniqid: str; Traccar uniqueID for a device (Traccar IMEI on Vehicle)
	:return: device data JSON object if successful, None with raised error if not
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	try:
		response = requests.get(
			urljoin(traccar_server_url, f"/api/devices?uniqueId={device_uniqid}"),
			headers=headers,
			timeout=10,
		)
		response.raise_for_status()
		device = response.json()
		return device[0] if device else None

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Failed to connect to Traccar server: {0}").format(str(e)))


def add_traccar_device(vehicle_doc, method=None):
	"""
	Adds a device to Traccar if it doesn't already exist.

	:param vehicle_doc: Vehicle doctype
	:param method: str | None; method name function is called from
	:return: None (error raised if unsuccessful)
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}
	device_uniqid = vehicle_doc.traccar_imei

	if not device_uniqid:
		return

	try:
		device = get_traccar_device(device_uniqid)
		if device and not vehicle_doc.traccar_id:
			vehicle_doc.traccar_id = device["id"]

		if not device:
			data = {
				"id": int(device_uniqid),  # Traccar creates it's own ID
				"name": vehicle_doc.name,
				"uniqueId": device_uniqid,
				"status": "",
				"disabled": bool(vehicle_doc.disabled),
				"lastUpdate": int(time.time()),
				"positionId": 0,
				"groupId": 0,
				"phone": "",
				"model": vehicle_doc.model,
				"contact": "",
				"category": "",
				"attributes": {},
			}
			response = requests.post(
				urljoin(traccar_server_url, "/api/devices"),
				headers=headers,
				timeout=10,
				data=json.dumps(data),
			)
			response.raise_for_status()
			r = response.json()
			if r and r["id"]:
				vehicle_doc.traccar_id = r["id"]

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def update_traccar_device(device_id, to_update):
	"""
	Updates given keys in `to_update` if device exists in Traccar.

	:param device_id: str; Traccar device ID
	:param to_update: dict; the key-value pairs of data to update in Traccar
	:return: None (error raised if unsuccessful)
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	try:
		device = get_traccar_device(device_id)
		if not device:
			frappe.throw(_("Device does not exist in Traccar"))
		else:
			device = dict(device)
			to_update.update({"lastUpdate": int(time.time())})
			data = device.update(to_update)
			response = requests.put(
				urljoin(traccar_server_url, f"/api/devices?id={device_id}"),
				headers=headers,
				timeout=10,
				json=json.dumps(data),
			)
			response.raise_for_status()

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def delete_traccar_device(device_id):
	"""
	Deletes device in Traccar with given `device_id`.

	:param device_id: int | str; Traccar device ID
	:return: None (error raised if unsuccessful)
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	try:
		response = requests.delete(
			urljoin(traccar_server_url, f"/api/devices?id={device_id}"),
			headers=headers,
			timeout=10,
		)
		response.raise_for_status()

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def get_traccar_driver(driver_uniqid):
	"""
	Collects driver data from Traccar.

	:param driver_uniqid: str; Traccar uniqueID for a driver (name field on Driver)
	:return: driver data JSON object if successful, None with raised error if not
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	try:
		response = requests.get(
			urljoin(traccar_server_url, "/api/drivers"),
			headers=headers,
			timeout=10,
		)
		response.raise_for_status()
		drivers = response.json()
		drivers = [d for d in drivers if d["uniqueId"] == driver_uniqid] if drivers else None
		return drivers[0] if drivers else None

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Failed to connect to Traccar server: {0}").format(str(e)))


def add_traccar_driver(driver_doc, method=None):
	"""
	Adds a driver to Traccar if it doesn't already exist. The Driver document's name is uniqueId

	:param driver_doc: Driver doctype
	:param method: str | None; method name function is called from
	:return: None (error raised if unsuccessful)
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}
	driver_uniqid = driver_doc.name

	try:
		driver = get_traccar_driver(driver_uniqid)
		if driver and not driver_doc.traccar_user_id:
			driver_doc.traccar_user_id = driver["uniqueId"]

		if not driver:
			data = {
				"id": 0,  # Traccar creates it's own ID
				"name": driver_doc.full_name,
				"uniqueId": driver_uniqid,
				"attributes": {},
			}
			response = requests.post(
				urljoin(traccar_server_url, "/api/drivers"),
				headers=headers,
				timeout=10,
				data=json.dumps(data),
			)
			response.raise_for_status()
			r = response.json()
			if r and r["uniqueId"]:
				driver_doc.traccar_user_id = r["uniqueId"]

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def get_traccar_geofences(device_uniqid=None, geofence_id=None):
	"""
	Collects all geofences in Traccar. If given, collects geofences associated with either the
	`device_uniqid` (Vehicle's Traccar IMEI) or match the `geofence_id` from Traccar.

	:param device_uniqid: str | None; Traccar uniqueID for a device (Traccar IMEI on Vehicle)
	:param geofence_id: int | None; the Traccar ID field on the geofence
	:return: list; geofence data JSON objects if successful, None with raised error if not
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}
	api_url = f"?deviceId={device_uniqid}" if device_uniqid else ""
	try:
		response = requests.get(
			urljoin(traccar_server_url, "/api/geofences" + api_url),
			headers=headers,
			timeout=10,
		)
		response.raise_for_status()
		geofences = response.json()
		if geofence_id:
			geofences = [g for g in geofences if g["id"] == geofence_id]
		return geofences

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Failed to connect to Traccar server: {0}").format(str(e)))


def add_traccar_geofence(doc, shape, coords, device_ids=None, group_ids=None):
	"""
	Adds a geofence to Traccar. If `device_ids` or `group_ids` are provided, will link all devices
	and groups to the geofence.

	:param doc: doc creating geofence from (either Location or Address)
	:param shape: str; Traccar only supports polygon and polyline shapes
	:param coords: non-nested sequence of coordinates that defines the shape
	:param device_ids: str | sequence | None; Traccar deviceId for devices to link to the geofence
	:param group_ids: str | sequence | None; Traccar groupId for groups to link to the geofence
	:return: None (error raised if unsuccessful)

	Traccar only requires the name and area keys to create a new geofence. Area is a string in
	Well-Known Text (WKT) format to represent the geometry. Examples:
	"POLYGON ((lat1 lon1, lat2 lon2, lat3 lon3, lat1 lon1))"
	"LINESTRING (lat1 lon1, lat2 lon2, lat3 lon3)"
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}
	if shape.lower() not in ["polygon", "linestring"]:
		frappe.throw(
			_(
				f"Invalid shape of {shape}. Traccar only supports Polygon or Polyline (LineString) shapes for new geofences."
			)
		)
	if device_ids and isinstance(device_ids, str):
		device_ids = [device_ids]
	if group_ids and isinstance(group_ids, str):
		group_ids = [group_ids]

	try:
		area = coords_list_to_wkt_format(shape, coords)
		data = {
			"name": doc.name,
			"description": doc.name,
			"area": area,
			"attributes": {},
		}
		response = requests.post(
			urljoin(traccar_server_url, "/api/geofences"),
			headers=headers,
			timeout=10,
			data=json.dumps(data),
		)
		response.raise_for_status()
		r = response.json()
		if r and r["id"]:
			if device_ids:
				for did in device_ids:
					link_traccar_object("deviceId", did, "geofenceId", r["id"])
			if group_ids:
				for gid in group_ids:
					link_traccar_object("groupId", gid, "geofenceId", r["id"])
			return r["id"]

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def update_traccar_geofence(geofence_id, to_update):
	"""
	Updates given keys in `to_update` if geofence exists in Traccar.

	:param geofence_id: str; Traccar geofence ID
	:param to_update: dict; the key-value pairs of data to update in Traccar
	:return: None (error raised if unsuccessful)
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	try:
		response = requests.put(
			urljoin(traccar_server_url, f"/api/geofences?id={geofence_id}"),
			headers=headers,
			timeout=10,
			json=json.dumps(to_update),
		)
		response.raise_for_status()

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def delete_traccar_geofence(geofence_id):
	"""
	Deletes geofence in Traccar with given `geofence_id`.

	:param geofence_id: int | str; Traccar geofence ID
	:return: None (error raised if unsuccessful)
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	try:
		response = requests.delete(
			urljoin(traccar_server_url, f"/api/geofences?id={geofence_id}"),
			headers=headers,
			timeout=10,
		)
		response.raise_for_status()

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def link_traccar_object(first_param_key, first_param_val, second_param_key, second_param_val):
	"""
	Links one object to another in Traccar.

	:param first_param_key: str; must be "userId", "deviceId", or "groupId"
	:param first_param_val: the ID of the user, device, or group that links to second param
	:param second_param_key: str; see Traccar permissions API reference for valid keys
	https://www.traccar.org/api-reference/#tag/Permissions
	:param second_param_val: the ID of the other key that links to first param
	:return: None (error raised if unsuccessful)
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}
	if first_param_key not in ["userId", "deviceId", "groupId"]:
		frappe.throw(
			_(
				f"Invalid first parameter key name of {first_param_key}. Must by 'userId', 'deviceId', or 'groupId'."
			)
		)
	try:
		data = {first_param_key: first_param_val, second_param_key: second_param_val}
		response = requests.post(
			urljoin(traccar_server_url, "/api/permissions"),
			headers=headers,
			timeout=10,
			data=json.dumps(data),
		)
		response.raise_for_status()

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def unlink_traccar_object(first_param_key, first_param_val, second_param_key, second_param_val):
	"""
	Un-links one object from another in Traccar.

	:param first_param_key: str; must be "userId", "deviceId", or "groupId"
	:param first_param_val: the ID of the user, device, or group to un-link from second param
	:param second_param_key: str; see Traccar permissions API reference for valid keys
	https://www.traccar.org/api-reference/#tag/Permissions
	:param second_param_val: the ID of the other key that un-links from first param
	:return: None (error raised if unsuccessful)
	"""
	traccar_server_url, credentials = get_server_url_and_credentials()
	if not traccar_server_url:
		return
	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}
	if first_param_key not in ["userId", "deviceId", "groupId"]:
		frappe.throw(
			_(
				f"Invalid first parameter key name of {first_param_key}. Must by 'userId', 'deviceId', or 'groupId'."
			)
		)
	try:
		data = {first_param_key: first_param_val, second_param_key: second_param_val}
		response = requests.delete(
			urljoin(traccar_server_url, "/api/permissions"),
			headers=headers,
			timeout=10,
			data=json.dumps(data),
		)
		response.raise_for_status()

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Traccar server error: {0}").format(str(e)))


def create_draft_asset_repair(asset_name, description):
	company, cost_center = frappe.db.get_value("Asset", asset_name, ["company", "cost_center"])
	ar = frappe.new_doc("Asset Repair")
	ar.asset = asset_name
	ar.company = company
	ar.failure_date = frappe.utils.get_datetime()
	ar.cost_center = cost_center
	ar.description = description
	ar.save()


def get_server_url_and_credentials():
	"""
	Returns tuple with Traccar server url and access credentials
	"""
	traccar_settings = frappe.get_cached_doc("Traccar Integration", "Traccar Integration")
	if not traccar_settings or not traccar_settings.enable_traccar:
		return None, None

	credentials = base64.b64encode(
		f"{traccar_settings.username}:{traccar_settings.get_password()}".encode()
	).decode()

	return traccar_settings.traccar_server_url, credentials


def get_now_timestamp_string():
	"""
	Returns a string of current UTC timestamp in IS0 8601 format
	"""
	timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
	return timestamp


def get_datetime_from_timestamp_string(timestamp):
	"""
	Given a string in ISO 8601 format, returns a datetime.datetime object.

	:param timestamp: a timestamp string in ISO 8601 format
	:return: datetime.datetime from timestamp string
	"""
	if not timestamp:
		return
	dt = parser.parse(timestamp)
	return dt


def get_distance_conversion_factor():
	traccar_settings = frappe.get_cached_doc("Traccar Integration", "Traccar Integration")
	dist_cf = traccar_settings.distance_conversion_factor
	return frappe.get_value("UOM Conversion Factor", dist_cf, "value") if dist_cf else 1


def coords_list_to_wkt_format(shape, coords):
	"""
	Creates a Well-Known Text string to represent the geometry of the given shape and coords.
	Wikipedia reference: https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry

	:param shape: string; either LINESTRING or POLYGON
	:param coords: sequence of sequences containing coordinate pairs describing the given shape
	:return: a WKT-formatted string with given shape's geometry
	"""
	coord_string = ", ".join([f"{lat} {lon}" for lat, lon in coords])
	if shape.lower() == "linestring":
		area = f"{shape.upper()} ({coord_string})"
	else:
		area = f"{shape.upper()} (({coord_string}))"
	return area


def get_geofence_change(prior_geofence_ids, current_geofence_ids):
	"""
	Returns a dict with "entered" and "exited" keys with respective lists of the geofence names.

	:param prior_geofence_ids: list | None; value in prior Vehicle Log's geofence_ids field
	:param current_geofence_ids: list | None; geofenceIds value in Vehicle's current Traccar
	position data
	:return: dict | None; {"entered": [geofence_name, ...], "exited": [geofence_name, ,,,]}
	"""
	prior = set(prior_geofence_ids) if prior_geofence_ids else set()
	current = set(current_geofence_ids) if current_geofence_ids else set()
	if prior == current:
		entered, exited = [], []
	else:
		entered = [
			frappe.get_value("Location", {"traccar_geofence_id": gfid}) for gfid in list(current - prior)
		]
		exited = [
			frappe.get_value("Location", {"traccar_geofence_id": gfid}) for gfid in list(prior - current)
		]
	return frappe._dict({"entered": entered, "exited": exited})
