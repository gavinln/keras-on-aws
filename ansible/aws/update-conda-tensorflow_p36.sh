#!/bin/bash

CONDA_ROOT=/home/ubuntu/anaconda3

source $CONDA_ROOT/bin/activate tensorflow_p36
python -c "import matplotlib; matplotlib.get_cachedir()"  # does not create cache
pip install sklearn
pip install seaborn

pip install jupyter_contrib_nbextensions
jupyter contrib nbextension install --user
cd $(jupyter --data-dir)/nbextensions
git clone https://github.com/lambdalisue/jupyter-vim-binding vim_binding
