const mapContainer = root_element.querySelector('#vehicles')
if (!mapContainer) {
	console.error('Map container not found in DOM')
}

let map = L.map(mapContainer).setView([51.505, -0.09], 13)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
	attribution: '© OpenStreetMap contributors',
}).addTo(map)

frappe
	.xcall('fleet.fleet.workspace.get_coords')
	.then(response => {
		if (!response.features.features.length) {
			console.log('No vehicle coordinates found')
			return
		}

		const latlngs = []
		let companyCoords = null

		response.features.features.forEach(feature => {
			const [lng, lat] = feature.geometry.coordinates
			const coords = [lat, lng]
			latlngs.push(coords)

			const marker = L.marker(coords)
				.bindPopup(
					`
                ${!feature.properties.is_company_address ? `<b>Vehicle</b>` : '<b>Address</b>'} ${feature.properties.name}
                ${feature.properties.driver ? `<b>Driver:</b> ${feature.properties.driver}<br>` : ''}
            `
				)
				.addTo(map)

			if (feature.properties.is_company_address) {
				companyCoords = coords
				marker.bindTooltip('Company', {
					permanent: true,
					direction: 'top',
				})
			}
		})

		if (latlngs.length) {
			const bounds = L.latLngBounds(latlngs)

			// Fit the map to show all markers with some padding
			map.fitBounds(bounds, { padding: [50, 50] })

			// Optionally shift the map view slightly towards the company
			if (companyCoords) {
				setTimeout(() => {
					// Get current center after fitBounds is applied
					const currentCenter = map.getCenter()

					const hqLat = companyCoords[0]
					const hqLng = companyCoords[1]

					// Calculate new center between the map's current center and the company location.
					// This softens the re-centering effect while still giving prominence to HQ.
					const adjustedLat = (currentCenter.lat + hqLat) / 2
					const adjustedLng = (currentCenter.lng + hqLng) / 2

					map.panTo([adjustedLat, adjustedLng])
				}, 500) // Wait a bit to ensure fitBounds animation completes
			}
		}
	})
	.catch(error => {
		console.error('Error fetching vehicle coordinates:', error)
	})

const calendarContainer = $(root_element).find('#fleet-calendar')
calendarContainer.prepend(`
  <link rel="stylesheet" href="/assets/frappe/js/lib/fullcalendar/fullcalendar.min.css">
`)

frappe.require(['assets/frappe/js/lib/fullcalendar/fullcalendar.min.js'], () => {
	let calendar = new frappe.views.Calendar({
		doctype: 'Vehicle',
		parent: calendarContainer,
		page: {
			clear_user_actions: () => {},
			add_menu_item: () => {},
		},
		list_view: {
			filter_area: {
				get: () => [],
			},
		},
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
			calendar.color_map['purple'] = 'purple'
			calendar.color_map['pink'] = 'pink'
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
	})
})

const etaTracker = root_element.querySelector('#eta-report')
frappe.xcall('fleet.fleet.workspace.get_eta').then(response => {
	etaTracker.innerHTML = response
})
