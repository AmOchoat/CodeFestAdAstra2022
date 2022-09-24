

from contextlib import contextmanager  
import os

import rasterio
from rasterio import Affine
from rasterio.enums import Resampling
from rasterio.plot import show

import numpy as np
from rasterio.warp import reproject, Resampling  

# ------------------------------------------------------------ Problema 1 ------------------------------------------------------------

def reproject_raster(in_path, out_path):
    with rasterio.open(in_path) as src:
        src_transform = src.transform
        r = np.random.uniform(100,1000)

        # Zoom out by a factor of 2 from the center of the source
        # dataset. The destination transform is the product of the
        # source transform, a translation down and to the right, and
        # a scaling.
        dst_transform = src_transform
        x_transform = src_transform*Affine.translation(
            src.width*r, src.height*r)

        data = src.read()

        kwargs = src.meta
        kwargs['transform'] = x_transform
        kwargs['nodata'] = 0

    with rasterio.open(out_path, 'w', **kwargs) as dst:

        for i, band in enumerate(data, 1):
            dest = np.zeros_like(band)

            reproject(
                band,
                dest,
                src_transform=src_transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=src.crs,
                resampling=Resampling.nearest)

            dst.write(dest, indexes=i)

# ------------------------------------------------------------ Problema 2 ------------------------------------------------------------

@contextmanager
def resample_raster(raster, out_path, blur_factor, scale_factor):
    t = raster.transform
    filename = out_path.split("/")[-1] or out_path
    
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

    data = raster.read(
            out_shape=(int(raster.count), int(height * blur_factor), int(width * blur_factor)),
            resampling=Resampling.cubic
    )

    with rasterio.open(out_path,'w', **profile) as dst:
        dst.write(data)
        yield data

def blur_and_resize(path, out_path):
    original_size = os.path.getsize(path) / 1000
    with rasterio.open(path) as src:
        with resample_raster(src, out_path, 0.9, 5.5) as resampled:
            new_size = os.path.getsize(out_path) / 1000
            print(f"Original size: {original_size} \nNew size: {new_size} \nNew size rate: {round((new_size / original_size) * 10000, 3)}%")