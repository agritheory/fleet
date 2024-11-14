# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt

import frappe
import pycountry


def install_states_and_provinces():
	for state in pycountry.subdivisions.get(country_code="US") + pycountry.subdivisions.get(
		country_code="CA"
	):
		if frappe.db.exists("State", {"state": state.name}):
			continue
		s = frappe.new_doc("State")
		s.state = state.name
		s.abbr = state.code.replace(f"{state.country_code}-")
		s.save()
