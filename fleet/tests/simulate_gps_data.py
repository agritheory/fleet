# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt


import random
import socket
import time
from itertools import cycle

import frappe

from fleet.fleet.traccar import get_now_timestamp_string
from fleet.tests.fixtures.locations_and_routes import routes


def simulate(port=5055):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(("localhost", port))

	vehicles = frappe.get_all(
		"Vehicle",
		filters={"disabled": False},
		fields=[
			"name",
			"chassis_no",
			"last_odometer",
			# "gps_location",  # class property, need to grab off instance
			"make",
			"fuel_type",
			"traccar_imei",
			"traccar_id",
		],
	)
	vehicle_routes = frappe._dict({r["vehicle"]: cycle(r["route"]) for r in routes})
	# usage_dict = frappe._dict({v.name: v.last_odometer for v in vehicles})
	try:
		while True:
			for vehicle in vehicles:
				# Get latest fuel level
				fuel_log = frappe.get_all(
					"Vehicle Log",
					filters={"license_plate": vehicle.name},
					fields=["fuel_qty"],
					order_by="date desc",
					limit=1,
				)
				fuel_level = fuel_log[0].fuel_qty if fuel_log else 0
				lat, lon = next(vehicle_routes[vehicle.name])
				usage = float(vehicle.last_odometer)
				# usage = usage_dict[vehicle.name]

				if vehicle.make in ["Kubota", "Bobcat"]:
					usage += round(random.uniform(0.01, 0.05), 2)  # Engine hours
					usage_param = f"hours={usage:.1f}"
				else:
					usage += round(random.uniform(0.05, 0.3), 2)  # Odometer miles
					usage_param = f"odometer={usage:.1f}"
				# usage_dict[vehicle.name] += usage
				batt = (
					round(random.uniform(23.8, 24.2), 2)
					if vehicle.fuel_type == "Diesel"
					else round(random.uniform(11.8, 12.4), 2)
				)
				temp = (
					round(random.uniform(85, 95), 2)
					if vehicle.fuel_type == "Diesel"
					else round(random.uniform(75, 85), 2)
				)

				timestamp = get_now_timestamp_string()

				if vehicle.name == "3812947":
					alarm_param = "&alarm=check-engine"  # or 'malfunction' is also commonly used
				else:
					alarm_param = ""

				data = (
					f"?id={vehicle.traccar_id}&lat={lat}&lon={lon}&timestamp={timestamp}"
					f"&batt={batt:.1f}&temp={temp:.1f}&{usage_param}&fuel={fuel_level}{alarm_param}\r\n"
				)

				sock.send(data.encode())
				print(f"Vehicle: {vehicle.name}, Position: {lat}, {lon}, Usage: {usage}, Fuel: {fuel_level}")

			time.sleep(5)
	except KeyboardInterrupt:
		print("\nStopping simulator...")
	finally:
		sock.close()
