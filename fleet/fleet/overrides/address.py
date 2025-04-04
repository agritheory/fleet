# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt


import frappe
from frappe import _


def validate_single_location_in_links(doc, method=None):
	if not doc.links:
		return
	loc_count = sum([1 for link in doc.links if link.link_doctype == "Location"])
	if loc_count > 1:
		frappe.throw(
			_(
				f"Addresses may link to only one Location at a time, please remove {loc_count - 1} Location(s) in the Links table."
			)
		)
