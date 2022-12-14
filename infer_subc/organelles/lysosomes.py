from scipy.ndimage import median_filter, extrema
from scipy.interpolate import RectBivariateSpline

from skimage import img_as_float, filters
from skimage import morphology
from skimage.morphology import remove_small_objects, ball, disk, dilation, binary_closing, white_tophat, black_tophat
from skimage.filters import threshold_triangle, threshold_otsu, threshold_li, threshold_multiotsu, threshold_sauvola
from skimage.measure import label
from skimage.segmentation import watershed
from skimage.feature import peak_local_max

import aicssegmentation
from aicssegmentation.core.seg_dot import dot_3d_wrapper, dot_slice_by_slice, dot_2d_slice_by_slice_wrapper, dot_3d

from aicssegmentation.core.utils import topology_preserving_thinning, hole_filling, size_filter
from aicssegmentation.core.MO_threshold import MO
from aicssegmentation.core.vessel import filament_2d_wrapper, vesselnessSliceBySlice
from aicssegmentation.core.output_utils import save_segmentation, generate_segmentation_contour
from aicssegmentation.core.pre_processing_utils import (
    intensity_normalization,
    image_smoothing_gaussian_3d,
    image_smoothing_gaussian_slice_by_slice,
    edge_preserving_smoothing_3d,
)

from infer_subc.utils.img import *


##########################
#  infer_LYSOSOMES
##########################
def infer_LYSOSOMES(struct_img, CY_object, in_params) -> tuple:
    """
    Procedure to infer LYSOSOME from linearly unmixed input.

    Parameters:
    ------------
    struct_img: np.ndarray
        a 3d image containing the LYSOSOME signal

    CY_object: np.ndarray boolean
        a 3d image containing the NU labels

    in_params: dict
        holds the needed parameters

    Returns:
    -------------
    tuple of:
        object
            mask defined boundaries of Lysosomes
        parameters: dict
            updated parameters in case any needed were missing
    """
    out_p = in_params.copy()

    ###################
    # PRE_PROCESSING
    ###################
    scaling_param = [0]
    struct_img = intensity_normalization(struct_img, scaling_param=scaling_param)
    out_p["intensity_norm_param"] = scaling_param

    # make a copy for post-post processing
    scaled_signal = struct_img.copy()

    med_filter_size = 3
    # structure_img_median_3D = ndi.median_filter(struct_img,    size=med_filter_size  )
    struct_img = median_filter_slice_by_slice(struct_img, size=med_filter_size)
    out_p["median_filter_size"] = med_filter_size

    gaussian_smoothing_sigma = 1.0
    gaussian_smoothing_truncate_range = 3.0
    struct_img = image_smoothing_gaussian_slice_by_slice(
        struct_img, sigma=gaussian_smoothing_sigma, truncate_range=gaussian_smoothing_truncate_range
    )
    out_p["gaussian_smoothing_sigma"] = gaussian_smoothing_sigma
    out_p["gaussian_smoothing_truncate_range"] = gaussian_smoothing_truncate_range

    # log_img, d = log_transform( struct_img )
    # struct_img = intensity_normalization( log_img ,  scaling_param=[0] )
    struct_img = intensity_normalization(struct_img, scaling_param=[0])

    ###################
    # CORE_PROCESSING
    ###################
    # dot and filiment enhancement - 2D

    ################################
    ## PARAMETERS for this step ##
    s2_param = [[5, 0.09], [2.5, 0.07], [1, 0.01]]
    ################################
    bw_spot = dot_2d_slice_by_slice_wrapper(struct_img, s2_param)

    ################################
    ## PARAMETERS for this step ##
    f2_param = [[1, 0.15]]
    ################################
    bw_filament = filament_2d_wrapper(struct_img, f2_param)

    bw = np.logical_or(bw_spot, bw_filament)

    out_p["s2_param"] = s2_param
    out_p["f2_param"] = f2_param
    ###################
    # POST_PROCESSING
    ###################

    # 2D cleaning
    hole_max = 1600
    # discount z direction
    struct_obj = aicssegmentation.core.utils.hole_filling(bw, hole_min=0.0, hole_max=hole_max**2, fill_2d=True)
    out_p["hole_max"] = hole_max

    # # 3D
    # cleaned_img = remove_small_objects(removed_holes>0,
    #                                                             min_size=width,
    #                                                             connectivity=1,
    #                                                             in_place=False)

    small_object_max = 15
    struct_obj = aicssegmentation.core.utils.size_filter(
        struct_obj,  # wrapper to remove_small_objects which can do slice by slice
        min_size=small_object_max**3,
        method="3D",  # "slice_by_slice" ,
        connectivity=1,
    )
    out_p["small_object_max"] = small_object_max

    retval = (struct_obj, out_p)
    return retval
