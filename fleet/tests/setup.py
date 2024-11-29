# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt
from pathlib import Path
import json

import unicodedata

import frappe
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
from frappe.utils.data import getdate
from test_utils.utils.chart_of_accounts import setup_chart_of_accounts


def before_test(company_name=None):
	frappe.clear_cache()
	today = frappe.utils.getdate()
	setup_complete(
		{
			"currency": "USD",
			"full_name": "Administrator",
			"company_name": "Quincy Cloudberry Farm",
			"timezone": "America/New_York",
			"company_abbr": "QCF",
			"domains": ["Distribution"],
			"country": "United States",
			"fy_start_date": today.replace(month=1, day=1).isoformat(),
			"fy_end_date": today.replace(month=12, day=31).isoformat(),
			"language": "english",
			"company_tagline": "Quincy Cloudberry Farm",
			"email": "Administrator",
			"password": "admin",
			"chart_of_accounts": "Standard with Numbers",
			"bank_account": "Primary Checking",
		}
	)
	for modu in frappe.get_all("Module Onboarding"):
		frappe.db.set_value("Module Onboarding", modu, "is_complete", 1)
	frappe.set_value("Website Settings", "Website Settings", "home_page", "login")
	frappe.db.commit()
	create_test_data()


def create_test_data(company_name="Quincy Cloudberry Farm"):
	setup_chart_of_accounts(company=company_name, chart_template="Farm")

	settings = frappe._dict(
		{
			"day": frappe.get_all(
				"Fiscal Year",
				"year_start_date",
				order_by="year_start_date ASC",
				limit_page_length=1,
				pluck="year_start_date",
			)[0],
			"company": company_name,
		}
	)
	# setup_accounts(settings)
	settings.company_account = frappe.get_value(
		"Account", {"account_type": "Bank", "company": company_name, "is_group": 0}
	)
	setup_farm_price_list()
	create_farm_shifts()
	company_address = frappe.new_doc("Address")
	company_address.title = settings.company
	company_address.address_type = "Office"
	company_address.address_line1 = "67C Sweeny Street"
	company_address.city = "Chelsea"
	company_address.state = "MA"
	company_address.pincode = "89077"
	company_address.is_your_company_address = 1
	company_address.append("links", {"link_doctype": "Company", "link_name": settings.company})
	company_address.save()
	co = frappe.get_doc("Company", company_name)
	co.tax_id = "04-9000561"
	co.domain = "quincycloudberry.farm"
	co.save()
	create_farm_employees()
	setup_farm_price_list()


def create_farm_shifts():
	if not frappe.db.exists("Shift Type", "Farm Shift - QCF"):
		es = frappe.new_doc("Shift Type")
		es.name = "Farm Shift - QCF"
		es.start_time = "07:00:00"
		es.end_time = "03:00:00"
		es.save()
	if not frappe.db.exists("Shift Type", "Office Hours - QFC"):
		ls = frappe.new_doc("Shift Type")
		ls.name = "Office Hours - QCF"
		ls.start_time = "09:00:00"
		ls.end_time = "05:00:00"
		ls.save()


def create_farm_employees(company_name=None):
	company_name = "Quincy Cloudberry Farm" if not company_name else company_name
	settings = frappe._dict({"company": company_name, "shift_map": shift_map})
	create_employees(settings, employees)


shift_map = frappe._dict(
	{
		"Operations": ["Farm Shift - QCF"],
		"Management": ["Office Hours - QCF"],
	}
)

employees = [
	{
		"name": "Merlin Barber",
		"gender": "Male",
		"date_of_birth": "1982-04-29",
		"date_of_joining": "2018-01-01",
		"address": {
			"address_line1": "1321 Mcdowell Shore",
			"city": "Willmar",
			"state": "RI",
			"postal_code": "72012",
		},
		"phone": "(651) 911-2851",
	},
	{
		"name": "Luanna Molina",
		"gender": "Female",
		"date_of_birth": "2001-04-02",
		"date_of_joining": "2018-01-01",
		"address": {
			"address_line1": "1001 Ramsel Street",
			"city": "Kirksville",
			"state": "VT",
			"postal_code": "60864",
		},
		"phone": "(895) 295-4847",
	},
	{
		"name": "Howard Sharp",
		"gender": "Male",
		"date_of_birth": "1976-01-06",
		"date_of_joining": "2018-01-01",
		"address": {
			"address_line1": "1044 Vara Viaduct",
			"city": "Topeka",
			"state": "CT",
			"postal_code": "01238",
		},
		"phone": "(122) 785-7428",
		"roles": ["Driver"],
	},
	{
		"name": "Dylan Lucas",
		"gender": "Male",
		"date_of_birth": "2000-07-17",
		"date_of_joining": "2018-01-01",
		"address": {
			"address_line1": "269 Edith Park",
			"city": "Edwardsville",
			"state": "NH",
			"postal_code": "81485",
		},
		"phone": "(602) 012-4480",
		"roles": ["Driver"],
	},
	{
		"name": "Bibi Bishop",
		"gender": "Other",
		"date_of_birth": "1972-03-13",
		"date_of_joining": "2018-01-01",
		"address": {
			"address_line1": "914 Fortuna Park",
			"city": "Dinuba",
			"state": "VT",
			"postal_code": "63243",
		},
		"phone": "(396) 509-0076",
	},
	{
		"name": "Issac Abbott",
		"gender": "Male",
		"date_of_birth": "1986-02-02",
		"date_of_joining": "2018-01-01",
		"address": {
			"address_line1": "1120 Cleo Rand Glen",
			"city": "Keizer",
			"state": "CT",
			"postal_code": "47329",
		},
		"phone": "(142) 627-2292",
		"roles": ["Driver"],
	},
	{
		"name": "Christian Dalton",
		"gender": "Male",
		"date_of_birth": "1970-08-09",
		"date_of_joining": "2018-01-01",
		"address": {
			"address_line1": "1350 Drumm Rapids",
			"city": "Coppell",
			"state": "VT",
			"postal_code": "00114",
		},
		"phone": "(926) 670-5011",
		"roles": ["Driver"],
	},
	{
		"name": "Lenore Robbins",
		"gender": "Female",
		"date_of_birth": "1996-05-10",
		"date_of_joining": "2023-06-19",
		"address": {
			"address_line1": "716 Crescent Hills",
			"city": "Chicopee",
			"state": "MA",
			"postal_code": "23292",
		},
		"phone": "(215) 326-9320",
		"roles": ["Driver"],
	},
	{
		"name": "Serena Rojas",
		"gender": "Female",
		"date_of_birth": "1995-02-08",
		"date_of_joining": "2018-07-15",
		"address": {
			"address_line1": "17 Quesada Station",
			"city": "Sidney",
			"state": "ME",
			"postal_code": "89989",
		},
		"phone": "(897) 608-1493",
		"roles": ["Driver"],
	},
	{
		"name": "Gordon Herman",
		"gender": "Male",
		"date_of_birth": "1992-12-19",
		"date_of_joining": "2020-06-20",
		"address": {
			"address_line1": "672 Bacon Mews",
			"city": "Fountain Hills",
			"state": "MA",
			"postal_code": "36604",
		},
		"phone": "(159) 204-1976",
	},
	{
		"name": "Arla Day",
		"gender": "Female",
		"date_of_birth": "1999-07-11",
		"date_of_joining": "2023-07-31",
		"address": {
			"address_line1": "987 Townsend Parkway",
			"city": "Bossier City",
			"state": "ME",
			"postal_code": "30671",
		},
		"phone": "(694) 362-4755",
	},
	{
		"name": "Waylon Hayden",
		"gender": "Male",
		"date_of_birth": "1989-03-26",
		"date_of_joining": "2021-09-18",
		"address": {
			"address_line1": "1227 Bradford Road",
			"city": "Rexburg",
			"state": "ME",
			"postal_code": "38962",
		},
		"phone": "(159) 387-3606",
	},
	{
		"name": "Vennie Morgan",
		"gender": "Female",
		"date_of_birth": "2000-10-22",
		"date_of_joining": "2023-09-27",
		"address": {
			"address_line1": "150 Massasoit Canyon",
			"city": "San Bruno",
			"state": "VT",
			"postal_code": "86290",
		},
		"phone": "(908) 090-5112",
	},
	{
		"name": "Charise Chavez",
		"gender": "Female",
		"date_of_birth": "1990-02-03",
		"date_of_joining": "2018-08-25",
		"address": {
			"address_line1": "1086 Pratt Hills",
			"city": "Hilton Head Island",
			"state": "RI",
			"postal_code": "34442",
		},
		"phone": "(987) 158-2480",
	},
	{
		"name": "Noriko Bernard",
		"gender": "Male",
		"date_of_birth": "1983-12-19",
		"date_of_joining": "2021-05-15",
		"address": {
			"address_line1": "46 Hugo Lane",
			"city": "Chino",
			"state": "NH",
			"postal_code": "25716",
		},
		"phone": "(436) 800-8302",
	},
	{
		"name": "Jenn Santos",
		"gender": "Female",
		"date_of_birth": "1994-10-11",
		"date_of_joining": "2021-03-19",
		"address": {
			"address_line1": "1280 Stratford Boulevard",
			"city": "Hanford",
			"state": "RI",
			"postal_code": "20577",
		},
		"phone": "(670) 845-0570",
	},
]


def setup_farm_price_list():
	if not frappe.db.exists("Price List", "Farm Supplies"):
		pl = frappe.new_doc("Price List")
		pl.price_list_name = "Farm Supplies"
		pl.buying = 1
		pl.append("countries", {"country": "United States"})
		pl.save()

	if not frappe.db.exists("Price List", "Farm Wholesale"):
		pl = frappe.new_doc("Price List")
		pl.price_list_name = "Farm Wholesale"
		pl.selling = 1
		pl.append("countries", {"country": "United States"})
		pl.save()


def create_employees(settings, employees):
	if frappe.db.exists("Employment Type", "Part-time"):
		frappe.rename_doc("Employment Type", "Part-time", "Part Time", force=True)
	if frappe.db.exists("Employment Type", "Full-time"):
		frappe.rename_doc("Employment Type", "Full-time", "Full Time", force=True)

	frappe.conf.throttle_user_limit = frappe.conf.user_type_doctype_limit[
		"employee_self_service"
	] = 1000
	company_domain = frappe.get_value("Company", settings.company, "domain")
	for employee_number, employee in enumerate(employees, start=10):
		employee = frappe._dict(employee)
		user = frappe.new_doc("User")
		user.first_name = employee.name.split(" ")[0]
		user.last_name = employee.name.split(" ")[1]
		user.user_type = "System User"
		user.username = f"{user.first_name[0].lower()}{user.last_name.lower()}"
		user.time_zone = "America/New_York"
		user.email = f"""{unicodedata.normalize('NFKD', user.first_name[0].lower())}{unicodedata.normalize('NFKD', user.last_name.replace("'", "").lower())}@{company_domain}"""
		user.user_type = "System User"
		user.append("roles", {"role": "Employee Self Service"})
		if "roles" in employee:
			for role in employee.get("roles"):
				user.append("roles", {"role": role})
		user.save()

		emp = frappe.new_doc("Employee")
		emp.first_name = user.first_name
		emp.last_name = user.last_name
		emp.employment_type = "Full Time"
		emp.company = settings.company
		emp.status = "Active"
		emp.gender = employee.gender
		emp.date_of_birth = employee.date_of_birth
		emp.date_of_joining = employee.date_of_joining
		emp.department = "Management" if (employee_number + 1) % 3 == 0 else "Operations"
		emp.designation = "Associate"
		emp.user_id = user.name
		emp.cell_number = employee.phone
		emp.create_user_permission = 0
		emp.save()

		addr = frappe.new_doc("Address")
		addr.address_title = employee.name
		addr.address_type = "Personal"
		addr.address_line1 = employee.address.get("address_line1")
		addr.city = employee.address.get("city")
		addr.state = employee.address.get("state")
		addr.country = "United States"
		addr.pincode = employee.address.get("postal_code")
		addr.phone = employee.phone
		addr.append("links", {"link_doctype": "Employee", "link_name": emp.name})
		addr.save()
		emp.employee_primary_address = addr.name
		emp.save()

		shift = frappe.new_doc("Shift Assignment")
		shift.employee = emp.name
		shift.company = settings.company
		shift.status = "Active"
		shift.start_date = emp.date_of_joining
		shift_type = settings.shift_map.get(emp.department)
		if len(shift_type) > 1:
			shift.shift_type = shift_type[0] if employee_number % 2 == 0 else shift_type[1]
		else:
			shift.shift_type = shift_type[0]
		shift.save()

		if "roles" in employee:
			if role == "Driver":
				create_driver(emp)


def create_vehicles():
	fixtures_directory = Path().cwd().parent / "apps" / "fleet" / "fleet" / "tests" / "fixtures"
	vehicles = json.loads((fixtures_directory / "vehicles.json").read_text(encoding="UTF-8"))
	drivers = frappe.get_all("Driver", pluck="name")
	driver_idx = 0
	for idx, vehicle in enumerate(vehicles):
		if frappe.db.exists("Vehicle", vehicle.get("name")):
			continue
		doc = frappe.new_doc("Vehicle")
		doc.update(vehicle)
		doc.start_date = getdate().replace(day=1)
		doc.end_date = doc.start_date.replace(month=(doc.start_date.month + 1) % 13)
		doc.insurance_company = "Cooperative Insurance Company"
		doc.append("drivers", {"driver": drivers[driver_idx]})
		doc.append("drivers", {"driver": drivers[driver_idx - 1]})
		if idx % 2:
			driver_idx += 1
			doc.append("drivers", {"driver": drivers[driver_idx]})
		doc.save()


def create_locations():
	# state parks or forests in New Hampshire
	# farm (Concord)
	pass


def create_vehicle_logs():
	pass


def create_driver(emp):
	driver = frappe.new_doc("Driver")
	driver.status = "Active"
	driver.full_name = emp.employee_name
	dl_expiry_year = getdate().year + (((getdate().year - emp.date_of_birth.year) - 16) % 5)
	driver.expiry_date = emp.date_of_birth.replace(year=dl_expiry_year)
	driver.issuing_date = driver.expiry_date.replace(year=driver.expiry_date.year - 5)
	driver.cell_number = emp.cell_number
	driver.employee = emp.name
	license_number = f"{emp.date_of_birth.month}{emp.last_name[0]}{emp.first_name[0]}{driver.issuing_date.year:02}{driver.issuing_date.day:02}"
	driver.license_number
	driver.append(
		"driving_license_category",
		{
			"license_number": license_number,
			"class": "C",
			"description": "Commercial",
			"issuing_date": driver.issuing_date,
			"expiry_date": driver.expiry_date,
		},
	)
	driver.address = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Employee", "link_name": emp.name, "parenttype": "Address"},
		"parent",
	)
	driver.save()


def create_suppliers(settings):
	fixtures_directory = Path().cwd().parent / "apps" / "fleet" / "fleet" / "tests" / "fixtures"
	suppliers = json.loads((fixtures_directory / "supplier.json").read_text(encoding="UTF-8"))
	for supplier in suppliers:
		if frappe.db.exists("Supplier", supplier.get("name")):
			continue
		if not frappe.db.exists("Supplier Group", supplier.get("supplier_group")):
			sg = frappe.new_doc("Supplier Group")
			sg.supplier_group_name = supplier.get("supplier_group")
			sg.parent_supplier_group = "All Supplier Groups"
			sg.save()
		doc = frappe.new_doc("Supplier")
		doc.update(supplier)
		doc.save()


def create_customers(settings):
	pass
	# captive customers
