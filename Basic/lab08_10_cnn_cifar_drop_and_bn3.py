# -*- coding: utf-8 -*-
from __future__ import division

import tensorflow as tf
import numpy as np
import os
import shutil
import time

import load_data

x_train, x_validation, x_test, y_train, y_validation, y_test \
    = load_data.load_cifar('./data/cifar/', seed=0, as_image=True, scaling=True)

BOARD_PATH = "./board/lab08-10_board"
INPUT_DIM = np.size(x_train, 1)
NCLASS = len(np.unique(y_train))
BATCH_SIZE = 32

TOTAL_EPOCH = 100
ALPHA = 0
INIT_LEARNING_RATE = 0.001

ntrain = len(x_train)
nvalidation = len(x_validation)
ntest = len(x_test)

image_width = np.size(x_train, 1)
image_height = np.size(x_train, 2)
n_channels = np.size(x_train, 3)

print("The number of train samples : ", ntrain)
print("The number of validation samples : ", nvalidation)
print("The number of test samples : ", ntest)


def l1_loss(tensor_op, name='l1_loss'):
    output = tf.reduce_sum(tf.abs(tensor_op), name=name)
    return output


def l2_loss(tensor_op, name='l2_loss'):
    output = tf.reduce_sum(tf.square(tensor_op), name=name) / 2
    return output


def linear(tensor_op, output_dim, weight_decay=False, regularizer=None, with_W=False, name='linear'):
    with tf.variable_scope(name):
        W = tf.get_variable(name='W', shape=[tensor_op.get_shape()[-1], output_dim], dtype=tf.float32,
                            initializer=tf.glorot_uniform_initializer())
        b = tf.get_variable(name='b', shape=[output_dim], dtype=tf.float32,
                            initializer=tf.constant_initializer(0.0))
        h = tf.nn.bias_add(tf.matmul(tensor_op, W), b, name='h')

        if weight_decay:
            if regularizer == 'l1':
                wd = l1_loss(W)
            elif regularizer == 'l2':
                wd = l2_loss(W)
            else:
                wd = tf.constant(0.)
        else:
            wd = tf.constant(0.)

        tf.add_to_collection("weight_decay", wd)

        if with_W:
            return h, W
        else:
            return h


def relu_layer(tensor_op, output_dim, weight_decay=False, regularizer=None,
               keep_prob=1.0, is_training=False, with_W=False, name='relu_layer'):
    with tf.variable_scope(name):
        W = tf.get_variable(name='W', shape=[tensor_op.get_shape()[-1], output_dim], dtype=tf.float32,
                            initializer=tf.glorot_uniform_initializer())
        b = tf.get_variable(name='b', shape=[output_dim], dtype=tf.float32,
                            initializer=tf.constant_initializer(0.0))
        pre_activation = tf.nn.bias_add(tf.matmul(tensor_op, W), b, name='pre_op')
        bn = tf.contrib.layers.batch_norm(pre_activation,
                                          is_training=is_training,
                                          updates_collections=None)
        h = tf.nn.relu(bn, name='relu_op')
        dr = tf.nn.dropout(h, keep_prob=keep_prob, name='dropout_op')

        if weight_decay:
            if regularizer == 'l1':
                wd = l1_loss(W)
            elif regularizer == 'l2':
                wd = l2_loss(W)
            else:
                wd = tf.constant(0.)
        else:
            wd = tf.constant(0.)

        tf.add_to_collection("weight_decay", wd)

        if with_W:
            return dr, W
        else:
            return dr


def to_flat(tensor_op, name):
    with tf.variable_scope(name):
        input_shape = tensor_op.get_shape().as_list()
        dim = np.prod(input_shape[1:])
        flat = tf.reshape(tensor_op, [-1, dim])
    return flat


def conv2d(tensor_op, stride_w, stride_h, shape, name='Conv'):
    with tf.variable_scope(name):
        W = tf.get_variable(name='W', shape=shape, dtype=tf.float32,
                            initializer=tf.truncated_normal_initializer())
        b = tf.get_variable(name='b', shape=shape[-1], dtype=tf.float32,
                            initializer=tf.constant_initializer(0.0))
        conv = tf.nn.conv2d(tensor_op, W, strides=[1, stride_w, stride_h, 1], padding='SAME', name='conv')
    return conv


def max_pooling(tensor_op, ksize_w, ksize_h, stride_w, stride_h, name='MaxPool'):
    with tf.variable_scope(name):
        p = tf.nn.max_pool(tensor_op, ksize=[1, ksize_w, ksize_h, 1], strides=[1, stride_w, stride_h, 1],
                           padding='SAME', name='p')
    return p


def dropout_layer(tensor_op, keep_prob, name):
    with tf.variable_scope(name):
        d = tf.nn.dropout(tensor_op, keep_prob=keep_prob, name = 'd')
    return d


def bn_layer(x, is_training, name):
    with tf.variable_scope(name):
        bn = tf.contrib.layers.batch_norm(x, updates_collections=None, scale=True, is_training=is_training)
        post_activation = tf.nn.relu(bn, name='relu')
    return post_activation


with tf.variable_scope("Inputs"):
    X = tf.placeholder(shape=[None, image_width, image_height, n_channels], dtype=tf.float32, name='X')
    Y = tf.placeholder(shape=[None, 1], dtype=tf.int32, name='Y')
    Y_one_hot = tf.reshape(tf.one_hot(Y, NCLASS), [-1, NCLASS], name='Y_one_hot')
    keep_prob = tf.placeholder(tf.float32, name='keep_prob')
    learning_rate = tf.placeholder(tf.float32, name='learning_rate')
    is_training = tf.placeholder(tf.bool, name='is_training')

h1_1 = conv2d(X, 1, 1, [3, 3, n_channels, 32], name='Conv1_1')
h1_2 = conv2d(h1_1, 1, 1, [5, 5, 32, 32], name='Conv1_2')
h1_3 = conv2d(h1_2, 1, 1, [7, 7, 32, 32], name='Conv1_3')
b1 = bn_layer(h1_3, is_training, name='bn1')
p1 = max_pooling(b1, 2, 2, 2, 2, name='MaxPool1')
d1 = dropout_layer(p1, keep_prob=keep_prob, name='Dropout1')

h2_1 = conv2d(d1, 1, 1, [3, 3, 32, 64], name='Conv2_1')
h2_2 = conv2d(h2_1, 1, 1, [5, 5, 64, 64], name='Conv2_2')
h2_3 = conv2d(h2_2, 1, 1, [7, 7, 64, 64], name='Conv2_3')
b2 = bn_layer(h2_3, is_training, name='bn2')
p2 = max_pooling(b2, 2, 2, 2, 2, name='MaxPool2')
d2 = dropout_layer(p2, keep_prob=keep_prob, name='Dropout2')

h3_1 = conv2d(d2, 1, 1, [3, 3, 64, 128], name='Conv3_1')
h3_2 = conv2d(h3_1, 1, 1, [5, 5, 128, 128], name='Conv3_2')
h3_3 = conv2d(h3_2, 1, 1, [7, 7, 128, 128], name='Conv3_3')
b3 = bn_layer(h3_3, is_training, name='bn3')
p3 = max_pooling(b3, 2, 2, 2, 2, name='MaxPool3')

flat_op = to_flat(p3, name='flat_op')
f1 = relu_layer(flat_op, 1024, name='FC_Relu')
d1 = dropout_layer(f1, keep_prob=keep_prob, name='Dropout3')
logits = linear(d1, NCLASS, name='FC_Linear')

with tf.variable_scope("Optimization"):
    hypothesis = tf.nn.softmax(logits, name='hypothesis')
    normal_loss = tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits_v2(logits=logits, labels=Y_one_hot),
                                name='loss')
    weight_decay_loss = tf.get_collection("weight_decay")
    loss = normal_loss + ALPHA*tf.reduce_sum(weight_decay_loss)
    optim = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(loss)

with tf.variable_scope("Prediction"):
    predict = tf.argmax(hypothesis, axis=1)

with tf.variable_scope("Accuracy"):
    accuracy = tf.reduce_sum(tf.cast(tf.equal(predict, tf.argmax(Y_one_hot, axis=1)), tf.float32))

with tf.variable_scope("Summary"):
    avg_train_loss = tf.placeholder(tf.float32)
    loss_train_avg = tf.summary.scalar('avg_train_loss', avg_train_loss)
    avg_train_acc = tf.placeholder(tf.float32)
    acc_train_avg = tf.summary.scalar('avg_train_acc', avg_train_acc)
    avg_validation_loss = tf.placeholder(tf.float32)
    loss_validation_avg = tf.summary.scalar('avg_validation_loss', avg_validation_loss)
    avg_validation_acc = tf.placeholder(tf.float32)
    acc_validation_avg = tf.summary.scalar('avg_validation_acc', avg_validation_acc)
    merged = tf.summary.merge_all()

init_op = tf.global_variables_initializer()
total_step = int(ntrain / BATCH_SIZE)
print("Total step : ", total_step)
with tf.Session() as sess:
    if os.path.exists(BOARD_PATH):
        shutil.rmtree(BOARD_PATH)
    writer = tf.summary.FileWriter(BOARD_PATH)
    writer.add_graph(sess.graph)

    sess.run(init_op)

    train_start_time = time.perf_counter()
    u = INIT_LEARNING_RATE
    for epoch in range(TOTAL_EPOCH):
        loss_per_epoch = 0
        acc_per_epoch = 0

        np.random.seed(epoch)
        mask = np.random.permutation(len(x_train))

        epoch_start_time = time.perf_counter()
        for step in range(total_step):
            s = BATCH_SIZE * step
            t = BATCH_SIZE * (step + 1)
            a, l, _ = sess.run([accuracy, loss, optim], feed_dict={X: x_train[mask[s:t], :], Y: y_train[mask[s:t], :],
                                                                   is_training:True,  keep_prob:0.7, learning_rate:u})
            loss_per_epoch += l
            acc_per_epoch += a
        epoch_end_time = time.perf_counter()
        epoch_duration = epoch_end_time - epoch_start_time
        loss_per_epoch /= total_step * BATCH_SIZE
        acc_per_epoch /= total_step * BATCH_SIZE

        va, vl = sess.run([accuracy, loss], feed_dict={X: x_validation, Y: y_validation, is_training:False,  keep_prob:1.0})
        epoch_valid_acc = va / len(x_validation)
        epoch_valid_loss = vl / len(x_validation)

        s = sess.run(merged, feed_dict={avg_train_loss: loss_per_epoch, avg_train_acc: acc_per_epoch,
                                        avg_validation_loss: epoch_valid_loss, avg_validation_acc: epoch_valid_acc})
        writer.add_summary(s, global_step=epoch)

        u = u*0.95
        if (epoch + 1) % 10 == 0:
            print("Epoch [{:2d}/{:2d}], train loss = {:.6f}, train accuracy = {:.2%}, "
                  "valid loss = {:.6f}, valid accuracy = {:.2%}, duration = {:.6f}(s)"
                  .format(epoch + 1, TOTAL_EPOCH, loss_per_epoch, acc_per_epoch, epoch_valid_loss, epoch_valid_acc,
                          epoch_duration))

    train_end_time = time.perf_counter()
    train_duration = train_end_time - train_start_time
    print("Duration for train : {:.6f}(s)".format(train_duration))
    print("<<< Train Finished >>>")

    ta = sess.run(accuracy, feed_dict={X: x_test, Y: y_test, is_training:False, keep_prob:1.0})
    print("Test Accraucy : {:.2%}".format(ta / ntest))

'''
GTX 1080
Epoch [10/100], train loss = 0.773211, train accuracy = 73.02%, valid loss = 0.715882, valid accuracy = 74.60%, duration = 18.041899(s)
Epoch [20/100], train loss = 0.511950, train accuracy = 81.68%, valid loss = 0.612546, valid accuracy = 78.90%, duration = 18.082348(s)
Epoch [30/100], train loss = 0.373265, train accuracy = 86.68%, valid loss = 0.616774, valid accuracy = 79.98%, duration = 18.154422(s)
Epoch [40/100], train loss = 0.292263, train accuracy = 89.56%, valid loss = 0.636738, valid accuracy = 80.48%, duration = 18.221083(s)
Epoch [50/100], train loss = 0.238034, train accuracy = 91.51%, valid loss = 0.664469, valid accuracy = 80.70%, duration = 18.282911(s)
Epoch [60/100], train loss = 0.216723, train accuracy = 92.23%, valid loss = 0.664509, valid accuracy = 80.68%, duration = 18.172769(s)
Epoch [70/100], train loss = 0.196578, train accuracy = 93.16%, valid loss = 0.667915, valid accuracy = 81.02%, duration = 18.209635(s)
Epoch [80/100], train loss = 0.189612, train accuracy = 93.21%, valid loss = 0.679422, valid accuracy = 80.90%, duration = 18.661657(s)
Epoch [90/100], train loss = 0.185632, train accuracy = 93.40%, valid loss = 0.684256, valid accuracy = 80.96%, duration = 18.216630(s)
Epoch [100/100], train loss = 0.180163, train accuracy = 93.73%, valid loss = 0.687451, valid accuracy = 80.96%, duration = 18.220751(s)
Duration for train : 1870.414942(s)
<<< Train Finished >>>
Test Accraucy : 80.62%
'''
