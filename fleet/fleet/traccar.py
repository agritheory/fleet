# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime
import requests
from urllib.parse import urljoin
import base64


def sync_vehicle(vehicle, traccar_settings=None):
	if not traccar_settings:
		traccar_settings = frappe.get_cached_doc("Traccar Integration", "Traccar Integration")

	if not traccar_settings.enable_traccar:
		return

	vehicle_doc = frappe.get_doc("Vehicle", vehicle)
	try:
		position_data = get_vehicle_position(vehicle_doc, traccar_settings)
		if not position_data:
			frappe.log_error(
				_("No position data found for vehicle {0}").format(vehicle), "Traccar Integration Error"
			)
		log = create_vehicle_log(vehicle_doc, position_data, traccar_settings)

	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(), _("Failed to sync vehicle {0} with Traccar").format(vehicle)
		)


def get_vehicle_position(vehicle_doc, traccar_settings):
	credentials = base64.b64encode(
		f"{traccar_settings.username}:{traccar_settings.get_password()}".encode()
	).decode()

	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	device_id = vehicle_doc.get("tracker_imei")
	if not device_id:
		frappe.throw(_("Traccar Device ID not configured for vehicle {0}").format(vehicle_doc.name))

	try:
		response = requests.get(
			urljoin(traccar_settings.traccar_server_url, f"/api/positions?deviceId={device_id}"),
			headers=headers,
			timeout=10,
		)
		response.raise_for_status()
		positions = response.json()
		return positions[-1] if positions else None

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Failed to connect to Traccar server: {0}").format(str(e)))


def create_vehicle_log(vehicle_doc, position_data):
	timestamp = datetime.fromtimestamp(position_data.get("fixTime") / 1000)

	log = frappe.new_doc("Vehicle Log")
	log.update(
		{
			"doctype": "Vehicle Log",
			"license_plate": vehicle_doc.name,
			"date": timestamp.date(),
			"employee": vehicle_doc.employee,
			"odometer": int(
				position_data.get("attributes", {}).get("totalDistance", 0) / 1000
			),  # TODO:  /1000 Convert to km, use settings for distance units
			"last_odometer": vehicle_doc.last_odometer or 0,
			"latitude": position_data.get("latitude"),
			"longitude": position_data.get("longitude"),
			"battery_level": position_data.get("attributes", {}).get("batteryLevel"),
		}
	)

	log.save()
	log.submit()
