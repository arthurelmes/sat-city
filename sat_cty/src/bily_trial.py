from pystac_client import Client
from pystac import ItemCollection
import geopandas as gpd

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

# I think I know how to collect these together
my_itemcollection = ItemCollection(items=list(search.items()))
my_itemcollection.save_object('my_itemcollection.json')

# I also think I may know how to create a geojson from this
stac_json = search.get_all_items_as_dict()
gdf = gpd.GeoDataFrame.from_features(stac_json, "epsg:32617")

print('\n', gdf.columns)

# I forget the rest of what is going on here, not even sure what I have