

from contextlib import contextmanager  
from rasterio import Affine
from rasterio.enums import Resampling
from rasterio.plot import show

import os
import rasterio

@contextmanager
def resample_raster(raster, path, blur_factor, scale_factor):
    t = raster.transform
    filename = path.split("/")[-1] or path

    # rescale the metadata
    transform = Affine(t.a / scale_factor, t.b, t.c, t.d, t.e / scale_factor, t.f)
    height = raster.height / scale_factor
    width = raster.width / scale_factor

    profile = raster.profile
    
    if (filename.split(".")[-1] == "tif" or filename.split(".")[-1] == "tiff"):
        profile.update(transform=transform, driver='GTiff', height=height, width=width, crs=raster.crs)
    elif filename.split(".")[-1] == "jp2":
        profile.update(transform=transform, driver='JP2OpenJPEG', height=height, width=width, crs=raster.crs)
    else:
        profile.update(transform=transform, driver='HFA', height=height, width=width, crs=raster.crs)

    data = raster.read( # Note changed order of indexes, arrays are band, row, col order not row, col, band
            out_shape=(int(raster.count), int(height * blur_factor), int(width * blur_factor)),
            resampling=Resampling.cubic)

    with rasterio.open("preview_" + filename,'w', **profile) as dst:
        dst.write(data)
        yield data

def blur_and_resize(path):
    original_size = os.path.getsize(path) / 1000
    with rasterio.open(path) as src:
        with resample_raster(src, path, 0.9, 5.5) as resampled:
            new_filename = "preview_" + path.split("/")[-1]
            new_path = "/".join(path.split("/")[:-1]) + new_filename
            new_size = os.path.getsize(new_path) / 1000
            print(f"Original size: {original_size} \nNew size: {new_size} \nNew size rate: {round((new_size / original_size) * 10000, 3)}%")
