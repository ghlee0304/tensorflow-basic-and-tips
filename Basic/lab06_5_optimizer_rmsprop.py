import tensorflow as tf
import numpy as np
import os
import shutil
import load_data
import time

x_train, x_validation, x_test, y_train, y_validation, y_test \
    = load_data.load_mnist('./data/mnist/', seed = 0, as_image = False, scaling = True)

BOARD_PATH = "./board/lab06-5_board"
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

def relu_layer(x, output_dim, name):
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

h1 = relu_layer(X, 256, 'Relu_Layer1')
h2 = relu_layer(h1, 128, 'Relu_Layer2')
h3 = relu_layer(h2, 64, 'Relu_Layer3')
logits = linear(h1, NCLASS, 'Linear_Layer')

with tf.variable_scope("Optimization"):
    hypothesis = tf.nn.softmax(logits, name = 'hypothesis')
    loss = tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits_v2(logits = logits, labels = Y_one_hot), name = 'loss')
    optim = tf.train.RMSPropOptimizer(learning_rate = 0.001).minimize(loss)

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

        epoch_start_time = time.perf_counter()
        for step in range(total_step):
            s = BATCH_SIZE*step
            t = BATCH_SIZE*(step+1)
            a, l, _ = sess.run([accuracy, loss, optim], feed_dict={X: x_train[mask[s:t],:], Y: y_train[mask[s:t],:]})
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
Epoch [ 1/20], train loss = 0.563685, train accuracy = 86.78%, valid loss = 0.384064, valid accuracy = 90.23%, duration = 1.787810(s)
Epoch [ 2/20], train loss = 0.365157, train accuracy = 90.41%, valid loss = 0.330808, valid accuracy = 91.38%, duration = 1.682016(s)
Epoch [ 3/20], train loss = 0.328561, train accuracy = 91.18%, valid loss = 0.304377, valid accuracy = 91.87%, duration = 2.188488(s)
Epoch [ 4/20], train loss = 0.307721, train accuracy = 91.66%, valid loss = 0.288482, valid accuracy = 92.25%, duration = 1.841162(s)
Epoch [ 5/20], train loss = 0.293378, train accuracy = 92.04%, valid loss = 0.276325, valid accuracy = 92.47%, duration = 1.780760(s)
Epoch [ 6/20], train loss = 0.282379, train accuracy = 92.33%, valid loss = 0.266869, valid accuracy = 92.73%, duration = 2.205451(s)
Epoch [ 7/20], train loss = 0.273220, train accuracy = 92.58%, valid loss = 0.259309, valid accuracy = 92.87%, duration = 1.812191(s)
Epoch [ 8/20], train loss = 0.265698, train accuracy = 92.80%, valid loss = 0.252731, valid accuracy = 93.15%, duration = 2.037798(s)
Epoch [ 9/20], train loss = 0.259177, train accuracy = 92.97%, valid loss = 0.247415, valid accuracy = 93.37%, duration = 2.186624(s)
Epoch [10/20], train loss = 0.253396, train accuracy = 93.11%, valid loss = 0.242277, valid accuracy = 93.48%, duration = 1.902952(s)
Epoch [11/20], train loss = 0.248362, train accuracy = 93.20%, valid loss = 0.237531, valid accuracy = 93.60%, duration = 2.205857(s)
Epoch [12/20], train loss = 0.243651, train accuracy = 93.37%, valid loss = 0.233492, valid accuracy = 93.73%, duration = 1.751091(s)
Epoch [13/20], train loss = 0.239280, train accuracy = 93.46%, valid loss = 0.229979, valid accuracy = 93.90%, duration = 1.738757(s)
Epoch [14/20], train loss = 0.235467, train accuracy = 93.61%, valid loss = 0.226459, valid accuracy = 94.00%, duration = 1.633035(s)
Epoch [15/20], train loss = 0.231842, train accuracy = 93.67%, valid loss = 0.223543, valid accuracy = 94.13%, duration = 1.579683(s)
Epoch [16/20], train loss = 0.228481, train accuracy = 93.76%, valid loss = 0.220320, valid accuracy = 94.17%, duration = 1.719937(s)
Epoch [17/20], train loss = 0.225198, train accuracy = 93.86%, valid loss = 0.217533, valid accuracy = 94.10%, duration = 1.598012(s)
Epoch [18/20], train loss = 0.222280, train accuracy = 93.97%, valid loss = 0.214656, valid accuracy = 94.20%, duration = 1.656361(s)
Epoch [19/20], train loss = 0.219544, train accuracy = 94.02%, valid loss = 0.212322, valid accuracy = 94.23%, duration = 1.745925(s)
Epoch [20/20], train loss = 0.216812, train accuracy = 94.11%, valid loss = 0.209934, valid accuracy = 94.28%, duration = 1.706980(s)
Duration for train : 37.316786(s)
<<< Train Finished >>>
Test Accraucy : 94.05%
'''
