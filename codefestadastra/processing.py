from contextlib import contextmanager
import os

import rasterio
from rasterio import Affine
from rasterio.enums import Resampling

import numpy as np
from rasterio.warp import reproject, Resampling

from rasterio.plot import show
from osgeo import gdal
from pathlib import Path

# ------------------------------------------------------------ Problema 1 ------------------------------------------------------------


def reproject_raster(in_path, out_path):
    """
    It takes a raster, randomly displaces it, and then saves it to a new file.

    :param in_path: The path to the input raster
    :param out_path: The path to the output file
    """
    with rasterio.open(in_path) as src:
        src_transform = src.transform
        random_displacement = np.random.uniform(100, 1000)

        dst_transform = src_transform

        valid_random_transform = src_transform * Affine.translation(
            src.width * random_displacement, src.height * random_displacement
        )

        data = src.read()

        # Change the transform to the new one
        kwargs = src.meta
        kwargs["transform"] = valid_random_transform
        kwargs["nodata"] = 0

    with rasterio.open(out_path, "w", **kwargs) as dst:

        for i, band in enumerate(data, 1):
            dest = np.zeros_like(band)

            # Reproject the data to the new transform
            reproject(
                band,
                dest,
                src_transform=src_transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=src.crs,
                resampling=Resampling.nearest,
            )

            dst.write(dest, indexes=i)


# ------------------------------------------------------------ Problema 2 ------------------------------------------------------------


@contextmanager
def resample_raster(raster, out_path, blur_factor, scale_factor):
    """
    It takes a raster, resamples it, and writes it to a new file

    :param raster: the raster to be resampled
    :param out_path: the path to the output file
    :param blur_factor: This is the amount of blurring you want to apply to the image. The higher the
    number, the more blurring
    :param scale_factor: The factor by which you want to scale the raster
    """

    current_transform = raster.transform
    filename = out_path.split("/")[-1] or out_path

    # rescale the metadata
    new_transform = Affine(
        current_transform.a / scale_factor,
        current_transform.b,
        current_transform.c,
        current_transform.d,
        current_transform.e / scale_factor,
        current_transform.f,
    )

    height = raster.height / scale_factor
    width = raster.width / scale_factor

    profile = raster.profile

    # In case the file is not .tiff or .jp2, then we assume it is .img
    format_driver = "HFA"

    if filename.split(".")[-1] == "tif" or filename.split(".")[-1] == "tiff":
        format_driver = "GTiff"
    elif filename.split(".")[-1] == "jp2":
        format_driver = "JP2OpenJPEG"

    profile.update(
        transform=new_transform,
        driver=format_driver,
        height=height,
        width=width,
        crs=raster.crs,
    )

    data = raster.read(
        out_shape=(
            int(raster.count),
            int(height * blur_factor),
            int(width * blur_factor),
        ),
        resampling=Resampling.cubic,
    )

    # Write the data to the new file and yield it so that it can be used
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(data)
        yield data


def blur_and_resize(path: str, out_path: str):
    """
    It takes a raster, resamples it to a new resolution, and blurs it

    :param path: the path to the original raster
    :param out_path: the path to the output file
    """

    original_size = os.path.getsize(path) / 1000
    with rasterio.open(path) as src:
        with resample_raster(src, out_path, 0.9, 5.5) as resampled:
            new_size = os.path.getsize(out_path) / 1000
            return f"Original size: {original_size} \nNew size: {new_size} \nNew size rate: {round((new_size / original_size) * 10000, 3)}%"


# ------------------------------------------------------------ Problema 3 ------------------------------------------------------------


def compress_raster_given_quality(
    input_path: str, out_path: str, quality: int
) -> float:
    """
    It takes a raster file, compresses it using the JP2OOpenJPEG format, and returns the compression ratio.

    :param input_path: The path to the input file
    :type input_path: str
    :param out_path: str = "compression_output_quality10.tif"
    :type out_path: str
    :return: The ratio of the size of the output file to the size of the input file.
    """

    # Basic quality input validator
    if quality > 100 or quality < 0:
        raise ValueError("Quality must be between 0 and 100")

    gdal.UseExceptions()

    translate_options = gdal.TranslateOptions(
        format="JP2OpenJPEG",
        creationOptions=[f"QUALITY={quality}", "REVERSIBLE=YES", "YCBCR420=NO"],
    )

    outds = gdal.Translate(
        "compression_output_quality10.tif",
        input_path,
        options=translate_options,
    )

    input_file = Path(input_path)

    size_input_file = input_file.stat().st_size

    output_file = Path(output_file)

    size_output_file = out_path.stat().st_size

    return size_output_file / size_input_file


def compress_raster_low_quality_high_compression(input_path: str, out_path: str):
    """
    > This function compresses a raster to a low quality and high compression ratio
    
    :param input_path: The path to the input raster file
    :type input_path: str
    :param out_path: The path to the output file
    :type out_path: str
    """
    compress_raster_given_quality(input_path, out_path, 10)


def compress_raster_high_quality_low_compression(input_path: str, out_path: str):
    """
    > This function compresses a raster to a high quality, low compression ratio
    
    :param input_path: The path to the input raster
    :type input_path: str
    :param out_path: The path to the output file
    :type out_path: str
    """
    compress_raster_given_quality(input_path, out_path, 100)
