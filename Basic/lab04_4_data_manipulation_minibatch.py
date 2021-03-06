import tensorflow as tf
import numpy as np
import os
import shutil

############################################################################
#load_data.py
def MinMaxScaler(cur_col):
    numerator = cur_col - np.min(cur_col, 0)
    denominator = np.max(cur_col, 0) - np.min(cur_col, 0)
    return numerator / (denominator + 1e-7), np.min(cur_col, 0), np.max(cur_col, 0)

def MinMaxScaler_with(cur_col, min_col, max_col):
    numerator = cur_col - min_col
    denominator = max_col - min_col
    return numerator / (denominator + 1e-7)

SEED = 0
pendigits_train = np.loadtxt('./data/pendigits_train.csv', delimiter = ',')
pendigits_test = np.loadtxt('./data/pendigits_test.csv', delimiter = ',')

pendigits_data = np.append(pendigits_train, pendigits_test, axis = 0)
nsamples = np.size(pendigits_data, 0)

np.random.seed(SEED)
mask = np.random.permutation(nsamples)
pendigits_data = pendigits_data[mask]

x_data = pendigits_data[:,:-1]
y_data = pendigits_data[:,[-1]].astype(int)

ndim = np.size(x_data, 1)

ntrain = int(nsamples*0.7)
nvalidation = int(nsamples*0.1)
ntest = nsamples-ntrain-nvalidation

x_train = x_data[:ntrain]
x_validation = x_data[ntrain:(ntrain+nvalidation)]
x_test = x_data[-ntest:]

x_train, train_min_col, train_max_col = MinMaxScaler(x_train)
x_validation = MinMaxScaler_with(x_validation, train_min_col, train_max_col)
x_test = MinMaxScaler_with(x_test, train_min_col, train_max_col)

y_train = y_data[:ntrain]
y_validation = y_data[ntrain:(ntrain+nvalidation)]
y_test = y_data[-ntest:]

############################################################################

BOARD_PATH = "./board/lab04-4_board"
NSAMPLES = nsamples
INPUT_DIM = ndim
NCLASS = len(np.unique(y_data))
BATCH_SIZE = 32

TOTAL_EPOCH = 1000

print("The number of data samples : ", NSAMPLES)
print("The dimension of data samples : ", INPUT_DIM)

def linear(x, output_dim, name):
    with tf.variable_scope(name):
        W = tf.get_variable(name='W', shape=[x.get_shape()[-1], output_dim], dtype=tf.float32,
                            initializer=tf.truncated_normal_initializer())
        b = tf.get_variable(name = 'b', shape = [output_dim], dtype = tf.float32, initializer= tf.constant_initializer(0.0))
        h = tf.nn.bias_add(tf.matmul(x, W), b, name = 'h')
        return h

def sigmoid_layer(x, output_dim, name):
    with tf.variable_scope(name):
        W = tf.get_variable(name='W', shape=[x.get_shape()[-1], output_dim], dtype=tf.float32,
                            initializer=tf.truncated_normal_initializer())
        b = tf.get_variable(name = 'b', shape = [output_dim], dtype = tf.float32, initializer= tf.constant_initializer(0.0))
        h = tf.nn.sigmoid(tf.nn.bias_add(tf.matmul(x, W), b), name = 'h')
        return h

tf.set_random_seed(0)

with tf.variable_scope("Inputs"):
    X = tf.placeholder(shape = [None, INPUT_DIM], dtype = tf.float32, name = 'X')
    Y = tf.placeholder(shape = [None, 1], dtype = tf.int32, name = 'Y')
    Y_one_hot = tf.reshape(tf.one_hot(Y, NCLASS), [-1, NCLASS], name = 'Y_one_hot')

h1 = sigmoid_layer(X, 8, 'FC_Layer1')
h2 = sigmoid_layer(h1, 10, 'FC_Layer2')
logits = linear(h2, NCLASS, 'FC_Layer3')

with tf.variable_scope("Optimization"):
    hypothesis = tf.nn.softmax(logits, name = 'hypothesis')
    loss = -tf.reduce_sum(Y_one_hot*tf.log(hypothesis), name = 'loss')
    optim = tf.train.GradientDescentOptimizer(learning_rate = 0.001).minimize(loss)

with tf.variable_scope("Pred_and_Acc"):
    predict = tf.argmax(hypothesis, axis=1)
    accuracy = tf.reduce_sum(tf.cast(tf.equal(predict, tf.argmax(Y_one_hot, axis = 1)), tf.float32))

with tf.variable_scope("Summary"):
    avg_loss = tf.placeholder(tf.float32)
    loss_avg  = tf.summary.scalar('avg_loss', avg_loss)
    avg_acc = tf.placeholder(tf.float32)
    acc_avg = tf.summary.scalar('avg_acc', avg_acc)
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
    for epoch in range(TOTAL_EPOCH):
        loss_per_epoch = 0
        acc_per_epoch = 0
        np.random.seed(epoch)
        mask = np.random.permutation(len(x_train))
        for step in range(total_step):
            s = BATCH_SIZE*step
            t = BATCH_SIZE*(step+1)
            a, l, _ = sess.run([accuracy, loss, optim], feed_dict={X: x_train[mask[s:t],:], Y: y_train[mask[s:t],:]})
            loss_per_epoch += l
            acc_per_epoch += a

        loss_per_epoch /= total_step * BATCH_SIZE
        acc_per_epoch /= total_step * BATCH_SIZE

        s = sess.run(merged, feed_dict = {avg_loss:loss_per_epoch, avg_acc:acc_per_epoch})
        writer.add_summary(s, global_step = epoch)

        va, vl = sess.run([accuracy, loss], feed_dict={X: x_validation, Y: y_validation})
        epoch_valid_acc = va / len(x_validation)
        epoch_valid_loss = vl / len(x_validation)

        if (epoch+1) %100 == 0:
            print("Epoch [{:2d}/{:2d}], train loss = {:.6f}, train accuracy = {:.2%}, valid loss = {:.6f}, valid accuracy = {:.2%}"
                  .format(epoch + 1, TOTAL_EPOCH, loss_per_epoch, acc_per_epoch, epoch_valid_loss, epoch_valid_acc))

'''
Total step :  240
Epoch [100/1000], train loss = 0.277490, train accuracy = 92.67%, valid loss = 0.244109, valid accuracy = 94.63%
Epoch [200/1000], train loss = 0.170967, train accuracy = 95.36%, valid loss = 0.155349, valid accuracy = 96.00%
Epoch [300/1000], train loss = 0.131892, train accuracy = 96.32%, valid loss = 0.129110, valid accuracy = 96.45%
Epoch [400/1000], train loss = 0.109945, train accuracy = 96.91%, valid loss = 0.115636, valid accuracy = 96.72%
Epoch [500/1000], train loss = 0.095863, train accuracy = 97.28%, valid loss = 0.105041, valid accuracy = 97.36%
Epoch [600/1000], train loss = 0.085958, train accuracy = 97.55%, valid loss = 0.100272, valid accuracy = 97.45%
Epoch [700/1000], train loss = 0.078748, train accuracy = 97.77%, valid loss = 0.094253, valid accuracy = 97.27%
Epoch [800/1000], train loss = 0.072572, train accuracy = 97.90%, valid loss = 0.090324, valid accuracy = 97.54%
Epoch [900/1000], train loss = 0.067901, train accuracy = 98.03%, valid loss = 0.087233, valid accuracy = 97.82%
Epoch [1000/1000], train loss = 0.062622, train accuracy = 98.14%, valid loss = 0.084490, valid accuracy = 98.00%
'''
