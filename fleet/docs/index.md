<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Fleet

<div class="byline">
  Tyler Matteson 2025-12-30
</div>


Fleet brings real-time vehicle tracking into ERPNext. Instead of switching between a GPS tracking system and your ERP, fleet managers can monitor vehicles, track deliveries, and schedule maintenance from a single interface.

Fleet connects ERPNext to [Traccar](https://www.traccar.org/), an open-source GPS tracking platform. Vehicles equipped with GPS devices report their positions to Traccar, and Fleet syncs this data into ERPNext automatically. This creates a record of where vehicles have been, who was driving, and what condition the vehicle was in at each point.

1. [Vehicle Management](vehicle-management.md) — Set up your vehicles for tracking and connect them to Traccar
2. [Driver Assignment](driver-assignment.md) — Track which drivers operate which vehicles and when
3. [GPS Tracking](gps-tracking.md) — View your fleet on a map and monitor vehicle locations
4. [Telemetry](telemetry.md) — Monitor vehicle health through battery levels, engine data, and diagnostics
5. [Geofencing](geofencing.md) — Get notified when vehicles arrive at or leave specific locations
6. [Delivery Trip Optimization](delivery-trip-optimization.md) — Find the most efficient route for multiple delivery stops

## Requirements

Fleet requires Frappe Framework, ERPNext, and HRMS. A Traccar server instance (self-hosted or cloud) provides the GPS tracking backend.
