<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Geofencing

Geofences are virtual boundaries around physical locations. When a vehicle crosses a configured geofence boundary, Fleet records the event. This enables use cases like tracking arrivals at customer sites, monitoring compliance with territorial restrictions, and triggering workflows based on location.

## Why Use Geofences

Consider a delivery company that wants to know when drivers arrive at customer locations. Without geofencing, someone would need to watch the map constantly or review Vehicle Logs manually.

With geofencing, Fleet automatically records when a vehicle enters or exits each customer site. A dispatcher can see at a glance which deliveries have arrived. Automated notifications can alert customers that their delivery is on-site. Reports can show how long vehicles spent at each location.

## Limitations

Traccar does not support circle shapes for geofences. Draw a polygon that approximates a circle if you need a circular boundary.

Only polygons, rectangles, and polylines work as geofence shapes. Points and other geometry types are not supported.

## Creating a Geofence

Geofences are created from Location documents in ERPNext.

1. Open or create a Location document
2. In the Location field, draw a shape on the map that covers the area you want to monitor. This can be a polygon for irregular boundaries, a rectangle for simple areas, or a polyline for route corridors
3. Check **Sync Traccar Geofence**
4. Save the document

Fleet creates the geofence in Traccar. The **Traccar Geofence ID** field populates automatically, confirming the sync succeeded.

## Linking Vehicles to Geofences

By default, a geofence monitors all vehicles. To limit monitoring to specific vehicles, use the **Geofenced Vehicle** field on the Location. Add the vehicles that should trigger events for this geofence.

Vehicles must have a valid Traccar ID before they can be linked. If you see validation errors, check that the vehicle has synced with Traccar first.

## Tracking Arrivals and Departures

Each Vehicle Log records geofence activity in three fields:

- **Geofence IDs**: The Traccar IDs of all geofences the vehicle is currently inside
- **Geofences Entered**: The names of any geofences the vehicle entered since the previous sync
- **Geofences Exited**: The names of any geofences the vehicle left since the previous sync

Fleet calculates these by comparing the current position's geofences with those from the previous Vehicle Log for that vehicle.

## Setting Up Notifications

Fleet captures geofence events but does not send notifications by default. To alert someone when a vehicle arrives at or leaves a location, create a Notification document.

1. Create a new Notification
2. Set the Document Type to Vehicle Log
3. Add a condition that checks the `geofences_entered` or `geofences_exited` field. For example, to trigger when any geofence is entered: `doc.geofences_entered`
4. Configure the recipients and notification channel
5. Enable the notification

Now when a vehicle enters a geofence, the notification fires.

## Updating and Removing Geofences

To change a geofence's shape, edit the map in the Location document and save. Fleet updates the geofence in Traccar automatically.

To add or remove vehicles from a geofence, edit the Geofenced Vehicle field. Changes take effect immediately.

To delete a geofence entirely, uncheck Sync Traccar Geofence and save. Fleet removes the geofence from Traccar and clears the Traccar Geofence ID.

