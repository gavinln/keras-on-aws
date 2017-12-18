#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NOTEBOOK_DIR=$SCRIPT_DIR/notebooks

CONDA_ROOT=/home/ubuntu/anaconda3

source $CONDA_ROOT/bin/activate tensorflow_p36
jupyter nbconvert --to slides --post serve --ServePostProcessor.port=8888 \
    ~/code/notebooks/keras/06-Sentiment_analysis_movie_reviews.ipynb
