
# bioformats_jar was screwing things up. with OME
conda create -n napari-env python=3.9 pip notebook 
conda activate napari-env
pip install 'napari[all]'
pip install scipy scikit-learn matplotlib #jupyter
pip install aicsimageio 
pip install aicspylibczi
pip install aicssegmentation #downgrades napari and scikitlearn

pip install napari-aicsimageio  

# pip install infer_subc
# pip install napari-infer-subc  

# pip install opencv-python
# pip install opencv-contrib-python
#pip install opencv-python-headless  # seems to already be installed


# these are missing from some Ubuntu distros
# sudo apt-get install libegl1 libdbus-1-3 libxkbcommon-x11-0 \
#     libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
#     libxcb-render-util0 libxcb-xinerama0 libxcb-xinput0 libxcb-xfixes0
