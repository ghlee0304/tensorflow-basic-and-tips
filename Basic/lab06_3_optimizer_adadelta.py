import tensorflow as tf
import numpy as np
import os
import shutil
import load_data
import time

x_train, x_validation, x_test, y_train, y_validation, y_test \
    = load_data.load_mnist('./data/mnist/', seed = 0, as_image = False, scaling = True)

BOARD_PATH = "./board/lab06-3_board"
INPUT_DIM = np.size(x_train, 1)
NCLASS = len(np.unique(y_train))
BATCH_SIZE = 32

TOTAL_EPOCH = 20

ntrain = len(x_train)
nvalidation = len(x_validation)
ntest = len(x_test)

print("The number of train samples : ", ntrain)
print("The number of validation samples : ", nvalidation)
print("The number of test samples : ", ntest)

def linear(x, output_dim, name):
    with tf.variable_scope(name):
        W = tf.get_variable(name='W', shape=[x.get_shape()[-1], output_dim], dtype=tf.float32,
                            initializer=tf.glorot_uniform_initializer())
        b = tf.get_variable(name = 'b', shape = [output_dim], dtype = tf.float32, initializer= tf.constant_initializer(0.0))
        h = tf.nn.bias_add(tf.matmul(x, W), b, name = 'h')
        return h

def relu_linear(x, output_dim, name):
    with tf.variable_scope(name):
        W = tf.get_variable(name='W', shape=[x.get_shape()[-1], output_dim], dtype=tf.float32,
                            initializer=tf.glorot_uniform_initializer())
        b = tf.get_variable(name = 'b', shape = [output_dim], dtype = tf.float32, initializer= tf.constant_initializer(0.0))
        h = tf.nn.relu(tf.nn.bias_add(tf.matmul(x, W), b), name = 'h')
        return h

tf.set_random_seed(0)

with tf.variable_scope("Inputs"):
    X = tf.placeholder(shape = [None, INPUT_DIM], dtype = tf.float32, name = 'X')
    Y = tf.placeholder(shape = [None, 1], dtype = tf.int32, name = 'Y')
    Y_one_hot = tf.reshape(tf.one_hot(Y, NCLASS), [-1, NCLASS], name = 'Y_one_hot')

h1 = relu_linear(X, 256, 'Relu_Layer1')
h2 = relu_linear(h1, 128, 'Relu_Layer2')
h3 = relu_linear(h2, 64, 'Relu_Layer3')
logits = linear(h1, NCLASS, 'Linear_Layer')

with tf.variable_scope("Optimization"):
    hypothesis = tf.nn.softmax(logits, name = 'hypothesis')
    loss = tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits_v2(logits = logits, labels = Y_one_hot), name = 'loss')
    optim = tf.train.AdadeltaOptimizer(learning_rate = 0.001).minimize(loss)

with tf.variable_scope("Pred_and_Acc"):
    predict = tf.argmax(hypothesis, axis=1)
    accuracy = tf.reduce_sum(tf.cast(tf.equal(predict, tf.argmax(Y_one_hot, axis = 1)), tf.float32))

with tf.variable_scope("Summary"):
    avg_train_loss = tf.placeholder(tf.float32)
    loss_train_avg  = tf.summary.scalar('avg_train_loss', avg_train_loss)
    avg_train_acc = tf.placeholder(tf.float32)
    acc_train_avg = tf.summary.scalar('avg_train_acc', avg_train_acc)
    avg_validation_loss = tf.placeholder(tf.float32)
    loss_validation_avg = tf.summary.scalar('avg_validation_loss', avg_validation_loss)
    avg_validation_acc = tf.placeholder(tf.float32)
    acc_validation_avg = tf.summary.scalar('avg_validation_acc', avg_validation_acc)
    merged = tf.summary.merge_all()

init_op = tf.global_variables_initializer()
total_step = int(ntrain/BATCH_SIZE)
print("Total step : ", total_step)
with tf.Session() as sess:
    if os.path.exists(BOARD_PATH):
        shutil.rmtree(BOARD_PATH)
    writer = tf.summary.FileWriter(BOARD_PATH)
    writer.add_graph(sess.graph)

    sess.run(init_op)

    train_start_time = time.perf_counter()
    for epoch in range(TOTAL_EPOCH):
        loss_per_epoch = 0
        acc_per_epoch = 0

        np.random.seed(epoch)
        mask = np.random.permutation(len(x_train))
        x_trian = x_train[mask]
        epoch_start_time = time.perf_counter()
        for step in range(total_step):
            s = BATCH_SIZE*step
            t = BATCH_SIZE*(step+1)
            a, l, _ = sess.run([accuracy, loss, optim], feed_dict={X: x_train[s:t,:], Y: y_train[s:t,:]})
            loss_per_epoch += l
            acc_per_epoch += a
        epoch_end_time = time.perf_counter()
        epoch_duration = epoch_end_time - epoch_start_time
        loss_per_epoch /= total_step*BATCH_SIZE
        acc_per_epoch /= total_step*BATCH_SIZE

        va, vl = sess.run([accuracy, loss], feed_dict={X: x_validation, Y: y_validation})
        epoch_valid_acc = va / len(x_validation)
        epoch_valid_loss = vl / len(x_validation)

        s = sess.run(merged, feed_dict = {avg_train_loss:loss_per_epoch, avg_train_acc:acc_per_epoch,
                                          avg_validation_loss:epoch_valid_loss, avg_validation_acc:epoch_valid_acc})
        writer.add_summary(s, global_step = epoch)

        if (epoch+1) % 1 == 0:

            print("Epoch [{:2d}/{:2d}], train loss = {:.6f}, train accuracy = {:.2%}, "
                  "valid loss = {:.6f}, valid accuracy = {:.2%}, duration = {:.6f}(s)"
                  .format(epoch + 1, TOTAL_EPOCH, loss_per_epoch, acc_per_epoch, epoch_valid_loss, epoch_valid_acc, epoch_duration))

    train_end_time = time.perf_counter()
    train_duration = train_end_time - train_start_time
    print("Duration for train : {:.6f}(s)".format(train_duration))
    print("<<< Train Finished >>>")

    ta = sess.run(accuracy, feed_dict = {X:x_test, Y:y_test})
    print("Test Accraucy : {:.2%}".format(ta/ntest))

'''
Epoch [ 1/20], train loss = 2.297358, train accuracy = 9.82%, valid loss = 2.250826, valid accuracy = 11.00%, duration = 2.395474(s)
Epoch [ 2/20], train loss = 2.215116, train accuracy = 13.16%, valid loss = 2.171822, valid accuracy = 16.13%, duration = 2.015403(s)
Epoch [ 3/20], train loss = 2.139085, train accuracy = 19.90%, valid loss = 2.097708, valid accuracy = 24.25%, duration = 1.745262(s)
Epoch [ 4/20], train loss = 2.067311, train accuracy = 29.27%, valid loss = 2.027229, valid accuracy = 35.13%, duration = 1.949739(s)
Epoch [ 5/20], train loss = 1.998821, train accuracy = 39.41%, valid loss = 1.959642, valid accuracy = 46.03%, duration = 1.750276(s)
Epoch [ 6/20], train loss = 1.932958, train accuracy = 48.32%, valid loss = 1.894427, valid accuracy = 52.93%, duration = 2.199621(s)
Epoch [ 7/20], train loss = 1.869283, train accuracy = 55.20%, valid loss = 1.831221, valid accuracy = 58.77%, duration = 1.795437(s)
Epoch [ 8/20], train loss = 1.807559, train accuracy = 60.54%, valid loss = 1.769910, valid accuracy = 63.72%, duration = 1.938959(s)
Epoch [ 9/20], train loss = 1.747634, train accuracy = 64.37%, valid loss = 1.710397, valid accuracy = 66.65%, duration = 2.102093(s)
Epoch [10/20], train loss = 1.689434, train accuracy = 67.08%, valid loss = 1.652650, valid accuracy = 68.85%, duration = 2.618851(s)
Epoch [11/20], train loss = 1.632933, train accuracy = 69.16%, valid loss = 1.596608, valid accuracy = 70.88%, duration = 2.202858(s)
Epoch [12/20], train loss = 1.578135, train accuracy = 70.85%, valid loss = 1.542245, valid accuracy = 72.45%, duration = 1.725262(s)
Epoch [13/20], train loss = 1.525077, train accuracy = 72.24%, valid loss = 1.489655, valid accuracy = 73.77%, duration = 1.932959(s)
Epoch [14/20], train loss = 1.473800, train accuracy = 73.51%, valid loss = 1.438926, valid accuracy = 75.03%, duration = 1.734269(s)
Epoch [15/20], train loss = 1.424352, train accuracy = 74.61%, valid loss = 1.390085, valid accuracy = 76.02%, duration = 1.941095(s)
Epoch [16/20], train loss = 1.376781, train accuracy = 75.53%, valid loss = 1.343193, valid accuracy = 76.98%, duration = 1.804475(s)
Epoch [17/20], train loss = 1.331129, train accuracy = 76.40%, valid loss = 1.298278, valid accuracy = 77.77%, duration = 1.876606(s)
Epoch [18/20], train loss = 1.287445, train accuracy = 77.15%, valid loss = 1.255377, valid accuracy = 78.42%, duration = 1.976176(s)
Epoch [19/20], train loss = 1.245749, train accuracy = 77.79%, valid loss = 1.214485, valid accuracy = 78.80%, duration = 1.670540(s)
Epoch [20/20], train loss = 1.206047, train accuracy = 78.41%, valid loss = 1.175621, valid accuracy = 79.33%, duration = 1.898023(s)
Duration for train : 42.068840(s)
<<< Train Finished >>>
Test Accraucy : 79.99%
'''