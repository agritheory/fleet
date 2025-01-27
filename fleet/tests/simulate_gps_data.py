# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

import socket
import time
from datetime import datetime
import random
import frappe


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
			"gps_location",
			"make",
			"fuel_type",
			"traccar_iemi",
		],
	)

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

				lat = 43.2081  # Manchester, NH
				lon = -71.5376
				usage = float(vehicle.last_odometer)
				lat += random.uniform(-0.001, 0.001)
				lon += random.uniform(-0.001, 0.001)

				if vehicle.make in ["Kubota", "Bobcat"]:
					usage += random.uniform(0.01, 0.05)  # Engine hours
					usage_param = f"hours={usage:.1f}"
				else:
					usage += random.uniform(0.1, 0.5)  # Odometer miles
					usage_param = f"odometer={usage:.1f}"

				batt = (
					random.uniform(23.8, 24.2) if vehicle.fuel_type == "Diesel" else random.uniform(11.8, 12.4)
				)
				temp = random.uniform(85, 95) if vehicle.fuel_type == "Diesel" else random.uniform(75, 85)

				timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

				if vehicle.name == "3812947":
					alarm_param = "&alarm=check-engine"  # or 'malfunction' is also commonly used
				else:
					alarm_param = ""

				data = (
					f"?id={vehicle.traccar_iemi}&lat={lat}&lon={lon}&timestamp={timestamp}"
					f"&batt={batt:.1f}&temp={temp:.1f}&{usage_param}&fuel={fuel_level}{alarm_param}\r\n"
				)

				sock.send(data.encode())
				print(f"Vehicle: {vehicle.name}, Position: {lat}, {lon}, Usage: {usage}, Fuel: {fuel_level}")

			time.sleep(5)
	except KeyboardInterrupt:
		print("\nStopping simulator...")
	finally:
		sock.close()
