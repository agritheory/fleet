<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Delivery Trip Optimization

When a vehicle has multiple stops, the order matters. Visiting locations in a poorly chosen sequence wastes fuel and time. Fleet can analyze a Delivery Trip's stops and suggest an efficient route.

## How Route Optimization Works

Fleet uses the Valhalla routing engine, which calculates travel times using real road networks. Given a list of delivery stops, it solves the Traveling Salesperson Problem to find an order that minimizes total travel.

This is not a simple "nearest neighbor" approach. Valhalla considers actual driving distances, turn restrictions, and road types to produce routes that work in practice.

## Optimizing a Delivery Trip

Route optimization is available through the `optimize_path` function. Pass a Delivery Trip document or name, and it returns the stops in optimized order.

```python
from fleet.fleet.overrides.delivery_trip import optimize_path

optimized_stops = optimize_path("DT-00001")
```

The function returns a list of delivery stops sorted by the recommended visit order. A developer can use this to update the Delivery Trip's stop sequence or display the optimized route to a dispatcher.

## What the Optimizer Considers

The current implementation optimizes for a single vehicle visiting all stops in one trip. It assumes:

- The vehicle starts at the first delivery stop
- All stops must be visited
- The vehicle does not need to return to a depot

This fits simple delivery scenarios. For more complex routing with time windows, multiple vehicles, or capacity constraints, additional development would be needed.

## Geocoding Addresses

Route optimization requires coordinates for each stop. If delivery stops have latitude and longitude populated, those coordinates are used directly.

For addresses without coordinates, Fleet includes a geocoding function that looks up locations using OpenStreetMap's Nominatim service:

```python
from fleet.fleet.overrides.delivery_trip import get_geocode_from_address

lat, lon = get_geocode_from_address("123 Main St, Springfield, IL")
```

For production use with high volumes, consider populating coordinates on Address documents ahead of time or using a commercial geocoding service with higher rate limits.

## Monitoring Active Deliveries

The Fleet workspace shows an ETA table for Delivery Trips with status Scheduled or In Transit. This displays:

- The assigned driver
- The assigned vehicle
- The next customer
- The estimated arrival time

Dispatchers can monitor this table to track delivery progress without opening individual Delivery Trip documents.

## Technical Details

Fleet connects to the public Valhalla instance hosted by OpenStreetMap at `valhalla1.openstreetmap.de`. The pyvroom library handles communication with this service.

The optimizer uses the "auto" vehicle profile, which assumes a standard automobile. It runs with exploration level 5 and 4 threads to balance solution quality against response time.

For self-hosted deployments or different vehicle types (trucks, motorcycles), the routing configuration in `delivery_trip.py` would need modification.
