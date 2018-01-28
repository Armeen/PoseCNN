#!/bin/bash

set -x
set -e

export PYTHONUNBUFFERED="True"
export CUDA_VISIBLE_DEVICES=$1

LOG="experiments/logs/linemod_can_train.txt.`date +'%Y-%m-%d_%H-%M-%S'`"
exec &> >(tee -a "$LOG")
echo Logging output to "$LOG"

export LD_PRELOAD=/usr/lib/libtcmalloc.so.4

# train for labeling
time ./tools/train_net.py --gpu 0 \
  --network vgg16_convs \
  --weights data/imagenet_models/vgg16_convs.npy \
  --imdb linemod_can_train \
  --cfg experiments/cfgs/linemod_can.yml \
  --iters 40000

# train for pose
time ./tools/train_net.py --gpu 0 \
  --network vgg16_convs \
  --weights data/imagenet_models/vgg16.npy \
  --ckpt output/linemod/linemod_can_train/vgg16_fcn_color_single_frame_linemod_can_iter_40000.ckpt \
  --imdb linemod_can_train \
  --cfg experiments/cfgs/linemod_can_pose.yml \
  --iters 80000
