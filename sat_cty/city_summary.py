from pystac_client import Client

landsat_sr_endpoint = "https://landsatlook.usgs.gov/stac-server"

cat = Client.open(landsat_sr_endpoint)

geom = {
    "type": "Polygon",
        "coordinates": [
          [
            [
              -80.04469820810723,
              39.67742545310713
            ],
            [
              -80.04469820810723,
              39.5691199181569
            ],
            [
              -79.8936372965484,
              39.5691199181569
            ],
            [
              -79.8936372965484,
              39.67742545310713
            ],
            [
              -80.04469820810723,
              39.67742545310713
            ]
          ]
        ],
}

search_kwargs = {
    "max_items": 15,
    "collections": ["landsat-c2l2-sr"],
    "datetime": "2020-01-01/2020-01-16",
    "intersects": geom
}

search = cat.search(**search_kwargs)

items = search.get_all_items()

for item in items:
    print(item.id)
