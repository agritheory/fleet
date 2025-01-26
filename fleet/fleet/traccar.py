# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime
import requests
from urllib.parse import urljoin
import base64


def sync_vehicle(vehicle, traccar_settings=None):
	"""
	Synchronize vehicle data from Traccar to ERPNext Vehicle Log

	Args:
	        vehicle (str): Vehicle license plate/ID
	        traccar_settings (Document, optional): Traccar Integration settings document

	Returns:
	        Document: Created/Updated Vehicle Log document
	"""
	if not frappe.db.exists("Vehicle", vehicle):
		frappe.throw(_("Vehicle {0} does not exist").format(vehicle))

	if not traccar_settings:
		traccar_settings = frappe.get_cached_doc("Traccar Integration", "Traccar Integration")

	if not traccar_settings.enable_traccar:
		return

	vehicle_doc = frappe.get_doc("Vehicle", vehicle)

	# Get vehicle position from Traccar
	try:
		position_data = get_vehicle_position(vehicle_doc, traccar_settings)
		if not position_data:
			frappe.log_error(
				_("No position data found for vehicle {0}").format(vehicle), "Traccar Integration"
			)
			return

		# Create vehicle log
		log = create_vehicle_log(vehicle_doc, position_data, traccar_settings)
		return log

	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(), _("Failed to sync vehicle {0} with Traccar").format(vehicle)
		)
		raise


def get_vehicle_position(vehicle_doc, traccar_settings):
	"""Get the latest position data for a vehicle from Traccar"""
	# Prepare authentication
	credentials = base64.b64encode(
		f"{traccar_settings.username}:{traccar_settings.password}".encode()
	).decode()

	headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

	# Get device ID from vehicle (assuming it's stored in a custom field)
	device_id = vehicle_doc.get("traccar_device_id")
	if not device_id:
		frappe.throw(_("Traccar Device ID not configured for vehicle {0}").format(vehicle_doc.name))

	# Make API request to Traccar
	try:
		response = requests.get(
			urljoin(traccar_settings.traccar_server_url, f"/api/positions?deviceId={device_id}"),
			headers=headers,
			timeout=10,
		)
		response.raise_for_status()
		positions = response.json()

		# Return the latest position
		return positions[-1] if positions else None

	except requests.exceptions.RequestException as e:
		frappe.throw(_("Failed to connect to Traccar server: {0}").format(str(e)))


def create_vehicle_log(vehicle_doc, position_data, traccar_settings):
	"""Create a Vehicle Log entry from Traccar position data"""
	# Convert timestamp to datetime
	timestamp = datetime.fromtimestamp(position_data.get("fixTime") / 1000)

	log = frappe.get_doc(
		{
			"doctype": "Vehicle Log",
			"license_plate": vehicle_doc.name,
			"date": timestamp.date(),
			"employee": vehicle_doc.employee,
			"odometer": int(
				position_data.get("attributes", {}).get("totalDistance", 0) / 1000
			),  # Convert to km
			"last_odometer": vehicle_doc.last_odometer or 0,
			"notes": frappe.as_json(
				{
					"latitude": position_data.get("latitude"),
					"longitude": position_data.get("longitude"),
					"speed": position_data.get("speed"),
					"battery_level": position_data.get("attributes", {}).get("batteryLevel"),
					"external_battery": position_data.get("attributes", {}).get("extBatteryLevel"),
				}
			),
		}
	)

	# Check battery levels and create notifications if configured
	check_battery_levels(log, position_data, traccar_settings)

	log.save()
	log.submit()


def check_battery_levels(log, position_data, traccar_settings):
	"""Check battery levels and create notifications if thresholds are exceeded"""
	if not traccar_settings.battery_level_notification:
		return

	ext_battery = position_data.get("attributes", {}).get("extBatteryLevel")
	if (
		ext_battery is not None
		and traccar_settings.external_battery_low_threshold
		and ext_battery < traccar_settings.external_battery_low_threshold
	):

		notification = frappe.get_doc("Notification", traccar_settings.battery_level_notification)
		notification.send_notification(
			doc=log,
			message=_("External battery level is low ({0}%) for vehicle {1}").format(
				ext_battery, log.license_plate
			),
		)
