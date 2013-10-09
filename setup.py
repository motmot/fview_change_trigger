from setuptools import setup, find_packages
import sys,os

setup(name='motmot.fview_change_trigger',
      description='change trigger plugin for FView',
      version='0.0.2',
      packages = find_packages(),
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      url='http://code.astraw.com/projects/motmot',
      entry_points = {
    'motmot.fview.plugins':'fview_change_trigger = motmot.fview_change_trigger.fview_change_trigger:FviewChangeTrigger',
    },
      )
