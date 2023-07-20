"""utility funcs"""

import requests
from pystac import Item, ItemCollection
import os.path as op
from os import makedirs
import logging


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


def s3_to_local(item: dict, dl_folder: str, bands: list) -> dict:
    """Take in pystac item, download its assets, and update the asset href to point
    to dl location.
    Args:
        item (pystac.Item): the item to download the assets for
        dl_folder (str): the path to put the files

    Returns:
        item (pystac.Item): the item with downloaded assets and updated asset hrefs
        
    """

    for v in item["assets"].values():
        if k in bands:
            fn = op.basename(v["href"])
            f_path = op.join(dl_folder, fn)
            if not op.exists(f_path):
                with requests.get(v["href"], timeout=60, stream=True) as r:
                    r.raise_for_status()
                    with open(f_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            v["href"] = f_path
            print("Garbage")

    return item


def download_items_to_local(item_col: ItemCollection, bands: list, wkdir: str) -> ItemCollection:
    """Download items locally, using appropriate download method.
    Args:
        item_col (pystac.ItemCollection): item collection with remote asset hrefs to download
        wkdir (str): local working dir to use, make if not exist
    Returns:
        local_ic (pystac.ItemCollection): item collection with local asset hrefs
    """

    makedirs(wkdir, exist_ok=True)

    items_local = []

    for item in item_col:
        logging.info("Downloading assets for item: %s", item.id)
        dl_dir = op.join(wkdir, item.id)
        makedirs(dl_dir, exist_ok=True)
        item = Item.from_dict((s3_to_local(item=item.to_dict(), dl_folder=dl_dir, bands=bands)))
        items_local.append(item)

    local_ic = ItemCollection(items=items_local)

    return local_ic
