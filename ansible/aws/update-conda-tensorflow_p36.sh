#!/bin/bash

CONDA_ROOT=/home/ubuntu/anaconda3

source $CONDA_ROOT/bin/activate tensorflow_p36
pip install sklearn
pip install seaborn

# pip install jupyter_contrib_nbextensions
