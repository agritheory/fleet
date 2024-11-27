# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt

import frappe
import pycountry


def after_install():
	install_states_and_provinces()
	install_custom_html_blocks()


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


def install_custom_html_blocks():
	vehicle_map = {
		"html": '<div id="vehicles" style="height: 500px; width: 100%;"></div>',
		"modified": "2024-11-26 18:29:00.503434",
		"name": "Vehicle Map",
		"script": "const mapContainer = root_element.querySelector('#vehicles')\nif (!mapContainer) {\n    console.error(\"Map container not found in DOM\");\n    return;\n}\n\ntry {\n    let map = L.map(mapContainer).setView([51.505, -0.09], 13);\n    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {\n        attribution: '© OpenStreetMap contributors'\n    }).addTo(map);\n    \n    frappe.xcall('fleet.fleet.workspace.get_coords').then(response => {\n        if (!response.features.features.length) {\n            console.log(\"No vehicle coordinates found\");\n            return;\n        }\n\n        // Add markers for each vehicle\n        response.features.features.forEach(feature => {\n            const [lng, lat] = feature.geometry.coordinates;\n            const marker = L.marker([lat, lng])\n                .bindPopup(`\n                    <b>Vehicle:</b> ${feature.properties.name}<br>\n                    <b>Driver:</b> ${feature.properties.driver}\n                `)\n                .addTo(map);\n        });\n\n        // Fit map to show all markers with padding\n        const bounds = L.latLngBounds([\n            [response.bounds.minLat, response.bounds.minLng],\n            [response.bounds.maxLat, response.bounds.maxLng]\n        ]);\n        map.fitBounds(bounds, {\n            padding: [50, 50] // Add 50px padding around the bounds\n        });\n    }).catch(error => {\n        console.error(\"Error fetching vehicle coordinates:\", error);\n    });\n} catch (error) {\n    console.error(\"Error initializing map:\", error);\n}",
	}
	if frappe.db.exists("Custom HTML Block", {"name": vehicle_map.name}):
		vm = frappe.new_doc("Custom HTML Block")
		vm.update(vehicle_map)
		vm.save()

	battery_voltage = {
		"docstatus": 0,
		"doctype": "Custom HTML Block",
		"html": '<div id="vehicle-battery-voltage"></div>\n',
		"modified": "2024-11-26 19:17:28.755195",
		"name": "Vehicle Battery Voltage",
		"script": "const batteryLevels = root_element.querySelector('#vehicle-battery-voltage')\nfrappe.xcall('fleet.fleet.workspace.get_battery_voltage').then(response => {\n    console.log(response)\n    batteryLevels.innerHTML = response\n})",
	}
	if frappe.db.exists("Custom HTML Block", {"name": battery_voltage.name}):
		bv = frappe.new_doc("Custom HTML Block")
		bv.update(vehicle_map)
		bv.save()
