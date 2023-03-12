from pystac_client import Client
from pystac import ItemCollection
from odc.stac import stac_load
from pyproj import CRS
import logging
import sys
from xarray import Dataset
from pyproj import Proj

# need to import rioxarray in order to get 'rio' accessor in datacubes
import rioxarray

from utils import bbox_to_geom, download_items_to_local


def run_query(endpoint, collections, date_range, geometry) -> ItemCollection:
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


def make_datacube(items: ItemCollection, bands, resolution) -> Dataset:
    """Convert stac item collection into xarray Dataset object. 
    Temporal compositing hard-coded to solar_day for now.
    Arg:
        items (pystac.ItemCollection): items to convert to datacube
    Return:
        dc (Dataset): space-time datacube    
    """

    logging.info("Making datacube for items: %s", items.items)

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

    logging.info("Calculating NDVI for %s", dc)

    dc["NDVI"] = (dc[nir_band_name] - dc[red_band_name])/(dc[nir_band_name] + dc[red_band_name])

    return dc


if __name__ == "__main__":

    # set up logging
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    wkdir = sys.argv[1] if len(sys.argv) > 1 else "/data/sat-cty"
    
    # currently only the sentinel-2 data are downloadable from this script b/c missing auth for landsat
    # landsat_sr_endpoint = "https://landsatlook.usgs.gov/stac-server" 

    earthsearch_stac_endpoint = "https://earth-search.aws.element84.com/v0"
    landsatlook_stac_endpoint = "https://landsatlook.usgs.gov/stac-server/"

    collections = ["sentinel-s2-l2a-cogs"]
    collections_landsat = ["landsat-c2l2-st"]

    bands = ["B02", "B03", "B04", "B08"]
    landsat_st_bands = ["lwir11", "qa_pixel"]

    bbox = [-80.04469820810723, 39.5691199181569, -79.8936372965484, 39.67742545310713]
    geom = bbox_to_geom(bbox)
    query_point = (-80.0,39.6)

    items = run_query(date_range="2020-01-01/2020-03-01", geometry=geom, collections=collections_landsat, endpoint=landsatlook_stac_endpoint)
    items = download_items_to_local(items, bands, wkdir)

    dc = make_datacube(items=items, bands=bands, resolution=10)
    dc = calc_ndvi(dc, red_band_name="B04", nir_band_name="B08")

    # convert query lon/lat to UTM meters
    p = Proj(CRS.from_epsg(items[0].properties["proj:epsg"]), preserve_units=False)

    # pylint: disable=unpacking-non-sequence
    x, y = p(query_point[0], query_point[1])
    # pylint: enable=unpacking-non-sequence

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
