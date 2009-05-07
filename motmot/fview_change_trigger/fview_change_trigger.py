from __future__ import with_statement, division

import pkg_resources
import warnings, threading
import enthought.traits.api as traits

import motmot.fview.traited_plugin as traited_plugin
import motmot.fview_ext_trig.ttrigger as ttrigger
import numpy as np

from enthought.traits.ui.api import View, Item, Group

class FviewChangeTrigger(traited_plugin.HasTraits_FViewPlugin):
    plugin_name = 'change detecting trigger'

    trigger_device = traits.Instance(ttrigger.DeviceModel)
    enabled = traits.Bool(False)

    capture_background = traits.Button
    _capture_background_notify = traits.Bool(False) # pass value to realtime thread

    difference_mode = traits.Trait( 'darker', 'lighter', 'any change' )

    draw_roi_box = traits.Bool(False)

    roi_left = traits.Int(-1)
    roi_bottom = traits.Int(-1)
    roi_width = traits.Int(-1)
    roi_height = traits.Int(-1)

    threshold_value = traits.Float
    difference_value = traits.Float(5)

    # Store some values about the camera
    camera_cam_id = traits.String(transient=True)
    camera_max_width = traits.Int(transient=True)
    camera_max_height = traits.Int(transient=True)

    traits_view = View(Group(Item(name='enabled'),
                             Item(name='difference_mode'),
                             Item(name='capture_background',
                                  label='set threshold from image',
                                  show_label=False),
                             Item(name='threshold_value'),
                             Item(name='difference_value'),
                             Item(name='draw_roi_box'),
                             Group(Item(name='roi_left'),
                                   Item(name='roi_bottom'),
                                   Item(name='roi_width'),
                                   Item(name='roi_height'),
                                   )))

    def __init__(self,*args,**kwargs):
        super(FviewChangeTrigger,self).__init__(*args,**kwargs)

    def set_all_fview_plugins(self,plugins):
        """Get reference to 'FView external trigger' plugin"""

        # This method is called by FView to let plugins know about
        # each other.

        for plugin in plugins:
            if plugin.get_plugin_name()=='FView external trigger':
                self.trigger_device = plugin.trigger_device
        if self.trigger_device is None:
            raise RuntimeError('this plugin requires "FView external trigger"')

    def _capture_background_fired(self):
        self._capture_background_notify = True

    def camera_starting_notification(self,cam_id,
                                     pixel_format=None,
                                     max_width=None,
                                     max_height=None):
        if self.camera_cam_id != '':
            warnings.warn('FviewChangeTrigger only supports one camera')
            return
        self.camera_cam_id = cam_id
        self.camera_max_width = max_width
        self.camera_max_height = max_height

        # default margin ( in pixels )
        margin = 10
        if self.roi_left==-1:
            self.roi_left = margin
        if self.roi_bottom==-1:
            self.roi_bottom = margin
        if self.roi_width==-1:
            self.roi_width= self.camera_max_width-self.roi_left-margin
        if self.roi_height==-1:
            self.roi_height= self.camera_max_height-self.roi_bottom-margin

    def process_frame(self,cam_id,buf,buf_offset,timestamp,framenumber):
        draw_points = []
        draw_linesegs = []

        if cam_id != self.camera_cam_id:
            return draw_points, draw_linesegs

        l = self.roi_left
        r = l + self.roi_width
        b = self.roi_bottom
        t = b + self.roi_height

        if self.draw_roi_box:
            draw_linesegs.extend( [ (l,b,l,t),
                                    (l,t,r,t),
                                    (r,t,r,b),
                                    (r,b,l,b) ])

        npbuf = np.asarray(buf) # make sure it's a numpy array
        assert buf_offset==(0,0)
        roi_buf = npbuf[b:t,l:r]

        if self._capture_background_notify:
            self._capture_background_notify = False
            self.threshold_value = np.mean(roi_buf)

        # turn of LED from any previous runs
        self.trigger_device.led1 = False

        if self.enabled:
            current_value = np.mean(roi_buf)
            fire_trigger = False
            if self.difference_mode == 'darker':
                if (self.threshold_value - current_value) > self.difference_value:
                    fire_trigger = True
            elif self.difference_mode == 'lighter':
                if (current_value - self.threshold_value) > self.difference_value:
                    fire_trigger = True
            elif self.difference_mode == 'any change':
                if abs(current_value - self.threshold_value) > self.difference_value:
                    fire_trigger = True
            else:
                raise ValueError('unknown difference_mode')

            if fire_trigger:
                # fire pulse on EXT_TRIG1
                self.trigger_device.ext_trig1 = True

                # toggle LED
                self.trigger_device.led1 = True

        return draw_points, draw_linesegs
