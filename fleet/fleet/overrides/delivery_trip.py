# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING

import frappe
import requests
import vroom

if TYPE_CHECKING:
	from erpnext.stock.doctype.delivery_trip.delivery_trip import DeliveryTrip


def get_geocode_from_address(address: str) -> tuple:
	# Placeholder function, location should be populated on address entry
	url = "https://nominatim.openstreetmap.org/search"
	params = {"q": address, "format": "json", "limit": "1"}
	headers = {"User-Agent": "fleet/1.0 (cole@agritheory.dev)"}
	try:
		response = requests.get(url, params=params, headers=headers)
		response.raise_for_status()
		data = response.json()
		loc = data[0]["lat"], data[0]["lon"]
		return loc
	except requests.exceptions.RequestException as e:
		frappe.log_error(f"Error fetching geocode for address {address}: {e}")
		return None
	except IndexError:
		frappe.log_error(f"No geocode found for address {address}")
		return None


class Delivery:
	def __init__(self, id, stop):
		self.id = id
		self.stop = stop
		self.location = (stop["lat"], stop["lng"])

	def __repr__(self):
		return f"Deliveries({self.id})"


def tsp_vehicle_solver(deliveries: list[Delivery], vehicle_location: tuple):
	problem_instance = vroom.Input(
		servers={"auto": "valhalla1.openstreetmap.de:443"}, router=vroom._vroom.ROUTER.VALHALLA
	)
	problem_instance.add_vehicle(vroom.Vehicle(1, start=vehicle_location, profile="auto"))
	problem_instance.add_job([vroom.Job(deliv.id, location=deliv.location) for deliv in deliveries])
	sol = problem_instance.solve(exploration_level=5, nb_threads=4).to_dict()["routes"]
	return sol


@frappe.whitelist()
def optimize_path(doc: "DeliveryTrip") -> list:
	# Get locations of deliveries
	if isinstance(doc, str):
		doc = frappe.get_doc("Delivery Trip", doc).as_dict()
	deliveries = [Delivery(i, stop) for i, stop in enumerate(doc["delivery_stops"])]

	# Get vehicle location
	# veh = doc["vehicle"]
	# TODO: Placeholder for vehicle location
	veh = deliveries[0].location

	# TSP optimization
	sol = tsp_vehicle_solver(deliveries, veh)

	# Return optimized path
	optimized_order = [i["id"] for i in sol[0]["steps"] if i.get("id") != None]
	sorted_deliveries = sorted(deliveries, key=lambda d: optimized_order.index(d.id))
	sorted_stops = [d.stop for d in sorted_deliveries]
	return sorted_stops
