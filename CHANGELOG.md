<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Changelog

## [v15.1.1] - 2025-10-08

### Release Notes

## v15.1.1 (2025-10-08)

### Bug Fixes

- Sync traccar geofence error when no location data ([`6e1c493`](https://github.com/agritheory/fleet/commit/6e1c4939518fe5c3307c4c6cb243010eadf8944f))

### Chores

- Move workspace templates ([`bc30271`](https://github.com/agritheory/fleet/commit/bc30271cb5f650622b8ba4c66ff91f9f54b91f5e))

- Update installation instructions with troubleshooting info ([`4225cb1`](https://github.com/agritheory/fleet/commit/4225cb120f957b2bf506b15ca39d0832eb9e82f6))

---

**Detailed Changes**: [v15.1.0...v15.1.1](https://github.com/agritheory/fleet/compare/v15.1.0...v15.1.1)


### Changes from Pull Requests

Fixed an issue where adding a Location caused an error when Traccar syncing wasn't enabled. Now, the system only attempts to load location data when syncing is enabled, preventing errors and improving the user experience.
  _Source: PR #19_

Updated installation instructions with troubleshooting information to help you get started more easily. If you encounter any issues during the setup process, our new guide includes helpful tips and solutions to resolve common problems. This should simplify and streamline installation.
  _Source: PR #15_

**Route Optimization Update**

Added a route optimization feature to the application for Delivery Trips. Given a number of stops defined in a Delivery Trip, this feature uses Pyvroom to find the optimal route.

  _Source: PR #13_

## [v15.1.0] - 2025-05-27

### Release Notes

## v15.1.0 (2025-05-27)

---

**Detailed Changes**: [v15.0.0...v15.1.0](https://github.com/agritheory/fleet/compare/v15.0.0...v15.1.0)


### Changes from Pull Requests

This update adds style tabs to custom HTML blocks in the Frappe form to match the tab styling of the Fleet workspace. This ensures a more consistent and visually appealing interface for users.

**What's New:**
- Style tabs in custom HTML blocks to align with Fleet workspace tab design.
- Added new icons and updated CSS files to support the changes.

**How It Helps You:**
- The updated tab styling makes it easier to navigate through different sections of your forms, improving usability.
- Consistent styling across different parts of the application enhances a cohesive user experience.

**What's Changed:**
- Modified `fleet/fleet/workspace/fleet/fleet.json` and `fleet/hooks.py`.
- Added new CSS file `fleet/fleet_home.css` and HTML file `fleet/fleet_home.html`.
- Updated `fleet/install.py` to include new icon files.
- Removed unused icons.

**Additional Notes:**
- Added a new Fleet icon

  _Source: PR #12_

**Added Geofence Features**

We're excited to announce the addition of geofence features in our system! With these new capabilities, you can now:

1. **Draw Polygons, Rectangles, and Polylines**: Easily create geofences on a map by drawing polygons, rectangles, or polylines. This allows you to define the geofence in an ERPNext Location, which then syncs with Traccar. (Note that Traccar no longer support the circle shape to define a geofence.)

2. **Link Geofences to Devices**: Assign devices to geofences so that when they enter or leave these areas, alerts can be triggered based on your predefined rules.

3. **Manage Multiple Vehicles per Geofence**: Link multiple vehicles to a single geofence for comprehensive tracking and management.

4. **Alarm Functionality Based on Vehicle Logs**: Receive alerts when vehicles enter or exit geofences, helping you stay informed about their movements in real-time.

5. **Customize Address Doctype**: Enhances the Address doctype by allowing a dynamic link to a Location doctype, to sync a physical address with its corresponding latitude and longitude.

6. **Sync Geofences with Traccar**: Automatically sync geofences between ERPNext and Traccar, ensuring that all relevant data is up-to-date and consistent across both systems.

  _Source: PR #10_

**Asset and Vehicle Integration Update**

We're excited to announce that our system now includes a new feature for integrating assets and vehicles! This update allows you to create an "Asset Category" called "Vehicle" and utilize ERPNext's built-in asset repair functionality if a tracked vehicle triggers a Traccar diagnostic alert.

If a diagnostic is found during the creation of a vehicle log, our system will automatically create a draft asset repair document for your review. This allows you to update the cost and repairs done on the asset or delete the document if it's not needed. This feature ensures that you always have up-to-date information about your vehicles and their maintenance.

  _Source: PR #7_

**Traccar Integration Update**

We're excited to announce that our fleet management system now includes a Traccar integration! This update allows us to seamlessly connect with the Traccar GPS tracking platform, providing enhanced vehicle and location management capabilities.

With this new feature:
- **Vehicle IMEI Management**: We've added a way to create and manage Vehicle IMEI codes directly within our system.
- **Automatic Device Creation**: If a device (vehicle) does not exist in Traccar, it will be automatically created using the provided IMEI code.
- **Initial GPS Logs**: We've set up initial vehicle logs with GPS coordinates as test data to ensure everything is working smoothly.
- **Custom Cron Configuration**: You can now configure custom cron jobs for vehicles, and these configurations are saved persistently in our system.
- **Data Push to Traccar**: When a new vehicle or configuration is created, the relevant data will be pushed to Traccar. We've also saved the Traccar device ID on the vehicle to facilitate position requests.

This update enhances your fleet management by providing better integration with external GPS tracking systems, making it easier for you to monitor and manage your vehicles effectively.
  _Source: PR #4_

## [v15.0.0] - 2024-11-27

### Release Notes

## v15.0.0
