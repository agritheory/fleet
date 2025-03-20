# Copyright (c) 2024, AgriTheory and contributors
# For license information, please see license.txt

app_name = "fleet"
app_title = "Fleet"
app_publisher = "AgriTheory"
app_description = "Fleet Management Tools for ERPNext"
app_email = "support@agritheory.com"
app_license = "mit"
required_apps = ["erpnext", "hrms"]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "fleet",
# 		"logo": "/assets/fleet/logo.png",
# 		"title": "Fleet",
# 		"route": "/fleet",
# 		"has_permission": "fleet.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/fleet/css/fleet.css"
# app_include_js = "/assets/fleet/js/fleet.js"

# include js, css files in header of web template
# web_include_css = "/assets/fleet/css/fleet.css"
# web_include_js = "/assets/fleet/js/fleet.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "fleet/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
doctype_calendar_js = {
	"Vehicle": "public/js/fleet_calendar.js",
	"Driver": "public/js/fleet_calendar.js",
}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "fleet/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "fleet.utils.jinja_methods",
# 	"filters": "fleet.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "fleet.install.before_install"
after_install = "fleet.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "fleet.uninstall.before_uninstall"
# after_uninstall = "fleet.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "fleet.utils.before_app_install"
# after_app_install = "fleet.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "fleet.utils.before_app_uninstall"
# after_app_uninstall = "fleet.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "fleet.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Vehicle": "fleet.fleet.overrides.vehicle.FleetVehicle",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Vehicle": {
		"validate": [
			"fleet.fleet.overrides.vehicle.validate_poll_frequency_cron_format",
		],
		"before_save": [
			"fleet.fleet.overrides.vehicle.check_schedule_poll_frequency",
			"fleet.fleet.traccar.add_traccar_device",
		],
	},
	"Driver": {
		"before_save": [
			"fleet.fleet.traccar.add_traccar_driver",
		]
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
		"* * * * *": [
			"fleet.fleet.traccar.sync_vehicle",
		],
	}
}

# Testing
# -------

# before_tests = "fleet.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "fleet.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "fleet.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["fleet.utils.before_request"]
# after_request = ["fleet.utils.after_request"]

# Job Events
# ----------
# before_job = ["fleet.utils.before_job"]
# after_job = ["fleet.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"fleet.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
