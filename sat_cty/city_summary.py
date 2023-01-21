from pystac_client import Client
from cirrus.lib.transfer import download_item_assets
import pystac
import os
from odc.stac import stac_load
from pyproj import CRS
import logging
import sys
from xarray import Dataset


def bbox_to_geom(bbox: list) -> dict:
    """Convert a bounding box to a geojson-formatted
    geometry.
    Arg:
        bbox (list): bouning box with coordinate order left, bottom, right, top
    Return:
        geometry (dict): geojson-formatted geometry, as a dict  
    """
    geometry = {
      "type": "Polygon",
          "coordinates": [
            [
              [
                bbox[0],
                bbox[3]
              ],
              [
                bbox[0],
                bbox[1]
              ],
              [
                bbox[2],
                bbox[1]
              ],
              [
                bbox[2],
                bbox[3]
              ],
              [
                bbox[0],
                bbox[3]
              ]
            ]
          ],
  }

    return geometry

def run_query(endpoint, collections, date_range, geometry) -> pystac.ItemCollection:
    """Use provided params to run pystac search.
    Args:
        endpoint (str): STAC search endpoint url
        collections (list): item collection names to search
        date_range (str): string formatted date range, e.g. "2020-01-01/2020-01-16"
        geometry (dict): geojson-formatted polygon geometry to search with
    Returns:
        items (pystac.ItemCollection)
    """
    search_kwargs = {
        "max_items": 15,
        "collections": collections,
        "datetime": date_range,
        "intersects": geometry
    }

    cat = Client.open(endpoint)
    search = cat.search(**search_kwargs)
    items = search.get_all_items()

    return items


def download_items_to_local(item_col: pystac.ItemCollection, bands: list, wkdir: str) -> pystac.ItemCollection:
    """Download items locally, using appropriate download method.
    Args:
        item_col (pystac.ItemCollection): item collection with remote asset hrefs to download
        wkdir (str): local working dir to use, make if not exist
    Returns:
        local_ic (pystac.ItemCollection): item collection with local asset hrefs
    """

    os.makedirs(wkdir, exist_ok=True)

    items_local = []

    for item in item_col:
        logging.info("Downloading assets for item: %s", item.id)

        dl_dir = os.path.join(wkdir, item.id)

        # check if the assets are already downloaded, skip if so
        if os.path.basename(item.assets[bands[-1]].href) not in dl_dir:
            item = pystac.Item.from_dict((download_item_assets(item=item.to_dict(), path=dl_dir, assets=bands)))

        items_local.append(item)

    local_ic = pystac.ItemCollection(items=items_local)

    return local_ic

def make_datacube(items: pystac.ItemCollection, bands, resolution) -> Dataset:
    """Convert stac item collection into xarray Dataset object. 
    Temporal compositing hard-coded to solar_day for now.
    Arg:
        items (pystac.ItemCollection): items to convert to datacube
    Return:
        dc (Dataset): space-time datacube    
    """
    output_crs = CRS.from_epsg(items[0].properties["proj:epsg"])

    dc = stac_load(
            items=items.items, 
            bands=bands,
            resolution=10.0,
            groupby="solar_day",
            crs=output_crs,
            bbox=bbox
            )

    return dc


if __name__ == "__main__":

    # set up logging
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    wkdir = "/tmp/sat-cty"
    
    # currently only the sentinel-2 data are downloadable from this script b/c missing auth for landsat
    # landsat_sr_endpoint = "https://landsatlook.usgs.gov/stac-server" 

    earthsearch_stac_endpoint = "https://earth-search.aws.element84.com/v0"
    collections = ["sentinel-s2-l2a-cogs"]

    bands = ["B02", "B03", "B04", "B08"]

    bbox = [-80.04469820810723, 39.5691199181569, -79.8936372965484, 39.67742545310713]
    geom = bbox_to_geom(bbox)

    items = run_query(date_range="2020-01-01/2020-01-16", geometry=geom, collections=collections, endpoint=earthsearch_stac_endpoint)
    items = download_items_to_local(items, bands, wkdir)

    dc = make_datacube(items=items, bands=bands, resolution=10)
