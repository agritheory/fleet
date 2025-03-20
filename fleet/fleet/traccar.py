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


def sync_vehicle(vehicle=None, traccar_settings=None):
	if not traccar_settings:
		traccar_settings = frappe.get_cached_doc("Traccar Integration", "Traccar Integration")

	if not traccar_settings or not traccar_settings.enable_traccar:
		return

	if not vehicle:
		vehicles = frappe.get_all(
			"Vehicle", {"disabled": 0, "traccar_imei": ["is", "set"]}, pluck="name"
		)
	else:
		vehicles = [vehicle]

	for v in vehicles:
		vehicle_doc = frappe.get_doc("Vehicle", v)
		try:
			position = get_vehicle_position(vehicle_doc)
			if not position:
				frappe.log_error(
					_("No position data found for vehicle {0}").format(v), "Traccar Integration Error"
				)
			log = create_vehicle_log(vehicle_doc, position)

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Failed to sync vehicle {0} with Traccar").format(v))


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
	timestamp = get_datetime_from_timestamp_string(
		position.get("fixTime") or get_now_timestamp_string()
	)
	attributes = position.get("attributes", {})
	distance_cf = get_distance_conversion_factor()
	frappe.set_user("Traccar")
	if attributes.get("driverUniqueId"):
		driver_emp = frappe.get_value("Driver", attributes.get("driverUniqueId"), "employee")
	else:
		last_emp = frappe.get_all(
			"Vehicle Log",
			filters={"license_plate": vehicle_doc.name, "docstatus": 1},
			fields=["employee"],
			order_by="modified desc",
			limit=1,
			pluck="employee",
		)
		driver_emp = last_emp[0]
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
			"engine_temperature": attributes.get("engineTemp"),
			"speed": position.get("speed"),
			"diagnostic": attributes.get("diagnostic", "")[:140],
			"rpm": attributes.get("rpm"),
		}
	)
	log.save(ignore_permissions=True)
	log.submit()

	if log.diagnostic:
		...  # enqueue creation of Asset Maintenance if an open does not already exist


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
