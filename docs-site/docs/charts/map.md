import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Map

One filled region per row, or one point per row at a latitude and longitude.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="map" title="Map" example="examples/sales_dashboard/visualisations/revenue_by_country.ggsql" summary="Regions filled by a value, or places as points. Shows where, not just how much.">

```sql
SELECT country, revenue
FROM {{ source('raw', 'country_sales') }}
ORDER BY country

VISUALISE country AS region, revenue AS color
DRAW map
LABEL title => 'Revenue by Country'
INTERACT tooltip
```

</ChartTypeCard>

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `map` | `region` or `latitude` and `longitude`, optional `size` and `color` | `tooltip` only | glyf |

## How it reads

A map draws one of two things, and the roles say which.

**Regions.** `region` names the shape a row fills; `color` shades it. A
number gets a continuous scale, text gets one colour per value.

```sql
SELECT country, revenue
FROM {{ source('raw', 'country_sales') }}
ORDER BY country

VISUALISE country AS region, revenue AS color
DRAW map
LABEL title => 'Revenue by Country'
INTERACT tooltip
```

**Points.** `latitude` and `longitude` place a circle per row; `size` and
`color` are optional.

```sql
SELECT city, latitude, longitude, revenue, format
FROM {{ source('raw', 'stores') }}
ORDER BY revenue DESC

VISUALISE latitude AS latitude, longitude AS longitude, revenue AS size, format AS color
DRAW map
LABEL title => 'Stores by Revenue'
INTERACT tooltip
```

A map takes `region` or the two coordinates, never both, and `size` only for
points. Both kinds are drawn over the land, so the regions and points the
query returns keep their place in the world.

The world's countries ship with glyf, so a map needs no setup and builds
offline. A region matches its country by ISO 3166 code, alpha-3 (`USA`) or
alpha-2 (`US`), or by English name (`United States`). glyf reads the column
and uses whichever of the three it matches best, so codes and names are never
mixed up. The shapes are drawn at 1:110 million, which leaves out the
smallest countries, such as Singapore. A region with no shape is left off the
map, and the build says which:

```text
! visualisations/revenue_by_country.ggsql: 1 region(s) have no shape and are left off the map: SGP
```

For states, sales territories or anything else, name a TopoJSON file in the
project:

```sql
CONFIG shapes => 'geo/us-states.topojson'
CONFIG projection => 'albersUsa'
```

The path is relative to the project and must stay inside it. glyf draws the
file's first object, and matches each row against the shape's `id` and each
of its properties, again taking the best match. `projection` is one of
`equalEarth` (the default), `naturalEarth1`, `mercator`, `equirectangular`,
`albersUsa` or `orthographic`.

A map takes `INTERACT tooltip`, which lists the columns it binds.
`legend_filter` and `zoom` fail validation. Dashboard filters narrow the
regions or points and leave the land whole. The visual diff compares a map
pixel by pixel, the way it does a scatter.

Points at exact coordinates can identify a person or a home. Aggregate them
in SQL, or round the coordinates, before they reach a published map; see
[data exposure](../guides/data-exposure.md).

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
