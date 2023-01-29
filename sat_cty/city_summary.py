from pystac_client import Client
import pystac
import os
from odc.stac import stac_load
from pyproj import CRS
import logging
import sys
from xarray import Dataset
import rioxarray
from pyproj import Proj
import requests


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


def s3_to_local(item: pystac.Item, dl_folder: str) -> pystac.Item:
    """Take in pystac item, download its assets, and update the asset href to point
    to dl location.
    Args:
        item (pystac.Item)
        dl_folder (str)

    Returns:
        
    """

    for v in item["assets"].values():
        fn = os.path.basename(v["href"])
        f_path = os.path.join(dl_folder, fn)
        if not os.path.exists(f_path):
            with requests.get(v["href"], stream=True) as r:
                r.raise_for_status()
                with open(f_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)
            
        v["href"] = f_path

    return item


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

        os.makedirs(dl_dir, exist_ok=True)

        # check if the assets are already downloaded, skip if so
        if os.path.basename(item.assets[bands[-1]].href) not in os.listdir(dl_dir):
            item = pystac.Item.from_dict((s3_to_local(item=item.to_dict(), dl_folder=dl_dir)))

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
            resolution=resolution,
            groupby="solar_day",
            crs=output_crs,
            bbox=bbox
            )

    return dc


def calc_ndvi(dc: Dataset, red_band_name: str, nir_band_name: str) -> Dataset:
    """Calculate NDVI for a datacube.
    Args:
        dc (Dataset): datacube with at least red and nir bands
        red_band_name (str): name of red band variable
        nir_band_name (str): name of near infrared band variable
    Returns:
        dc (Dataset): datacube with NDVI variable
    """

    dc["NDVI"] = (dc[nir_band_name] - dc[red_band_name])/(dc[nir_band_name] + dc[red_band_name])

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
    query_point = (-80.0,39.6)

    items = run_query(date_range="2020-01-01/2020-01-16", geometry=geom, collections=collections, endpoint=earthsearch_stac_endpoint)
    items = download_items_to_local(items, bands, wkdir)

    dc = make_datacube(items=items, bands=bands, resolution=10)
    dc = calc_ndvi(dc, red_band_name="B04", nir_band_name="B08")

    # convert query lon/lat to UTM meters
    p = Proj(CRS.from_epsg(items[0].properties["proj:epsg"]), preserve_units=False)
    x, y = p(query_point[0], query_point[1])

    # get the row/col from the lon/lat based on the bounds and the resolution
    # TODO review the below with additional (but not too much) caffeine
    bounds = dc.NDVI.rio.bounds()
    x_res = dc.NDVI.rio.resolution()[0]
    y_res = dc.NDVI.rio.resolution()[1]

    x_offset_m = x - bounds[0]
    y_offset_m = y - bounds[3]

    x_offset_cols = int(round(x_offset_m / x_res, 0))
    y_offset_cols = int(round(y_offset_m / y_res, 0))

    sample_coord_array_1d = dc.NDVI.isel(x=x_offset_cols, y=y_offset_cols)

    print(sample_coord_array_1d)
