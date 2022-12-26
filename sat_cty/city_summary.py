from pystac_client import Client
from cirrus.lib.transfer import download_item_assets
import pystac
import os
from odc.stac import stac_load

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

items_local = []

for item in items:
    print(item.id)
    dl_dir = "/tmp/sat-cty/"
    bands = ["blue", "green", "red", "nir08"]
    os.makedirs(dl_dir, exist_ok=True)
    item = pystac.Item.from_dict((download_item_assets(item=item.to_dict(), path=dl_dir, assets=bands)))
    items_local.append(item)

local_ic = pystac.ItemCollection(items=items_local)

dc = stac_load(local_ic)

print(dc)
