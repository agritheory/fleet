<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Telemetry

Modern GPS devices report more than just location. They can capture battery voltage, engine RPM, speed, temperature, fuel levels, and diagnostic codes. Fleet stores this data in Vehicle Logs, making it available for monitoring and analysis.

## What Fleet Captures

Each Vehicle Log can include:

- **Coordinates**: Longitude and latitude from the GPS fix
- **Speed**: The vehicle's speed at the time of the reading
- **Battery Level**: External battery voltage, useful for detecting charging issues
- **Engine Hours**: Total runtime, helpful for scheduling maintenance by operating hours rather than mileage
- **RPM**: Engine revolutions per minute
- **Engine Temperature**: Helps identify overheating before it causes damage
- **Fuel Quantity**: Fuel level if the device supports fuel sensors
- **Odometer**: Calculated from the device's total distance reading
- **Diagnostic Codes**: OBD-II trouble codes that indicate mechanical issues

Not every device reports all of these. The data available depends on the GPS hardware and how it connects to the vehicle.

## Monitoring Battery Health

The Fleet workspace includes a battery voltage report that lists all active vehicles sorted by battery level, lowest first. This makes it easy to spot vehicles with failing batteries before they leave drivers stranded.

For automated alerts, configure the Traccar Integration settings:

1. Set **External Battery Low Threshold** to a voltage level that indicates a problem
2. Link a Notification document in **Battery Level Notification**

When a vehicle's battery drops below the threshold, the notification triggers.

## Scheduling Syncs for Critical Vehicles

By default, Fleet syncs every vehicle once per minute. For vehicles on time-sensitive routes or carrying valuable cargo, more frequent updates might be necessary. For vehicles parked overnight, less frequent syncs reduce unnecessary load.

Set a custom schedule in the **Poll Frequency** field on the Vehicle. This field accepts standard cron expressions:

| Schedule | Expression |
| :-------- | :---------- |
| Every 2 minutes | `*/2 * * * *` |
| Every 5 minutes | `*/5 * * * *` |
| Every 15 minutes | `*/15 * * * *` |
| Every hour | `0 * * * *` |
| Weekdays 6 AM to 6 PM, every 10 minutes | `*/10 6-18 * * 1-5` |

Leave the field empty to use the default one-minute schedule.

## Handling Diagnostic Trouble Codes

When a GPS device reports a diagnostic code, it often indicates a mechanical issue that needs attention. Fleet can route these alerts to your maintenance team automatically.

If the vehicle is also set up as an Asset in ERPNext, Fleet creates a draft Asset Repair when a diagnostic code appears. The repair document includes the diagnostic text, making it easy for maintenance staff to see what the vehicle reported.

This only works when an Asset exists with the same name as the Vehicle. The Asset Repair remains in draft status, waiting for someone to review and decide on next steps.

## Converting Distance Units

Traccar typically reports distances in meters. If your organization tracks mileage in miles or kilometers, configure the conversion in Traccar Integration:

1. Set **Traccar Distance UoM** to the unit Traccar uses (usually Meter)
2. Set **ERPNext Distance UoM** to your preferred unit
3. Select a **Distance Conversion Factor** that converts between them

Fleet applies this conversion when calculating odometer values in Vehicle Logs.
