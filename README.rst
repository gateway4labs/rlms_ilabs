DO NOT USE THIS YET
===============================


iLabs plug-in
===============================

The `LabManager <http://github.com/gateway4labs/labmanager/>`_ provides an API for
supporting more Remote Laboratory Management Systems (RLMS). This project is the
implementation for the `MIT iLabs <http://ilab.mit.edu/wiki>`_ remote 
laboratory.

Usage
-----

First install the module::

  $ pip install git+https://github.com/gateway4labs/rlms_ilabs.git

Then add it in the LabManager's ``config.py``::

  RLMS = ['iLabs', ... ]

Profit!
