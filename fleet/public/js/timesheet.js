// Copyright (c) 2025, AgriTheory and contributors
// For license information, please see license.txt

frappe.ui.form.on('Timesheet', {
	fetch_timesheet_from_vehicle_log: function (frm, cdt, cdn) {
		frappe.prompt(
			[
				{
					fieldtype: 'Date',
					label: 'Start Date',
					fieldname: 'start_date',
					reqd: 1,
				},
				{
					fieldtype: 'Date',
					label: 'End Date',
					fieldname: 'end_date',
					reqd: 1,
				},
			],
			function (values) {
				frappe.call({
					method: 'fleet.fleet.overrides.timesheet.fetch_timesheet_from_vehicle_log',
					args: {
						employee: frm.doc.employee,
						start_date: values.start_date,
						end_date: values.end_date,
					},
					callback: function (r) {
						if (r.message) {
							frm.clear_table('time_logs')
							;(r.message || []).forEach(function (row) {
								frm.add_child('time_logs', {
									activity_type: row.activity_type || '',
									from_time: row.entered_on || '',
									to_time: row.exited_on || '',
									hours: row.hours || 0,
								})
							})
							frm.refresh_field('time_logs')
							frappe.msgprint(__('Fetched data successfully and added to Time Logs.'))
						}
					},
				})
			},
			__('Enter Date Range'),
			__('Fetch')
		)
	},
})
