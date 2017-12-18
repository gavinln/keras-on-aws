#!/bin/bash

CONDA_ROOT=/home/ubuntu/anaconda3

source $CONDA_ROOT/bin/activate tensorflow_p36
python -c "import matplotlib; matplotlib.get_cachedir()"  # does not create cache
pip install sklearn
pip install seaborn
pip install keras-tqdm

# install jupyter notebook extensions
pip install jupyter_contrib_nbextensions
jupyter contrib nbextension install --user

# disable nbpresent as it does not work correctly
jupyter nbextension disable nbpresent --py
jupyter serverextension disable nbpresent --py

# enable hide_input_all extension to hide/show all code cells
jupyter-nbextension enable hide_input_all/main --py

# install RISE for slideshows
pip install RISE
jupyter-nbextension install rise --py --sys-prefix
jupyter-nbextension enable rise --py --sys-prefix

# install vim bindings
cd $(jupyter --data-dir)/nbextensions
if [[ ! -d vim_binding ]]; then
    git clone https://github.com/lambdalisue/jupyter-vim-binding vim_binding
fi

