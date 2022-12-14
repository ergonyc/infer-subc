from scipy.ndimage import median_filter, extrema
from scipy.interpolate import RectBivariateSpline

from skimage import img_as_float, filters
from skimage import morphology
from skimage.morphology import remove_small_objects, ball, disk, dilation, binary_closing, white_tophat, black_tophat
from skimage.filters import threshold_triangle, threshold_otsu, threshold_li, threshold_multiotsu, threshold_sauvola
from skimage.measure import label
from skimage.segmentation import watershed
from skimage.feature import peak_local_max

# from napari_aicsimageio.core import  reader_function
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
#  infer_MITOCHONDRIA
##########################
def infer_MITOCHONDRIA(struct_img, CY_object, in_params) -> tuple:
    """
    Procedure to infer MITOCHONDRIA  from linearly unmixed input.

    Parameters:
    ------------
    struct_img: np.ndarray
        a 3d image containing the MITOCHONDRIA signal

    CY_object: np.ndarray boolean
        a 3d image containing the NU labels

    in_params: dict
        holds the needed parameters

    Returns:
    -------------
    tuple of:
        object
            mask defined boundaries of MITOCHONDRIA
        parameters: dict
            updated parameters in case any needed were missing
    """
    out_p = in_params.copy()

    ###################
    # PRE_PROCESSING
    ###################
    scaling_param = [0, 9]
    struct_img = intensity_normalization(struct_img, scaling_param=scaling_param)
    out_p["intensity_norm_param"] = scaling_param

    # make a copy for post-post processing
    scaled_signal = struct_img.copy()

    med_filter_size = 3
    structure_img = median_filter(struct_img, size=med_filter_size)
    out_p["median_filter_size"] = med_filter_size

    gaussian_smoothing_sigma = 1.3
    gaussian_smoothing_truncate_range = 3.0
    struct_img = image_smoothing_gaussian_3d(
        struct_img, sigma=gaussian_smoothing_sigma, truncate_range=gaussian_smoothing_truncate_range
    )
    out_p["gaussian_smoothing_sigma"] = gaussian_smoothing_sigma
    out_p["gaussian_smoothing_truncate_range"] = gaussian_smoothing_truncate_range

    # log_img, d = log_transform( struct_img )
    # struct_img = intensity_normalization( log_img ,  scaling_param=[0] )
    # struct_img = intensity_normalization( struct_img ,  scaling_param=[0] )

    ###################
    # CORE_PROCESSING
    ###################
    ################################
    ## PARAMETERS for this step ##
    vesselness_sigma = [1.5]
    vesselness_cutoff = 0.16
    # 2d vesselness slice by slice
    response = vesselnessSliceBySlice(struct_img, sigmas=vesselness_sigma, tau=1, whiteonblack=True)
    bw = response > vesselness_cutoff

    out_p["vesselness_sigma"] = vesselness_sigma
    out_p["vesselness_cutoff"] = vesselness_cutoff

    ###################
    # POST_PROCESSING
    ###################

    # MT_object = remove_small_objects(bw > 0, min_size=small_object_max**2, connectivity=1, in_place=False)
    small_object_max = 10
    struct_obj = size_filter(
        bw,  # wrapper to remove_small_objects which can do slice by slice
        min_size=small_object_max**3,
        method="3D",  # "slice_by_slice" ,
        connectivity=1,
    )
    out_p["small_object_max"] = small_object_max

    retval = (struct_obj, out_p)
    return retval
