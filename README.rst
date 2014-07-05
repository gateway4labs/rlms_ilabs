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

  RLMS = ['ilabs', ... ]


The ``/iLab/clientList.aspx.cs`` provides an optional feature that should be deployed within an iLab Service Broker. It is a service that returns a list of lab clients available for an specific authority. Can be installed for ISA releases 4.3.1 or newer. You will need Visual Sudio to compile it.

A precompiled version can be download from here: `http://ilabs.cti.ac.at/Precompiled.zip <http://ilabs.cti.ac.at/Precompiled.zip>`.

Profit!
