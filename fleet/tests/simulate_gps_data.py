# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt


import math
import random
import time
from itertools import cycle
from urllib.parse import urljoin

import frappe
import requests

from fleet.fleet.traccar import get_server_url_and_credentials
from fleet.tests.fixtures.locations_and_routes import routes


def simulate(port=5055):
	traccar_server_url, credentials = get_server_url_and_credentials()
	traccar_server_url = traccar_server_url or f"http://localhost:{port}"
	if credentials:
		headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}
	else:
		headers = {"Content-Type": "application/json"}

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
	usage_dict = {v.name: v.last_odometer for v in vehicles}
	last_position = {r["vehicle"]: r["route"][-1] for r in routes}
	driver_dict = {
		v.name: frappe.get_value("Vehicle Driver", {"parent": v.name}, "driver") for v in vehicles
	}

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
				lat_0, lon_0 = last_position[vehicle.name]
				lat_1, lon_1 = next(vehicle_routes[vehicle.name])
				bearing = get_bearing(lat_0, lon_0, lat_1, lon_1)
				last_position[vehicle.name] = (lat_1, lon_1)
				# usage = float(vehicle.last_odometer)  # replace usage dict if syncing vehicles
				usage = usage_dict[vehicle.name]

				if vehicle.make in ["Kubota", "Bobcat"]:
					usage += round(random.uniform(0.01, 0.05), 2)  # Engine hours
					usage_param = "hours"
				else:
					# Traccar distance default is km
					usage += round(random.uniform(0.05, 0.3), 2)  # Odometer distance
					usage_param = "odometer"
				usage_dict[vehicle.name] = usage
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
				speed = (  # Traccar default is knots (1 knot = 1.15 mph = 1.852 km/h)
					random.randint(5, 15) if vehicle.fuel_type == "Diesel" else random.randint(30, 70)
				)
				altitude = random.randint(10, 300)

				data = {
					"id": vehicle.traccar_imei,
					"timestamp": int(time.time()),
					"lat": lat_1,
					"lon": lon_1,
					"altitude": altitude,
					"bearing": bearing,
					"speed": speed,
					"batt": batt,
					"temp": temp,
					"fuel": fuel_level,
					usage_param: usage,
					"driverUniqueId": driver_dict.get(vehicle.name, ""),
				}
				if vehicle.name == "3812947":
					data["alarm"] = "check-engine"  # or 'malfunction' is also commonly used

				response = requests.post(urljoin(traccar_server_url, "/"), headers=headers, data=data)
				response.raise_for_status()
				print(
					f"Vehicle: {vehicle.name}, Position: {lat_1}, {lon_1}, Speed: {speed}, Usage: {usage}, Fuel: {fuel_level}"
				)

			time.sleep(5)
	except KeyboardInterrupt:
		print("\nStopping simulator...")


def get_bearing(lat1, lon1, lat2, lon2):
	lat1 = lat1 * math.pi / 180
	lon1 = lon1 * math.pi / 180
	lat2 = lat2 * math.pi / 180
	lon2 = lon2 * math.pi / 180
	y = math.sin(lon2 - lon1) * math.cos(lat2)
	x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
	return (math.atan2(y, x) % (2 * math.pi)) * 180 / math.pi
