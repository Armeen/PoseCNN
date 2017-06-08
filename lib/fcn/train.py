# --------------------------------------------------------
# FCN
# Copyright (c) 2016 RSE at UW
# Licensed under The MIT License [see LICENSE for details]
# Written by Yu Xiang
# --------------------------------------------------------

"""Train a FCN"""

from fcn.config import cfg
from gt_data_layer.layer import GtDataLayer
from gt_single_data_layer.layer import GtSingleDataLayer
from utils.timer import Timer
import numpy as np
import os
import tensorflow as tf
import sys
import threading

class SolverWrapper(object):
    """A simple wrapper around Caffe's solver.
    This wrapper gives us control over he snapshotting process, which we
    use to unnormalize the learned bounding-box regression weights.
    """

    def __init__(self, sess, network, imdb, roidb, output_dir, pretrained_model=None):
        """Initialize the SolverWrapper."""
        self.net = network
        self.imdb = imdb
        self.roidb = roidb
        self.output_dir = output_dir
        self.pretrained_model = pretrained_model

        # For checkpoint
        self.saver = tf.train.Saver()


    def snapshot(self, sess, iter):
        """Take a snapshot of the network after unnormalizing the learned
        bounding-box regression weights. This enables easy use at test-time.
        """
        net = self.net

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        infix = ('_' + cfg.TRAIN.SNAPSHOT_INFIX
                 if cfg.TRAIN.SNAPSHOT_INFIX != '' else '')
        filename = (cfg.TRAIN.SNAPSHOT_PREFIX + infix +
                    '_iter_{:d}'.format(iter+1) + '.ckpt')
        filename = os.path.join(self.output_dir, filename)

        self.saver.save(sess, filename)
        print 'Wrote snapshot to: {:s}'.format(filename)


    def train_model(self, sess, train_op, loss, learning_rate, max_iters):
        """Network training loop."""
        # add summary
        tf.summary.scalar('loss', loss)
        merged = tf.summary.merge_all()
        train_writer = tf.summary.FileWriter(self.output_dir, sess.graph)

        # intialize variables
        sess.run(tf.global_variables_initializer())
        if self.pretrained_model is not None:
            print ('Loading pretrained model '
                   'weights from {:s}').format(self.pretrained_model)
            self.net.load(self.pretrained_model, sess, True)

        tf.get_default_graph().finalize()

        last_snapshot_iter = -1
        timer = Timer()
        for iter in range(max_iters):
            timer.tic()
            summary, loss_value, lr, _ = sess.run([merged, loss, learning_rate, train_op])
            train_writer.add_summary(summary, iter)
            timer.toc()
            
            print 'iter: %d / %d, loss: %.4f, lr: %.8f, time: %.2f' %\
                    (iter+1, max_iters, loss_value, lr, timer.diff)

            if (iter+1) % (10 * cfg.TRAIN.DISPLAY) == 0:
                print 'speed: {:.3f}s / iter'.format(timer.average_time)

            if (iter+1) % cfg.TRAIN.SNAPSHOT_ITERS == 0:
                last_snapshot_iter = iter
                self.snapshot(sess, iter)

        if last_snapshot_iter != iter:
            self.snapshot(sess, iter)


    def train_gan(self, sess, train_op_d, train_op_g, loss_d, loss_true, loss_false, loss_g, loss_l1, loss_ad, max_iters):
        """Network training loop."""

        # intialize variables
        sess.run(tf.global_variables_initializer())
        if self.pretrained_model is not None:
            print ('Loading pretrained model '
                   'weights from {:s}').format(self.pretrained_model)
            self.net.load(self.pretrained_model, sess, True)

        tf.get_default_graph().finalize()

        last_snapshot_iter = -1
        timer = Timer()
        for iter in range(max_iters):
            timer.tic()
            # update discriminator
            loss_value_d, loss_value_true, loss_value_false, _ \
                = sess.run([loss_d, loss_true, loss_false, train_op_d])

            # update generator
            loss_value_g, loss_value_l1, loss_value_ad, _ = sess.run([loss_g, loss_l1, loss_ad, train_op_g])
            timer.toc()
            
            #print 'iter: %d / %d, loss_d: %.4f, loss_true: %.4f, loss_false: %.4f, lr_d: %.8f, time: %.2f' %\
            #        (iter+1, max_iters, loss_value_d, loss_value_true, loss_value_false, lr_d, timer.diff)
            print 'iter: %d / %d, loss_d: %.4f, loss_true: %.4f, loss_false: %.4f, loss_g: %.4f, loss_l1: %.4f, loss_ad: %.4f, time: %.2f' %\
                    (iter+1, max_iters, loss_value_d, loss_value_true, loss_value_false, loss_value_g, loss_value_l1, loss_value_ad, timer.diff)

            if (iter+1) % (10 * cfg.TRAIN.DISPLAY) == 0:
                print 'speed: {:.3f}s / iter'.format(timer.average_time)

            if (iter+1) % cfg.TRAIN.SNAPSHOT_ITERS == 0:
                last_snapshot_iter = iter
                self.snapshot(sess, iter)

        if last_snapshot_iter != iter:
            self.snapshot(sess, iter)


    def train_model_vertex(self, sess, train_op, loss, loss_cls, loss_vertex, learning_rate, max_iters):
        """Network training loop."""
        # add summary
        # tf.summary.scalar('loss', loss)
        # merged = tf.summary.merge_all()
        # train_writer = tf.summary.FileWriter(self.output_dir, sess.graph)

        # intialize variables
        sess.run(tf.global_variables_initializer())
        if self.pretrained_model is not None:
            print ('Loading pretrained model '
                   'weights from {:s}').format(self.pretrained_model)
            self.net.load(self.pretrained_model, sess, True)

        tf.get_default_graph().finalize()

        # tf.train.write_graph(sess.graph_def, self.output_dir, 'model.pbtxt')

        last_snapshot_iter = -1
        timer = Timer()
        for iter in range(max_iters):
            timer.tic()
            loss_value, loss_cls_value, loss_vertex_value, lr, _ = sess.run([loss, loss_cls, loss_vertex, learning_rate, train_op])
            # train_writer.add_summary(summary, iter)
            timer.toc()
            
            print 'iter: %d / %d, loss: %.4f, loss_cls: %.4f, loss_vertex: %.4f, lr: %.8f, time: %.2f' %\
                    (iter+1, max_iters, loss_value, loss_cls_value, loss_vertex_value, lr, timer.diff)

            if (iter+1) % (10 * cfg.TRAIN.DISPLAY) == 0:
                print 'speed: {:.3f}s / iter'.format(timer.average_time)

            if (iter+1) % cfg.TRAIN.SNAPSHOT_ITERS == 0:
                last_snapshot_iter = iter
                self.snapshot(sess, iter)

        if last_snapshot_iter != iter:
            self.snapshot(sess, iter)


def get_training_roidb(imdb):
    """Returns a roidb (Region of Interest database) for use in training."""
    if cfg.TRAIN.USE_FLIPPED:
        print 'Appending horizontally-flipped training examples...'
        imdb.append_flipped_images()
        print 'done'

    return imdb.roidb


def load_and_enqueue(sess, net, roidb, num_classes, coord):
    if cfg.TRAIN.SINGLE_FRAME:
        # data layer
        data_layer = GtSingleDataLayer(roidb, num_classes)
    else:
        # data layer
        data_layer = GtDataLayer(roidb, num_classes)

    while not coord.should_stop():
        blobs = data_layer.forward()

        if cfg.INPUT == 'RGBD':
            data_blob = blobs['data_image_color']
            data_p_blob = blobs['data_image_depth']
        elif cfg.INPUT == 'COLOR':
            data_blob = blobs['data_image_color']
        elif cfg.INPUT == 'DEPTH':
            data_blob = blobs['data_image_depth']
        elif cfg.INPUT == 'NORMAL':
            data_blob = blobs['data_image_normal']

        if cfg.TRAIN.SINGLE_FRAME:
            if cfg.INPUT == 'RGBD':
                if cfg.TRAIN.VERTEX_REG:
                    feed_dict={net.data: data_blob, net.data_p: data_p_blob, net.gt_label_2d: blobs['data_label'], net.keep_prob: 0.5, \
                               net.vertex_targets: blobs['data_vertex_targets'], net.vertex_weights: blobs['data_vertex_weights'], net.poses: blobs['data_pose']}

                else:
                    feed_dict={net.data: data_blob, net.data_p: data_p_blob, net.gt_label_2d: blobs['data_label'], net.keep_prob: 0.5}

            else:
                if cfg.TRAIN.VERTEX_REG:
                    if cfg.TRAIN.GAN:
                        feed_dict={net.data: blobs['data_image_color_rescale'], net.data_gt: blobs['data_vertex_images'], net.keep_prob: 0.5, \
                                   net.z: blobs['data_gan_z']}
                    else:
                        feed_dict={net.data: data_blob, net.gt_label_2d: blobs['data_label'], net.keep_prob: 0.5, \
                                   net.vertex_targets: blobs['data_vertex_targets'], net.vertex_weights: blobs['data_vertex_weights'], net.poses: blobs['data_pose']}

                else:
                    if cfg.TRAIN.GAN:
                        feed_dict={net.data: blobs['data_image_color_rescale'], net.data_gt: blobs['data_vertex_images'], net.keep_prob: 0.5, \
                                   net.z: blobs['data_gan_z']}
                    else:
                        feed_dict={net.data: data_blob, net.gt_label_2d: blobs['data_label'], net.keep_prob: 0.5}
        else:
            if cfg.INPUT == 'RGBD':
                feed_dict={net.data: data_blob, net.data_p: data_p_blob, net.gt_label_2d: blobs['data_label'], \
                           net.depth: blobs['data_depth'], net.meta_data: blobs['data_meta_data'], \
                           net.state: blobs['data_state'], net.weights: blobs['data_weights'], net.points: blobs['data_points'], net.keep_prob: 0.5}
            else:
                feed_dict={net.data: data_blob, net.gt_label_2d: blobs['data_label'], \
                           net.depth: blobs['data_depth'], net.meta_data: blobs['data_meta_data'], \
                           net.state: blobs['data_state'], net.weights: blobs['data_weights'], net.points: blobs['data_points'], net.keep_prob: 0.5}

        sess.run(net.enqueue_op, feed_dict=feed_dict)

def loss_cross_entropy(scores, labels):
    """
    scores: a list of tensors [batch_size, height, width, num_classes]
    labels: a list of tensors [batch_size, height, width, num_classes]
    """

    with tf.name_scope('loss'):
        loss = 0
        for i in range(cfg.TRAIN.NUM_STEPS):
            score = scores[i]
            label = labels[i]
            cross_entropy = -tf.reduce_sum(label * score, reduction_indices=[3])
            loss += tf.div(tf.reduce_sum(cross_entropy), tf.reduce_sum(label))
        loss /= cfg.TRAIN.NUM_STEPS
    return loss

def loss_cross_entropy_single_frame(scores, labels):
    """
    scores: a tensor [batch_size, height, width, num_classes]
    labels: a tensor [batch_size, height, width, num_classes]
    """

    with tf.name_scope('loss'):
        cross_entropy = -tf.reduce_sum(labels * scores, reduction_indices=[3])
        loss = tf.div(tf.reduce_sum(cross_entropy), tf.reduce_sum(labels))

    return loss


def train_net(network, imdb, roidb, output_dir, pretrained_model=None, max_iters=40000):
    """Train a Fast R-CNN network."""

    if cfg.TRAIN.SINGLE_FRAME:
        # classification loss
        if cfg.NETWORK == 'FCN8VGG':
            scores = network.prob
            labels = network.gt_label_2d_queue
            loss = loss_cross_entropy_single_frame(scores, labels)
        else:
            if cfg.TRAIN.VERTEX_REG:
                scores = network.get_output('prob')
                labels = network.get_output('gt_label_2d')
                loss_cls = loss_cross_entropy_single_frame(scores, labels)

                vertex_pred = network.get_output('vertex_pred')
                vertex_targets = network.get_output('vertex_targets')
                vertex_weights = network.get_output('vertex_weights')
                loss_vertex = tf.div( tf.reduce_sum(tf.multiply(vertex_weights, tf.abs(tf.subtract(vertex_pred, vertex_targets)))), tf.reduce_sum(vertex_weights) )

                loss_matching = network.get_output('matching_loss')[0]
                print loss_matching
                
                loss = loss_cls + loss_vertex + loss_matching
            else:
                scores = network.get_output('prob')
                labels = network.get_output('gt_label_2d')
                loss = loss_cross_entropy_single_frame(scores, labels)
    else:
        # classification loss
        scores = network.get_output('outputs')
        labels = network.get_output('labels_gt_2d')
        loss = loss_cross_entropy(scores, labels)

    # optimizer
    global_step = tf.Variable(0, trainable=False)
    starter_learning_rate = cfg.TRAIN.LEARNING_RATE
    learning_rate = tf.train.exponential_decay(starter_learning_rate, global_step,
                                           cfg.TRAIN.STEPSIZE, 0.1, staircase=True)
    momentum = cfg.TRAIN.MOMENTUM
    train_op = tf.train.MomentumOptimizer(learning_rate, momentum).minimize(loss, global_step=global_step)
    
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
    with tf.Session(config=tf.ConfigProto(allow_soft_placement=True, gpu_options=gpu_options)) as sess:

        sw = SolverWrapper(sess, network, imdb, roidb, output_dir, pretrained_model=pretrained_model)

        # thread to load data
        coord = tf.train.Coordinator()
        if cfg.TRAIN.VISUALIZE:
            load_and_enqueue(sess, network, roidb, imdb.num_classes, coord)
        else:
            t = threading.Thread(target=load_and_enqueue, args=(sess, network, roidb, imdb.num_classes, coord))
            t.start()

        print 'Solving...'
        if cfg.TRAIN.VERTEX_REG:
            sw.train_model_vertex(sess, train_op, loss, loss_cls, loss_vertex, learning_rate, max_iters)
        else:
            sw.train_model(sess, train_op, loss, learning_rate, max_iters)
        print 'done solving'

        sess.run(network.close_queue_op)
        coord.request_stop()
        coord.join([t])

# train GAN
def train_gan(network, imdb, roidb, output_dir, pretrained_model=None, max_iters=40000):
    """Train a GAN."""

    # define losses

    # classification loss for the discriminator
    outputs_d = network.get_output('outputs_d')
    scores_d_true = outputs_d[1]
    scores_d_false = outputs_d[0]

    loss_true = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(scores_d_true, tf.ones_like(scores_d_true)))
    loss_false = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(scores_d_false, tf.zeros_like(scores_d_false)))
    loss_d = loss_true + loss_false

    # loss for the generator
    output_g = network.get_output('output_g')
    data_gt = network.get_output('data_gt')
    loss_l1 = tf.reduce_mean(tf.abs(tf.sub(output_g, data_gt)))
    loss_ad = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(scores_d_false, tf.ones_like(scores_d_false)))
    loss_g = 0 * loss_l1 + 0.2 * loss_ad

    # optimizer
    train_op_d = tf.train.AdamOptimizer(cfg.TRAIN.LEARNING_RATE, cfg.TRAIN.MOMENTUM).minimize(loss_d)
    train_op_g = tf.train.AdamOptimizer(cfg.TRAIN.LEARNING_RATE, cfg.TRAIN.MOMENTUM).minimize(loss_g)
    
    with tf.Session(config=tf.ConfigProto(allow_soft_placement=True)) as sess:

        sw = SolverWrapper(sess, network, imdb, roidb, output_dir, pretrained_model=pretrained_model)

        # thread to load data
        coord = tf.train.Coordinator()
        if cfg.TRAIN.VISUALIZE:
            load_and_enqueue(sess, network, roidb, imdb.num_classes, coord)
        else:
            t = threading.Thread(target=load_and_enqueue, args=(sess, network, roidb, imdb.num_classes, coord))
            t.start()

        print 'Solving...'
        sw.train_gan(sess, train_op_d, train_op_g, loss_d, loss_true, loss_false, loss_g, loss_l1, loss_ad, max_iters)
        print 'done solving'

        sess.run(network.close_queue_op)
        coord.request_stop()
        coord.join([t])
