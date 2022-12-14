import numpy as np

from platform import system
import os

from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Union, List, Any, Tuple

from aicsimageio.writers import OmeTiffWriter
from napari_aicsimageio.core import reader_function as napari_aiscimageio_reader_fn


@dataclass
class AICSImageReaderWrap:
    """
    Simple dataclass wrapper for the AICSImage output to prepare for imprting to our bioim class
    TODO: make a nice reppr
    """

    name: str
    image: np.ndarray
    meta: Dict[str, Any]
    raw_meta: Tuple[Dict[str, Any], Union[Dict[str, Any], List]]

    def __init__(self, name: str, image: np.ndarray, meta: Dict[str, Any]):
        self.name = name
        self.image = image
        self.meta = meta
        self.raw_meta = get_raw_meta_data(meta)


def export_ome_tiff(data_in, meta_in, img_name, out_path, curr_chan=0) -> str:
    """
    #  data_in: types.ArrayLike,
    #  meta_in: dict,
    # img_name: types.PathLike,
    # out_path: types.PathLike,
    # curr_chan: int
    # assumes a single image
    """

    out_name = out_path + img_name + ".ome.tiff"

    image_names = [img_name]
    print(image_names)
    # chan_names = meta_in['metadata']['aicsimage'].channel_names

    physical_pixel_sizes = [meta_in["metadata"]["aicsimage"].physical_pixel_sizes]

    dimension_order = ["CZYX"]
    channel_names = [meta_in["metadata"]["aicsimage"].channel_names[curr_chan]]
    if len(data_in.shape) == 3:  # single channel zstack
        data_in = data_in[np.newaxis, :, :, :]

    if data_in.dtype == "bool":
        data_in = data_in.astype(np.uint8)
        data_in[data_in > 0] = 255

    out_ome = OmeTiffWriter.build_ome(
        [data_in.shape],
        [data_in.dtype],
        channel_names=channel_names,  # type: ignore
        image_name=image_names,
        physical_pixel_sizes=physical_pixel_sizes,
        dimension_order=dimension_order,
    )

    OmeTiffWriter.save(
        data_in,
        out_name,
        dim_order=dimension_order,
        channel_names=channel_names,
        image_names=image_names,
        physical_pixel_sizes=physical_pixel_sizes,
        ome_xml=out_ome,
    )
    return out_name


### UTILS
def etree_to_dict(t):
    """
    etree dumper from stackoverflow
    """
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(("@" + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]["#text"] = text
        else:
            d[t.tag] = text
    return d


def get_raw_meta_data(meta_dict):
    """
    not sure why the linux backend works for ome... need to solve
    """
    curr_platform = system()

    if curr_platform == "Linux":
        raw_meta_data = meta_dict["metadata"]["raw_image_metadata"].dict()
        ome_types = meta_dict["metadata"]["ome_types"]
    elif curr_platform == "Darwin":
        raw_meta_data = meta_dict["metadata"]["raw_image_metadata"]
        ome_types = []
    else:
        raw_meta_data = meta_dict["metadata"]["raw_image_metadata"]
        ome_types = []
        print(f"warning: platform = '{curr_platform}' is untested")
    return (raw_meta_data, ome_types)


def read_input_image(image_name):
    """
    send output from napari aiscioimage reader wrapped in dataclass
    """
    data_out, meta_out, layer_type = napari_aiscimageio_reader_fn(image_name)[0]
    return AICSImageReaderWrap(image_name, data_out, meta_out)


# function to collect all the
def list_image_files(data_folder: Path, file_type: str) -> List:
    """
    get a list of all the filetypes
    TODO: aics has cleaner functions than this "lambda"
    """
    return [os.path.join(data_folder, f_name) for f_name in os.listdir(data_folder) if f_name.endswith(file_type)]
