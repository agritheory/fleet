# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt

import frappe
import pycountry


def after_install():
	install_states_and_provinces()
	install_custom_html_blocks()


def install_states_and_provinces():
	for state in list(pycountry.subdivisions.get(country_code="US")) + list(
		pycountry.subdivisions.get(country_code="CA")
	):
		if frappe.db.exists("State", {"state": state.name}):
			continue
		s = frappe.new_doc("State")
		s.state = state.name
		s.abbr = state.code.replace(f"{state.country_code}-", "")
		s.save()


def install_custom_html_blocks():
	vehicle_map = {
		"html": '<div class="tabbed">\n\t<input type="radio" id="tab1" name="css-tabs" checked>\n\t<input type="radio" id="tab2" name="css-tabs">\n\t<input type="radio" id="tab3" name="css-tabs">\n\t\n\t<ul class="tabs">\n\t\t<li class="tab"><label for="tab1">Vehicle Map</label></li>\n\t\t<li class="tab"><label for="tab2">Fleet Calendar</label></li>\n\t\t<li class="tab"><label for="tab3">ETA Tracker</label></li>\n\t</ul>\n\t\n\t<div class="tab-content">\n\t\t<div id="vehicles" style="height: 475px; width: 100%;"></div>\n\t</div>\n\t\n\t<div class="tab-content">\n\t\t<div id="fleet-calendar" style="height: 475x; width: 100%;"></div>\n\t</div>\n\t\n\t<div class="tab-content">\n\t\t<div id="eta-report" style="height: 475px; width: 100%;"></div>\n\t</div>\n</div>',
		"name": "Fleet Home",
		"script": "const mapContainer = root_element.querySelector('#vehicles')\nif (!mapContainer) {\n    console.error(\"Map container not found in DOM\");\n    return;\n}\n\ntry {\n    let map = L.map(mapContainer).setView([51.505, -0.09], 13);\n    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {\n        attribution: '© OpenStreetMap contributors'\n    }).addTo(map);\n    \n    frappe.xcall('fleet.fleet.workspace.get_coords').then(response => {\n        if (!response.features.features.length) {\n            console.log(\"No vehicle coordinates found\");\n            return;\n        }\n\n        // Add markers for each vehicle\n        response.features.features.forEach(feature => {\n            const [lng, lat] = feature.geometry.coordinates;\n            const marker = L.marker([lat, lng])\n                .bindPopup(`\n                    <b>Vehicle:</b> ${feature.properties.name}<br>\n                    <b>Driver:</b> ${feature.properties.driver}\n                `)\n                .addTo(map);\n        });\n\n        // Fit map to show all markers with padding\n        const bounds = L.latLngBounds([\n            [response.bounds.minLat, response.bounds.minLng],\n            [response.bounds.maxLat, response.bounds.maxLng]\n        ]);\n        map.fitBounds(bounds, {\n            padding: [50, 50] // Add 50px padding around the bounds\n        });\n    }).catch(error => {\n        console.error(\"Error fetching vehicle coordinates:\", error);\n    });\n} catch (error) {\n    console.error(\"Error initializing map:\", error);\n}\n\nconst calendarContainer = $(root_element).find('#fleet-calendar');\ncalendarContainer.prepend(`\n  <link rel=\"stylesheet\" href=\"/assets/frappe/js/lib/fullcalendar/fullcalendar.min.css\">\n`);\n\nfrappe.require([\n    \"assets/frappe/js/lib/fullcalendar/fullcalendar.min.js\",\n], \n    () => {\n    let calendar = new frappe.views.Calendar({\n        doctype: 'Vehicle',\n        parent: calendarContainer,\n        page: {\n            clear_user_actions: () => {},\n            add_menu_item: () => {}\n        },\n        list_view: {\n            filter_area: {\n                get: () => []\n            }\n        },\n        field_map: {\n\t\tstart: 'date',\n\t\tend: 'date',\n\t\tid: 'name',\n\t\ttitle: 'description',\n\t\tallDay: 'allDay',\n\t\tprogress: 'progress',\n\t},\n\tfilters: [\n\t\t{\n\t\t\tfieldtype: 'Link',\n\t\t\tfieldname: 'vehicle',\n\t\t\toptions: 'Vehicle',\n\t\t\tlabel: __('Vehicle'),\n\t\t},\n\t\t{\n\t\t\tfieldtype: 'Driver',\n\t\t\tfieldname: 'driver',\n\t\t\toptions: 'Driver',\n\t\t\tlabel: __('Driver'),\n\t\t},\n\t],\n\tget_events_method: 'fleet.fleet.calendar.get_events',\n\tget_css_class: data => {\n\t\tcalendar.color_map['purple'] = 'purple'\n\t\tcalendar.color_map['pink'] = 'pink'\n\t\tif (data.type === 'Holiday') {\n\t\t\treturn 'success'\n\t\t} else if (data.type === 'License') {\n\t\t\treturn 'purple'\n\t\t} else if (data.type === 'Registration') {\n\t\t\treturn 'danger'\n\t\t} else if (data.type === 'Insurance') {\n\t\t\treturn 'pink'\n\t\t} else if (data.type === 'Inspection') {\n\t\t\treturn 'warning'\n\t\t}\n\t},\n\tgantt: false,\n\toptions: {\n\t\teditable: false,\n\t\tselectable: false,\n\t},\n    })\n})",
		"style": '.tabbed {\n\toverflow-x: hidden;\n\tpadding-bottom: 16px;\n\tborder-bottom: 1px solid var(--border-color);\n}\n\n.tabbed [type="radio"] {\n\tdisplay: none;\n}\n\n.tabs {\n\tdisplay: flex;\n\talign-items: stretch;\n\tlist-style: none;\n\tpadding: 0;\n\tborder-bottom: 1px solid var(--border-color);\n}\n.tab > label {\n\tdisplay: block;\n\tmargin-bottom: -1px;\n\tpadding: 12px 15px;\n\tborder: 1px solid var(--border-color);\n\tfont-size: 12px; \n\tfont-weight: 600;\n\tletter-spacing: 1px;\n\tcursor: pointer;\t\n\ttransition: all 0.3s;\n}\n.tab:hover label {\n\tborder-top-color: black;\n\tcolor: black;\n}\n\n.tab-content {\n\tdisplay: none;\n\tcolor: black;\n}\n\n.tabbed [type="radio"]:nth-of-type(1):checked ~ .tabs .tab:nth-of-type(1) label,\n.tabbed [type="radio"]:nth-of-type(2):checked ~ .tabs .tab:nth-of-type(2) label,\n.tabbed [type="radio"]:nth-of-type(3):checked ~ .tabs .tab:nth-of-type(3) label\n{\n\tborder-bottom-color: var(--border-color);\n\tborder-top-color: black;\n\tbackground: #fff;\n}\n\n.tabbed [type="radio"]:nth-of-type(1):checked ~ .tab-content:nth-of-type(1),\n.tabbed [type="radio"]:nth-of-type(2):checked ~ .tab-content:nth-of-type(2)\n{\n\tdisplay: block;\n}\n\n.footnote-area {\n    display: none;\n}',
	}
	if not frappe.db.exists("Custom HTML Block", {"name": vehicle_map.get("name")}):
		vm = frappe.new_doc("Custom HTML Block")
		vm.update(vehicle_map)
		vm.save()

	battery_voltage = {
		"html": '<div id="vehicle-battery-voltage"></div>\n',
		"name": "Vehicle Battery Voltage",
		"script": "const batteryLevels = root_element.querySelector('#vehicle-battery-voltage')\nfrappe.xcall('fleet.fleet.workspace.get_battery_voltage').then(response => {\n    batteryLevels.innerHTML = response\n})",
	}
	if not frappe.db.exists("Custom HTML Block", {"name": battery_voltage.get("name")}):
		bv = frappe.new_doc("Custom HTML Block")
		bv.update(battery_voltage)
		bv.save()
