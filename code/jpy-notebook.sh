#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NOTEBOOK_DIR=$SCRIPT_DIR/notebooks

CONDA_ROOT=/home/ubuntu/anaconda3

source $CONDA_ROOT/bin/activate tensorflow_p36
# iopub_data_rate_limit needed for working with Plotly
jupyter notebook --ip localhost --port=8888 --no-browser \
    --notebook-dir=$NOTEBOOK_DIR --NotebookApp.iopub_data_rate_limit=10000000
source deactivate

# export PYTHONPATH=$DIR/../python
# NOTEBOOK_DIR=$DIR/../notebooks
# setup the address to last address
# IP_ADDR=$(hostname -I | awk '{ print $NF }')
# IP_ADDR=0.0.0.0
