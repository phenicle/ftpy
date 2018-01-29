# setup.py

from setuptools import setup

with open("README", 'r') as f:
    long_description = f.read()

setup(
   name='ftpy',
   version='1.0.5',
   description='A python FTP module that supports pythonic idioms.',
   license="LGPLv3",
   long_description='Against our will, we had to build a python SFTP module to address deficiencies (support for mget) with existing ones. Might as well include FTP and provide a consistent behavior. Enjoy!',
   author='Phenicle',
   author_email='pheniclebeefheart@gmail.com',
   url="https://github.com/phenicle/ftpy",
   packages=['ftpy',],  #same as name
   install_requires=['pexpect', 'cfgpy'], #external packages as dependencies
)
