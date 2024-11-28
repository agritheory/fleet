// Copyright (c) 2024, AgriTheory and contributors
// For license information, please see license.txt

const fleet_calendar = {
	field_map: {
		start: 'date',
		end: 'date',
		id: 'name',
		title: 'description',
		allDay: 'allDay',
		progress: 'progress',
	},
	filters: [
		{
			fieldtype: 'Link',
			fieldname: 'vehicle',
			options: 'Vehicle',
			label: __('Vehicle'),
		},
		{
			fieldtype: 'Driver',
			fieldname: 'driver',
			options: 'Driver',
			label: __('Driver'),
		},
	],
	get_events_method: 'fleet.fleet.calendar.get_events',
	get_css_class: data => {
		cur_list.calendar.color_map['purple'] = 'purple'
		cur_list.calendar.color_map['pink'] = 'pink'
		if (data.type === 'Holiday') {
			return 'success'
		} else if (data.type === 'License') {
			return 'purple'
		} else if (data.type === 'Registration') {
			return 'danger'
		} else if (data.type === 'Insurance') {
			return 'pink'
		} else if (data.type === 'Inspection') {
			return 'warning'
		}
	},
	gantt: false,
	options: {
		editable: false,
		selectable: false,
	},
}

frappe.views.calendar['Vehicle'] = {
	...fleet_calendar,
}

frappe.views.calendar['Driver'] = {
	...fleet_calendar,
}
