Job Dictionary
==============

A Job dictionary is maintained by each worker during execution of the codes list
(defined in the the configuration file. The purpose of the Job dictionary is to provide a mutable
object that user's can read from and write to if they are using preprocessing or postprocessing
functions to make modifications between simulations in the code list. The Job dictionary is also passed
to the objective function to provide information about the final state of the job.

The Job dictionary will always contain several pre-populated fields containing information about
the state of the job. These can be read from or even overwritten by the pre/postprocess functions.
However, in the latter case caution is advised as this can certainly break the rsopt run if not done properly.
Pre-populated fields are:

- `inputs`: This is a dictionary of parameters and settings for the job being run. This is populated
  for each job before preprocess is called. Because any inputs files are written after preprocess is called
  this allows users to make modifications or additions to the `inputs` dictionary. This is useful setting
  covariables in particular. An example of covariable setting is shown below:

  .. code-block:: python
   :linenos:
      # Before preprocess is called let the state of J, set by rsopt be:
      J = {'inputs':
              # Our simulation function has one variable 'x' that has been assigned a value already
              {'x': 5.0}
          }

  .. code-block:: python
   :linenos:

      def my_preprocess(J):
         # Let's say we want a linear relationship between the variable 'x' which is being set by
         #  rsopt directly and another input variable in the simulation 'y'. This can't be written
         #  into the rsopt configuration file but we can enforce it here. If we write a value for 'y'
         #  into J['inputs'] it will be passed to the simulation function.

         # Current value of x
         x = J['inputs']['x']
         # Set y based on a linear relationship with x
         y = 3 * x
         # Create an entry for y in the Job dictionary inputs field
         J['inputs']['y'] = y

         # No return value needs to be set for pre/postprocess functions

- `sim_status`: This is an integer code that is set after a simulation has finished that details whether the simulation
  finished successfully or not; or if something else happened. It is only available for use with postprocess functions
  and objective functions.
  This status is actually being set and used by the libEnsemble library that rsopt uses. For a list of statuses and
  their descriptions see calc_status_. This can be useful for instance to check if a Job failed to complete fully.
  The state can be checked in the objective function and used to invoke alternate calculation routines if a penalty
  function needs to be evaluated.

  .. code-block:: python
   :linenos:
   from libensemble import message_numbers
   import h5py
   import numpy as np

   """
   Suppose a simulation runs and produces an output file 'my_result.h5'. For the sake of this example we will
   assume that if the simulation finishes successfully this file will always contain fifty, positively valued entries
   and we want to minimize the total of these numbers.
   If the simulation does not complete then some of these will be missing and we will need to account for this when
   writing the objective function.
   """


   def my_objective(J):
       MAX_ENTRIES = 50
       ENTRY_PENALTY_VALUE = 100.0
       if J['sim_status'] == message_numbers.WORKER_DONE:
           # Job finished successfully - assume all entries are present - normal evaluation
           result_file = h5py.File('my_result.h5', 'r')
           result = np.sum(result_file['x'][()])

           return result
       elif J['sim_status'] == message_numbers.TASK_FAILED:
           # Some number of entries will be missing
           # Find out how many and replace their value with ENTRY_PENALTY_VALUE
           result_file = h5py.File('my_result.h5', 'r')
           missing_count = MAX_ENTRIES - result_file['x'].size
           result = np.sum(result_file['x'][()]) + missing_count * ENTRY_PENALTY_VALUE

           return result
       else:
           # Maybe some unknown failure state can occur. Perhaps you would just want to return
           # the max penalty in this case
           return MAX_ENTRIES * ENTRY_PENALTY_VALUE

.. _calc_status: https://libensemble.readthedocs.io/en/main/data_structures/calc_status.html