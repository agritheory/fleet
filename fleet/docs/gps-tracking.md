<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# GPS Tracking

Fleet provides a central view of where all vehicles are and where they have been. This helps dispatchers coordinate deliveries, managers verify field operations, and maintenance staff locate vehicles that need service.

## Viewing Your Fleet on a Map

The Fleet workspace shows an interactive map with markers for each tracked vehicle. The map adjusts its view to fit all vehicles, so a user sees the entire fleet at once.

Each marker links to the Vehicle document and displays the most recent driver. Clicking a marker opens details about that vehicle.

Below the map, a battery voltage table lists all active vehicles sorted by battery level, lowest first. This highlights vehicles that may need attention before their batteries fail.

For companies with active deliveries, an ETA table shows Delivery Trips that are scheduled or in transit, with driver, vehicle, customer, and estimated arrival information.

## Understanding Position History

Every time Fleet syncs a vehicle, it creates a Vehicle Log document. These logs accumulate into a complete movement history.

To review where a vehicle has been, open the Vehicle Log list and filter by the vehicle's license plate. Each log shows the date, time, coordinates, driver, and any telemetry data the device reported.

This history supports several use cases:

- Verifying a driver visited a customer site on a specific date
- Investigating incidents by reviewing the vehicle's location at a given time
- Analyzing route patterns to identify inefficiencies
- Auditing compliance with territorial restrictions

## How Syncing Works

Fleet runs a scheduled task every minute. This task checks each tracked vehicle and decides whether to sync based on its configuration.

Vehicles without a custom poll frequency sync immediately during each run. Vehicles with a custom poll frequency (set as a cron expression) only sync when their schedule dictates.

When syncing a vehicle, Fleet calls the Traccar API to retrieve the most recent position. It extracts coordinates, speed, and any telemetry attributes the device reported. Then it creates and submits a Vehicle Log with all this data.

If the vehicle's position places it inside or outside geofences compared to the previous sync, Fleet records which geofences the vehicle entered or exited.

## Background Processing

Syncing many vehicles takes time. Fleet uses a dedicated background queue named `traccar` to handle sync jobs without blocking other operations.

If your site processes a large fleet, ensure your worker configuration includes the `traccar` queue. This keeps sync operations running smoothly and prevents them from competing with other background tasks.
