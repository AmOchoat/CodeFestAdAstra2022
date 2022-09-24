from codefestadastra import processing

# Case of use of blur_and_resize method - Problema 2
processing.reproject_raster("./tests_assets/test.tiff", "./tests_results/offuscated_test1.tiff")

# Case of use of blur_and_resize method - Problema 2
processing.blur_and_resize("./tests_assets/test.tiff",  "./tests_results/offuscated_test1.tiff")

