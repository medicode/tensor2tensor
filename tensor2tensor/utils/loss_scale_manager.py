# Copyright 2018 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Distributed LossScaleManager classes for mixed precision training."""

import tensorflow as tf
from tensorflow.contrib.mixed_precision import ExponentialUpdateLossScaleManager
from tensorflow.python.framework import dtypes, ops
from tensorflow.python.ops import variable_scope


class FathomDistributedExponentialUpdateLossScaleManager(ExponentialUpdateLossScaleManager):
  """ 
  This class is necessary because the base LossScaleManager doesn't suport
    distribution strategies, and there are no plans to fix that.
    See https://github.com/tensorflow/tensorflow/issues/25080
  """

  def __init__(self,
               init_loss_scale,
               incr_every_n_steps,
               decr_every_n_nan_or_inf=2,
               incr_ratio=2,
               decr_ratio=0.8):
    """Constructor of distribution strategy exp-update loss scale manager.

    Args:
      init_loss_scale: A Python float.  The loss scale to use at the beginning.
      incr_every_n_steps: Increases loss scale every n consecutive steps with
        finite gradients.
      decr_every_n_nan_or_inf: Decreases loss scale every n accumulated steps
        with nan or inf gradients.
      incr_ratio: The multiplier to use when increasing the loss scale.
      decr_ratio: The less-than-one-multiplier to use when decreasing the loss
        scale.
    """
    self._incr_every_n_steps = incr_every_n_steps
    self._decr_every_n_nan_or_inf = decr_every_n_nan_or_inf
    self._incr_ratio = incr_ratio
    self._decr_ratio = decr_ratio
    agg_type = tf.VariableAggregation.ONLY_FIRST_TOWER #Fathom
    synch_type = variable_scope.VariableSynchronization.ON_READ #Fathom
    print("Agg type is {}".format(agg_type)) #Fathom
    print("synch type is {}".format(synch_type)) #Fathom
    self._loss_scale = variable_scope.variable(
        name="loss_scale",
        initial_value=ops.convert_to_tensor(init_loss_scale, dtypes.float32),
        dtype=dtypes.float32,
        synchronization=synch_type,
        trainable=False, aggregation=agg_type) #Fathom
    self._num_good_steps = variable_scope.variable(
        name="good_steps",
        initial_value=0,
        dtype=dtypes.int32,
        trainable=False,
        synchronization=synch_type,
        aggregation=agg_type) #Fathom
    self._num_bad_steps = variable_scope.variable(
        name="bad_steps",
        initial_value=0,
        dtype=dtypes.int32,
        trainable=False,
        synchronization=synch_type,
        aggregation=agg_type) #Fathom
