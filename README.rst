WebLab-Deusto plug-in for iLabs
===============================

The `LabManager <http://github.com/lms4labs/labmanager/>`_ provides an API for
supporting more Remote Laboratory Management Systems (RLMS). This project is the
implementation for the `FCEIA / Universidad Nacional del Rosario
<http://labremf4a.fceia.unr.ar/>`_ remote laboratory.

Usage
-----

First install the module::

  $ pip install git+https://github.com/lms4labs/rlms_unr.git

Then add it in the LabManager's ``config.py``::

  RLMS = ['unr', ... ]

Profit!
