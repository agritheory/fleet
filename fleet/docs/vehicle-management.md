<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Vehicle Management

Before Fleet can track a vehicle, the vehicle needs a GPS device and a connection between ERPNext and Traccar. This guide walks through setting up that connection.

## Connecting to Traccar

Fleet needs to know where your Traccar server is and how to authenticate. A system manager configures this once in Traccar Integration.

Navigate to Traccar Integration and enter:

- **Traccar Server URL**: The full address of your Traccar instance, for example `https://traccar.example.com`
- **Username** and **Password**: Credentials for a Traccar account with permission to manage devices
- **Enable Traccar**: Check this box to activate the integration

If your GPS devices report distances in meters but you track odometer readings in miles, set the Traccar Distance UoM and ERPNext Distance UoM fields. Then select the appropriate UOM Conversion Factor to convert between them.

## Setting Up a Vehicle for Tracking

Each vehicle needs a unique identifier that matches its GPS device. Open the Vehicle record and go to the Telemetry tab.

Enter the **Traccar IMEI** field with the device's unique identifier. This is typically the IMEI number printed on the GPS device or shown in Traccar's device list.

When you save the Vehicle, Fleet checks Traccar for a device with that identifier. If one exists, Fleet links to it. If not, Fleet creates a new device in Traccar automatically.

After saving, the **Traccar ID** field populates with Traccar's internal device ID. This confirms the connection is working.

## How Position Data Flows into ERPNext

Fleet runs a background task every minute that checks each tracked vehicle's position in Traccar. When it finds new position data, it creates a Vehicle Log document with the coordinates, timestamp, and any telemetry the device reported.

This means every position update becomes a permanent record in ERPNext. A user can review a vehicle's history by looking at its Vehicle Log entries, filter by date ranges, or build reports on movement patterns.

## Controlling How Often a Vehicle Syncs

By default, all vehicles sync every minute. Some situations call for different frequencies. A vehicle making time-sensitive deliveries might need updates every few minutes, while a vehicle parked at a depot overnight might only need hourly checks.

The **Poll Frequency** field accepts a cron expression that controls when Fleet syncs that specific vehicle. For example:

- `*/5 * * * *` syncs every 5 minutes
- `*/15 * * * *` syncs every 15 minutes
- `0 6-18 * * 1-5` syncs hourly between 6 AM and 6 PM on weekdays

Leave this field empty to use the default every-minute schedule.

## When Something Goes Wrong with a Vehicle

GPS devices can report diagnostic trouble codes from the vehicle's onboard computer. When a Vehicle Log contains diagnostic data, Fleet looks for an Asset with the same name as the Vehicle. If found, it creates a draft Asset Repair document describing the issue.

This brings potential maintenance issues to the attention of staff who manage Assets, without requiring them to monitor GPS data directly. The draft repair waits for someone to review it, add details, and decide whether to proceed with maintenance.

## Registration and Administrative Fields

Fleet adds fields for tracking vehicle registration and compliance. These do not affect GPS tracking but help manage the administrative side of a fleet.

The Registration section includes Title Number, Registration State, and Registration Expiration Date. A user can also record Toll Tag Number and Toll Tag State for vehicles with electronic toll collection.

The Disabled checkbox stops Fleet from syncing a vehicle. Use this for vehicles that are out of service or sold.
