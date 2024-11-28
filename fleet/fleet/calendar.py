# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt


import frappe
from frappe.utils.data import get_first_day, get_last_day


@frappe.whitelist()
def get_events(doctype, start=None, end=None, field_map=None, filters=None, fields=None):
	events = []
	if not start:
		start = get_first_day()
	if not end:
		end = get_last_day()
	vehicles = frappe.get_list(
		"Vehicle", ["name", "registration_expiration_date AS date", "end_date"]
	)  # TODO add inspection date
	drivers = frappe.get_list("Driver", ["name", "expiry_date", "full_name"])
	# TODO: combine into single query licenses = frappe.get_all('Driving License Category', ['parent', 'expiry_date'])
	for v in vehicles:
		if v.registration_expiration_date:
			events.append(
				{
					"name": v.name,
					"description": v.name + frappe._(" Registration Expiration"),
					"date": v.registration_expiration_date,
					"allDay": True,
					"type": "Registration",
				}
			)
		if v.end_date:
			events.append(
				{
					"name": v.name,
					"description": v.name + frappe._(" Insurance Expiration"),
					"date": v.end_date,
					"allDay": True,
					"type": "Insurance",
				}
			)
	for d in drivers:
		if d.expiry_date:
			events.append(
				{
					"name": d.name,
					"description": d.name + frappe._(" License Expiration"),
					"date": d.expiry_date,
					"allDay": True,
					"type": "License",
				}
			)

	holidays = frappe.get_all("Holiday", ["parent", "holiday_date", "description"])
	for h in holidays:
		if h.holiday_date:
			events.append(
				{
					"description": h.description,
					"date": h.holiday_date,
					"allDay": True,
					"type": "Holiday",
				}
			)

	return events
