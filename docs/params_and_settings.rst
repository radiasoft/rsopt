.. _params_and_settings:

Parameters and Settings
=======================

Within the ``codes`` block of the configuration, each code can have optional fields to define ``settings`` and ``parameters``. These fields allow users to specify how values are passed to the code during execution.

Settings
--------

The ``settings`` field contains a dictionary of names and values that are passed to the code at each execution. Settings are static; their values remain unchanged throughout the rsopt run. Each key in the ``settings`` dictionary corresponds to a single value.

Example::

    codes:
        - python:
            settings:
                # Settings are optional. Each key should correspond to a single value.
                a: 42.
                b: 21
                c: false

Setting names are interpreted the same way as parameter names; see :ref:`naming`.

Settings Class Definition
-------------------------

.. automodule:: rsopt.configuration.schemas.settings
   :members: Setting

Parameters
----------

The ``parameters`` field specifies names and values that are passed to the optimizer. Unlike settings, parameter values are changed by the optimizer at each execution of the code.

Example::

    codes:
        - python:
            parameters:
                # All parameters must have subfields of min, max, start
                x:
                    min: 1.
                    max: 3.
                    start: 2.
                y:
                    min: 400
                    max: 1000
                    start: 500
        - elegant:
            parameters:
                m:
                    min: 8
                    max: 20
                    start: 12

Parameter Requirements
----------------------

Numeric parameters typically require the fields:

* ``min``: The minimum allowed value for the parameter.
* ``max``: The maximum allowed value for the parameter.
* ``start``: The initial value of the parameter.

These fields must always be provided in the configuration, although their usage may vary depending on the chosen ``software`` (specified in ``options``) and other run parameters. For example, in a single-step run, the code will execute once using the ``start`` values.

Parameter Types
---------------

rsopt supports several types of parameters, each with specific attributes:

* **NumericParameter:** Represents a single numerical parameter with ``min``, ``max``, and ``start`` values. It can also include ``samples`` and ``scale`` to control sampling.
* **Vector Parameters:** For specifying a vector of parameters with the same bounds and starting values for each dimension, use the following syntax. This is shorthand for defining multiple `NumericParameter` instances::

    codes:
        - elegant:
            parameters:
                # vector parameter example
                vector_param:
                    dimension: 4
                    min: 0
                    max: 10
                    start: 5

* **CategoryParameter:** Represents a parameter that can take on values from a predefined list.

.. _naming:

Naming Parameters and Settings
------------------------------

How a parameter or setting name is interpreted depends on the code it belongs to.

**python** and **user** (and **flash**) pass names through unchanged. Any name is accepted, including names
with any number of ``.`` characters (e.g. ``model.solver.tol``); how the name is used is up to your own code.

**elegant**, **opal**, **madx**, and **spiffe** use names to target a command or element in the input file::

    command-or-element-name.attribute[.index]

* ``command-or-element-name``: The name of the command or element.
* ``attribute``: The attribute of the command or element to set. Required.
* ``index``: Optional. Selects which instance of a command to edit when the command appears more than once
  in the input file. Indices start at 1. If a command is repeated and no index is given, rsopt raises an error.

For example, consider the following parameter from the `match_parallel.yaml` example::

   "L1.k1l":
      min: -1.0
      max: 1.0
      start: 0.0

Here, ``L1`` is an element name, and ``k1l`` is an attribute of that element. To set ``z_position`` on the
second ``define_screen`` command in a spiffe input file, use ``define_screen.z_position.2``.

**genesis** has a single command type, so names only give the attribute and optional index::

    attribute[.index]

Names are checked when the configuration is loaded. A name with the wrong number of parts, or an index that is
not a positive integer, is reported as a configuration error before any simulation runs.

.. note::
   Element and command names that themselves contain ``.`` cannot be targeted. The ``item_name``,
   ``item_attribute``, and ``item_index`` fields supported by earlier versions of rsopt have been removed.
