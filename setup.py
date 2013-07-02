#-*-*- encoding: utf-8 -*-*-
from setuptools import setup

classifiers=[
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "License :: Freely Distributable",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
]

cp_license="MIT"

# TODO: depend on gateway4labs

setup(name='g4l_rlms_ilabs',
      version='0.1',
      description="iLabs plug-in in the gateway4labs RLMS",
      classifiers=classifiers,
      author='Pablo Orduña, Christina Stuart',
      author_email='pablo.orduna@deusto.es, cstuart1021@gmail.com',
      url='http://github.com/gateway4labs/rlms_ilabs/',
      license=cp_license,
      py_modules=['g4l_rlms_ilabs'],
     )
