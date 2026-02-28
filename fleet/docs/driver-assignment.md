<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Driver Assignment

Knowing who was driving a vehicle matters for compliance, accountability, and payroll. Fleet tracks driver assignments and records which driver was operating each vehicle at any given time.

## Assigning Drivers to Vehicles

Open a Vehicle and find the **Drivers** field. This multi-select field links to Driver documents. Add the drivers who are authorized to operate this vehicle.

When Fleet creates a Vehicle Log, it records the driver. If the GPS device reports a driver ID (some devices have RFID readers or keypads for driver identification), Fleet uses that. Otherwise, it falls back to the most recently recorded driver for that vehicle, then to the last driver in the Drivers list.

This creates an audit trail. A user reviewing Vehicle Logs can see not just where a vehicle went, but who was behind the wheel.

## Syncing Drivers to Traccar

Some GPS setups identify drivers through RFID cards or PIN entry. For this to work, Traccar needs to know about your drivers.

When a user saves a Driver document, Fleet creates a corresponding driver record in Traccar. The Driver's name becomes the unique identifier that Traccar uses to match driver events from GPS devices.

The **Traccar User ID** field on the Driver populates automatically after the sync completes.

## Connecting Driver Time to Locations

Fleet's geofencing feature records when vehicles enter and exit specific locations. Combined with driver tracking, this data can support timesheet workflows.

For example, a company might create geofences around customer job sites. When a driver enters a site, that event appears in the Vehicle Log. Using Frappe's Notification system, a workflow could create Timesheet entries based on these arrivals and departures.

To support this, Location documents have a **Default Activity Type** field. This links to an Activity Type that describes the work typically performed at that location. A notification or script can reference this when creating Timesheet Detail entries.

Setting up automated timesheets requires custom configuration beyond what Fleet provides out of the box, but Fleet captures the underlying data that makes it possible.
