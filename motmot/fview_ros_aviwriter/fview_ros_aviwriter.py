from __future__ import with_statement, division
import pkg_resources
import warnings, threading
import os
import subprocess
import time
import atexit

try:
    import enthought.traits.api as traits
    from enthought.traits.ui.api import View, Item, Group, UItem, HGroup
    from enthought.pyface.api import FileDialog, OK
except ImportError:
    # traits 4
    import traits.api as traits
    from traitsui.api import View, Item, Group, UItem, HGroup

import motmot.fview.traited_plugin as traited_plugin
import numpy as np

try:
    import roslib
    have_ROS = True
except ImportError, err:
    have_ROS = False

have_basic_avi_writer = False
if have_ROS:
    try:
        roslib.load_manifest('basic_avi_writer')
        have_basic_avi_writer = True
    except roslib.exceptions.ROSLibException, e:
        msg = 'unable to load basic_avi_writer manifest'
        raise RuntimeError, msg
    import rospy

DEFAULT_PATH = os.environ['HOME']
DEFAULT_FILENAME = os.path.join(DEFAULT_PATH,'fview_default.avi')

class FviewROS_AVIWriter(traited_plugin.HasTraits_FViewPlugin):

    plugin_name = 'FView ROS AVI writer'
    roscore_popen = traits.Any(transient=True)
    writer_popen = traits.Any(transient=True)
    path = traits.String(DEFAULT_PATH)
    filename = traits.String(DEFAULT_FILENAME)
    recording = traits.Bool(False)
    set_filename_button = traits.Button('Set File')
    start_button = traits.Button('Start')
    stop_button = traits.Button('Stop')
    file_wildcard = traits.Str("AVI Movie file (*.avi)|*.avi")

    traits_view = View( 
                Group(
                    Item('filename',style='readonly'),
                    HGroup(
                        UItem('set_filename_button',enabled_when ="not recording"), 
                        UItem('start_button',enabled_when="not recording"),
                        UItem('stop_button',enabled_when="recording"),
                        )
                    )
                )

    def __init__(self,*args,**kwargs):
        super(FviewROS_AVIWriter, self).__init__(*args,**kwargs)

        self.roscore_popen = None
        self.writer_popen = None
        atexit.register(self.cleanup)

        if have_ROS and have_basic_avi_writer:
            if not roscore_running(): 
                self.roscore_popen = subprocess.Popen(['roscore'],stdout=subprocess.PIPE)
                while not roscore_running():
                    time.sleep(0.5)
            rospy.init_node('fview', anonymous=True, disable_signals=True,)
        else:
            raise RuntimeError, 'ROS not available'

    def _filename_changed(self):
        print '_filename_changed'

    def _recording_changed(self):
        print '_recording_changed', self.recording
        if self.recording == True:
            self.start_recording_node()
        else:
            self.stop_recording_node()

    def _start_button_fired(self):
        print '_start_button_fired'
        if self.recording == False:
            self.recording = True

    def _stop_button_fired(self):
        print '_stop_button_fired'
        if self.recording == True:
            self.recording = False

    def _set_filename_button_fired(self):
        dialog = FileDialog(
                default_directory=self.path,
                default_filename=self.filename,
                action="save as", 
                wildcard=self.file_wildcard
                )
        dialog.open()
        if dialog.return_code == OK:
            if not os.path.isdir(dialog.directory):
                raise IOError, 'directory does not exist'
            self.path = dialog.directory
            root, ext = os.path.splitext(dialog.filename)
            if not ext:
                ext = '.avi'
            filename = '{0}{1}'.format(root,ext)
            self.filename = os.path.join(dialog.directory, filename)

    def start_recording_node(self):
        print 'start recording node'
        image_topic = get_image_raw_topic()
        cmd = [ 'rosrun', 'basic_avi_writer', 'avi_writer_node.py'] 
        cmd.extend([image_topic, self.filename])
        self.writer_popen = subprocess.Popen(cmd)

    def stop_recording_node(self):
        print 'stop recording node'
        if self.writer_popen is not None:
            self.writer_popen.send_signal(subprocess.signal.SIGINT)
            self.writer_popen.wait()
            self.writer_popen = None

    def cleanup(self):
        # Close any open processes
        popen_list = [self.writer_popen, self.roscore_popen]
        for item in popen_list:
            if item is not None:
                item.send_signal(subprocess.signal.SIGINT)
                item.wait()

# -----------------------------------------------------------------------------

def get_image_raw_topic(): 
    """
    Returns the ROS fview image topic - actually returns the first image_raw topic that
    can be found and assumes that it is the fview image topic. There is probably a better
    why to do this.
    """
    topic_list = subprocess.Popen(['rostopic','list'],stdout=subprocess.PIPE).communicate()[0]
    topic_list = topic_list.split('\n')
    image_raw_topic = None
    for topic in topic_list:
        if topic[-9:] == 'image_raw':
            image_raw_topic = topic
    return image_raw_topic

def roscore_running(): 
    """
    Checks to see if ROS core is running. This is a bit kludgey as I just uses popen
    to call the rosnode command line function. If is fails than it is assumed that 
    ROS core isn't running.
    """
    devnull = open(os.devnull, 'w')
    rosnode_popen = subprocess.Popen(
            ['rosnode', 'list'], 
            stdout=subprocess.PIPE, 
            stderr=devnull
            )
    rsp = rosnode_popen.communicate()[0]
    if not rsp:
        return False
    else:
        return True


