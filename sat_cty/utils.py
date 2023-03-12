"""utility funcs"""

import requests
from pystac import Item, ItemCollection
import os.path as op
from os import makedirs
import logging
import boto3
from urllib.parse import urlparse

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


def download_using_boto3(item: dict, dl_folder: str) -> dict:
    """Take in pystac item, download its assets using boto3, 
    and update the asset href to point to dl location.
    Args:
        item (pystac.Item): the item to download the assets for
        dl_folder (str): the path to put the files

    Returns:
        item (pystac.Item): the item with downloaded assets and updated asset hrefs
        
    """

    s3 = boto3.client('s3')
    for v in item["assets"].values():
        dl_url = v["alternate"]["s3"]["href"] if v.get("alternate", None) else v["href"]
        if ".TIF" not in dl_url: # TODO check the actual bands of interest here, to avoid dling extra stuff
            continue
        fn = op.basename(dl_url)
        f_path = op.join(dl_folder, fn)
        if not op.exists(f_path):
            parsed_url = urlparse(dl_url)
            bucket = parsed_url.hostname
            prefix = parsed_url.path[1:]
            with open(f_path, 'wb') as f:
                resp = s3.get_object(Bucket=bucket, Key=prefix, RequestPayer="requester")
                response_content = resp['Body'].read()
                f.write(response_content)

        v["href"] = f_path

    return item


def download_using_requests(item: dict, dl_folder: str) -> dict:
    """Take in pystac item, download its assets using vanilla requests module, 
    and update the asset href to point to dl location.
    Args:
        item (pystac.Item): the item to download the assets for
        dl_folder (str): the path to put the files

    Returns:
        item (pystac.Item): the item with downloaded assets and updated asset hrefs
        
    """

    for v in item["assets"].values():
        fn = op.basename(v["href"])
        f_path = op.join(dl_folder, fn)
        if not op.exists(f_path):
            with requests.get(v["href"], timeout=60, stream=True) as r:
                r.raise_for_status()
                with open(f_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)

        v["href"] = f_path

    return item


def download_items_to_local(item_col: ItemCollection, bands: list, wkdir: str, with_boto3=False) -> ItemCollection:
    """Download items locally, using appropriate download method.
    Args:
        item_col (pystac.ItemCollection): item collection with remote asset hrefs to download
        bands (list): assets to download
        wkdir (str): local working dir to use, make if not exist
        with_boto3 (bool): download items from S3 using boto3 sdk where possible
    Returns:
        local_ic (pystac.ItemCollection): item collection with local asset hrefs
    """

    makedirs(wkdir, exist_ok=True)

    items_local = []

    for item in item_col:
        logging.info("Downloading assets for item: %s", item.id)
        dl_dir = op.join(wkdir, item.id)
        makedirs(dl_dir, exist_ok=True)
        if with_boto3:
            item = Item.from_dict((download_using_boto3(item=item.to_dict(), dl_folder=dl_dir)))
        else:    
            item = Item.from_dict((download_using_requests(item=item.to_dict(), dl_folder=dl_dir)))
        items_local.append(item)

    local_ic = ItemCollection(items=items_local)

    return local_ic
