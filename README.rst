===============================
iLabs plug-in
===============================

The `LabManager <http://github.com/gateway4labs/labmanager/>`_ provides an API for
supporting more Remote Laboratory Management Systems (RLMS). This project is the
implementation for the `MIT iLab Shared Architecture <http://ilab.mit.edu/wiki>`

Usage
-----

First install the module::

  $ pip install git+https://github.com/gateway4labs/rlms_ilabs.git

Then add it in the LabManager's ``config.py``::

  RLMS = ['iLabs', ... ]

The ``/iLab/clientList.aspx.cs`` provides an optional feature that should be deployed within an iLab Service Broker. It is a service that returns a list of lab clients available for an specific authority.

Profit!
