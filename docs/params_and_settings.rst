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

Settings Naming and Parsing
--------------------------

Settings can be simple values, or follow a naming convention to target specific parts of a code's input. rsopt uses a string formatting convention to specify model command/element names and attributes: ``command-or-element-name.[command-or-element-attribute].[command-index]``.

* ``command-or-element-name``: The name of the command or element.
* ``command-or-element-attribute``: The specific attribute of the command or element.
* ``command-index``: The index of the command or element, in case there are multiple instances.

If a setting name includes the ``.`` character, this formatting is not usable. In such cases, the ``item_name``, ``item_attribute``, and ``item_index`` fields can be used directly.  Settings also support this explicit naming convention.

Settings Class Definition
-------------------------

.. automodule:: rsopt.configuration.settings
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

Parameter Naming and Parsing
--------------------------

Similar to settings, parameters can also use a naming convention to target specific parts of a code's input. rsopt uses a string formatting convention to specify model command/element names and attributes: ``command-or-element-name.[command-or-element-attribute].[command-index]``.

* ``command-or-element-name``: The name of the command or element.
* ``command-or-element-attribute``: The specific attribute of the command or element.
* ``command-index``: The index of the command or element, in case there are multiple instances.

For example, consider the following parameter from the `match_parallel.yaml` example:

::

   "L1.k1l":
      min: -1.0
      max: 1.0
      start: 0.0

Here, `"L1"` is an element name, and `"k1l"` is an attribute of that element.

If a parameter name includes the ``.`` character or this formatting is not desired, the ``item_name``, ``item_attribute``, and ``item_index`` fields can be used directly.  The above parameter could be equivalently specified as:

::

   "my_parameter":
      item_name: "L1"
      item_attribute: "k1l"
      min: -1.0
      max: 1.0
      start: 0.0
