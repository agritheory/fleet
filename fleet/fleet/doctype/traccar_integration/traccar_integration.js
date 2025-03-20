// Copyright (c) 2024, AgriTheory and contributors
// For license information, please see license.txt

frappe.ui.form.on('Traccar Integration', {
	onload(frm) {
		if (!frm.doc.erpnext_distance_uom) {
			let global_uom = frappe.defaults.get_global_default('default_distance_unit')
			if (global_uom) {
				frm.doc.erpnext_distance_uom = global_uom
			}
		}
	},
})
