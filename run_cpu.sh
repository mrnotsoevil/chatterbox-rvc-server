#!/bin/bash

export CHATTERBOX_DEVICE=cpu
conda run --name chatterbox_rvc_server --live-stream python -m server
