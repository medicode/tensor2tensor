"""A mixed precision LossScaleManager with Distribution Strategy support
    added by Fathom."""

import tensorflow as tf
from tensorflow.contrib.mixed_precision import ExponentialUpdateLossScaleManager
from tensorflow.python.framework import dtypes, ops
from tensorflow.python.ops import variable_scope
from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops import gen_control_flow_ops
from tensorflow.python.ops import gen_math_ops
from tensorflow.python.ops import state_ops
from tensorflow.python.ops import variable_scope


class FathomDistributedExponentialUpdateLossScaleManager(
    ExponentialUpdateLossScaleManager):
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
    #Fathom | For dist strat
    agg_type = tf.VariableAggregation.ONLY_FIRST_TOWER

    print("Agg type is {}".format(agg_type))
    self._loss_scale = variable_scope.variable(
        name="loss_scale",
        initial_value=ops.convert_to_tensor(init_loss_scale, dtypes.float32),
        dtype=dtypes.float32,
        trainable=False, aggregation=agg_type)
    self._num_good_steps = variable_scope.variable(
        name="good_steps",
        initial_value=0,
        dtype=dtypes.int32,
        trainable=False,
        aggregation=agg_type)
    self._num_bad_steps = variable_scope.variable(
        name="bad_steps",
        initial_value=0,
        dtype=dtypes.int32,
        trainable=False,
        aggregation=agg_type)

  def update_loss_scale(self, finite_grads):
    """Updates loss scale based on if gradients are finite in current step."""
    #TODO: Fix
    next_step = self._num_good_steps + 1
    # self._loss_scale = tf.cond(finite_grads, )
    new_loss_scale = control_flow_ops.cond(
        gen_math_ops.is_finite(self._loss_scale * self._incr_ratio),
        lambda: self._loss_scale * self._incr_ratio,
        lambda: self._loss_scale)
    # Incr loss scale

    next_step_bigger = next_step >= self._incr_every_n_steps
    next_step_and_finite = tf.math.logical_and(finite_grads, next_step_bigger)
    self._num_good_steps = tf.cond(next_step_bigger, lambda: self._num_good_steps, lambda: self._num_good_steps + 1)
    self._loss_scale = tf.cond(next_step_and_finite, lambda: new_loss_scale, lambda: self._loss_scale)
    self._num_good_steps = tf.cond(next_step_and_finite, lambda: 0, lambda: self._num_good_steps)
    self._num_bad_steps = tf.cond(next_step_and_finite, lambda: 0, lambda: self._num_bad_steps)
    #next_step >= self._incr_every_n_steps
    # Incr the loss scale
    # Else, 
    # If all grads are finite
    
    # Do below if above is good
    
    # def update_if_not_finite_grads():
    #   """Branch function when any grad is not finite."""

    #   def decr_loss_scale():
    #     update_op = state_ops.assign(
    #         self._loss_scale,
    #         gen_math_ops.maximum(1., self._loss_scale * self._decr_ratio))
    #     # When loss_scale is updated, both good and bad steps are reset.
    #     return control_flow_ops.group(update_op, self._reset_stats())

    #   def just_update_steps():
    #     # When bad_steps is incremented, good_step is reset.
    #     return control_flow_ops.group(
    #         state_ops.assign_add(self._num_bad_steps, 1),
    #         state_ops.assign(self._num_good_steps, 0))

    #   return control_flow_ops.cond(
    #       next_step >= self._decr_every_n_nan_or_inf,
    #       decr_loss_scale, just_update_steps)
    return 
    # return control_flow_ops.cond(finite_grads, update_if_finite_grads,
                                #  update_if_not_finite_grads)
