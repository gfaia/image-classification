"""The basic multilayer perceptron with three hidden layers.
  Accuracy: 98.2%
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
sys.path.append('..')

import os
import time
import argparse
from tqdm import tqdm
import tensorflow as tf
import helper
import numpy as np


def fully_connected_layer(inputs, in_size, out_size, dropout=None, name='fl'):
  """Fully connected layer.
  
  Args:
    inputs: inputs, 1D tensor
    in_size, the size of input feature
    out_size, the size of out feature
    dropout, the ratio of dropout
    name, the name of layer
  """
  with tf.name_scope(name):
    W = tf.Variable(tf.truncated_normal(shape=[in_size, out_size], mean=0, stddev=0.1, name='W'))
    b = tf.Variable(tf.constant(shape=[out_size], value=0.1, name='bias'))
    outputs = tf.nn.relu(tf.matmul(inputs, W) + b)
    
    if dropout is None:
      outputs = tf.nn.dropout(outputs, dropout)

  return outputs


class MLP(object):

  def __init__(self, input_size, num_classes, init_lr, decay_steps, decay_rate, weight_decay):
    
    self.input_size = input_size
    self.num_classes = num_classes
    self.weight_decay = weight_decay
    self.inputs = tf.placeholder(tf.float32, [None, self.input_size], name='inputs')
    self.labels = tf.placeholder(tf.int64, [None], name='labels')
    self.dropout = tf.placeholder(tf.float32, name="dropout")

    self.global_step = tf.Variable(0, trainable=False)
    self.add_global = self.global_step.assign_add(1)
    self.learning_rate = tf.train.exponential_decay(init_lr, global_step=self.global_step, 
                                                    decay_steps=decay_steps, decay_rate=decay_rate)

    self.model(), self.loss_acc(), self.train_op()

  def model(self):

    outputs = fully_connected_layer(self.inputs, self.input_size, 392, self.dropout, 'fl1')
    outputs = fully_connected_layer(outputs, 392, 196, self.dropout, 'fl2')
    outputs = fully_connected_layer(outputs, 196, 98, self.dropout, 'fl3')

    with tf.name_scope('inference'):
      W = tf.Variable(tf.truncated_normal(shape=[98, self.num_classes], 
                       mean=0, stddev=0.1, name='W'))
      b = tf.Variable(tf.constant(shape=[self.num_classes], value=0.1, name='bias'))
      self.logits = tf.matmul(outputs, W) + b

  def loss_acc(self):
    """The loss and accuracy of model."""
    with tf.name_scope("loss"):
      losses = tf.losses.sparse_softmax_cross_entropy(labels=self.labels, logits=self.logits)
      self.loss = tf.add(tf.reduce_mean(losses), self.weight_decay * tf.add_n([tf.nn.l2_loss(v) 
                         for v in tf.trainable_variables() if 'bias' not in v.name]))

    with tf.name_scope("accuracy"):
      correct_prediction = tf.equal(tf.argmax(self.logits, 1), self.labels)
      self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

  def train_op(self):
    """The train operation."""
    self.optimization = tf.train.AdamOptimizer(self.learning_rate).minimize(self.loss)


def main(unused_argv):
  
  train_data, train_labels, test_data, test_labels = helper.mnist_data_loader()  

  model = MLP(
    input_size=FLAGS.input_size, num_classes=FLAGS.num_classes, 
    init_lr=FLAGS.learning_rate, decay_steps=FLAGS.decay_steps, 
    decay_rate=FLAGS.decay_rate, weight_decay=FLAGS.weight_decay
    )

  sess = tf.InteractiveSession()
  tf.global_variables_initializer().run()

  for e in range(FLAGS.epochs):
    print("----- Epoch {}/{} -----".format(e + 1, FLAGS.epochs))
    # training stage. 
    train_batches = helper.generate_batches(train_data, train_labels, FLAGS.batch_size)
    for xt, yt in tqdm(train_batches, desc="Training"):
      _, i = sess.run([model.optimization, model.add_global], 
                      feed_dict={ model.inputs: xt, model.labels: yt, 
                                  model.dropout: FLAGS.dropout})
    # testing stage.
    test_batches = helper.generate_batches(test_data, test_labels, FLAGS.batch_size)
    acc_list, loss_list = [], []
    for xd, yd in tqdm(test_batches, desc="Testing"):
      acc, loss, lr = sess.run([model.accuracy, model.loss, model.learning_rate], 
                               feed_dict={ model.inputs: xd, model.labels: yd,
                                           model.dropout: 1})
      acc_list.append(acc)
      loss_list.append(loss)
    acc, loss = np.mean(acc_list), np.mean(loss_list)

    current = time.asctime(time.localtime(time.time()))
    print("""{0} Step {1:5} Learning rate: {2:.6f} Losss: {3:.4f} Accuracy: {4:.4f}"""
          .format(current, i, lr, loss, acc))

  # Save the model
  saver = tf.train.Saver()
  model_path = saver.save(sess, FLAGS.save_path)
  print("Model saved in file: %s" % model_path)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--epochs', type=int, default=10,
                      help='Number of epochs to run trainer.')
  parser.add_argument('--learning_rate', type=float, default=0.001, 
                      help='Initial learning rate.')
  parser.add_argument('--decay_steps', type=int, default=5000, 
                      help='The period of decay.')
  parser.add_argument('--decay_rate', type=float, default=0.65, 
                      help='The rate of decay.')
  parser.add_argument('--weight_decay', type=float, default=2e-6,
                      help='The rate of weight decay.')
  parser.add_argument('--batch_size', type=int, default=128, 
                      help='The size of batch.')
  parser.add_argument('--input_size', type=int, default=784,
                      help='The size of input.')
  parser.add_argument('--num_classes', type=int, default=10,
                      help='The number of classes.')
  parser.add_argument('--dropout', type=float, default=0.5, 
                      help='Keep probability for training dropout.')
  parser.add_argument('--save_path', type=str,  
                      default='models/mnist_multi.ckpt')
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run()
