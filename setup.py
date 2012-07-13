from setuptools import setup, find_packages, Extension
import sys,os

setup(name='motmot.fview_ros_aviwriter',
      description='Robot Operating System (ROS) based avi movie writer or FView',
      version='0.0.1',
      packages = ['motmot.fview_ros_aviwriter',],
      author='Will Dickson',
      author_email='will@iorodeo.com',
      url='https://github.com/willdicksoni/fview_ros_aviwriter',
      entry_points = { 
          'motmot.fview.plugins':'fview_ros_aviwriter = motmot.fview_ros_aviwriter.fview_ros_aviwriter:FviewROS_AVIWriter', 
          },
      )
