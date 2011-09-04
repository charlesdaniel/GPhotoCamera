## A Python Wrapper around a very small subset of libgphoto2 via ctypes
## Copyright (c) 2009 Charles Daniel
##
## GPhotoCamera is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2, or (at your option)
## any later version.
##
## GPhotoCamera is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Paparazzi; see the file COPYING.  If not, write to
## the Free Software Foundation, 59 Temple Place - Suite 330,
## Boston, MA 02111-1307, USA.

## Note: As of the writing of this file gphoto2 was at version 2.4.8 and only really runs on Linux (we tested in Ubuntu 9.10 and 10.04).

## More information about gphoto can be found here:
## http://gphoto.sourceforge.net/

## More information about ctypes can be found here:
## http://python.net/crew/theller/ctypes/tutorial.html

import sys;
from ctypes import *;

## You may need to fix this filename if it's different on your OS.
G = cdll.LoadLibrary("libgphoto2.so.2");

class CameraFilePath(Structure):
	_fields_ = [("name", c_char * 128), ("folder", c_char * 1024)];

class GPhotoCamera():
	RetVals = {
		'GP_ERROR_CORRUPTED_DATA': -102,
		'GP_ERROR_FILE_EXISTS': -103,
		'GP_ERROR_MODEL_NOT_FOUND': -105,
		'GP_ERROR_DIRECTORY_NOT_FOUND': -107,
		'GP_ERROR_FILE_NOT_FOUND': -108,
		'GP_ERROR_DIRECTORY_EXISTS': -109,
		'GP_ERROR_CAMERA_BUSY': -110,
		'GP_ERROR_PATH_NOT_ABSOLUTE': -111,
		'GP_ERROR_CANCEL': -112,
		'GP_ERROR_CAMERA_ERROR': -113,
		'GP_ERROR_OS_FAILURE': -114,

		'GP_OK': 0,
		'GP_ERROR': -1,
		'GP_ERROR_BAD_PARAMETERS': -2,
		'GP_ERROR_NO_MEMORY': -3,
		'GP_ERROR_LIBRARY': -4,
		'GP_ERROR_UNKNOWN_PORT': -5,
		'GP_ERROR_NOT_SUPPORTED': -6,
		'GP_ERROR_IO': -7,
		'GP_ERROR_FIXED_LIMIT_EXCEEDED': -8,
		'GP_ERROR_TIMEOUT': -10,
		'GP_ERROR_IO_SUPPORTED_SERIAL': -20,
		'GP_ERROR_IO_SUPPORTED_USB': -21,
		'GP_ERROR_IO_INIT': -31,
		'GP_ERROR_IO_READ': -34,
		'GP_ERROR_IO_WRITE': -35,
		'GP_ERROR_IO_UPDATE': -37,
		'GP_ERROR_IO_SERIAL_SPEED': -41,
		'GP_ERROR_IO_USB_CLEAR_HALT': -51,
		'GP_ERROR_IO_USB_FIND': -52,
		'GP_ERROR_IO_USB_CLAIM': -53,
		'GP_ERROR_IO_LOCK': -60,
		'GP_ERRO_HAL': -70,
	};

	ErrorLookup = dict([(v,k) for (k,v) in RetVals.iteritems()]);

	CameraWidgetTypes = {
		'GP_WIDGET_WINDOW': 0,
		'GP_WIDGET_SECTION': 1,
		'GP_WIDGET_TEXT': 2,
		'GP_WIDGET_RANGE': 3,
		'GP_WIDGET_TOGGLE': 4,
		'GP_WIDGET_RADIO': 5,
		'GP_WIDGET_MENU': 6,
		'GP_WIDGET_BUTTON': 7,
		'GP_WIDGET_DATE': 8,
	};

	CameraCaptureTypes = {
		'GP_CAPTURE_IMAGE': 0,
		'GP_CAPTURE_MOVIE': 1,
		'GP_CAPTURE_SOUND': 2,
	};
	CameraFileTypes = {
		'GP_FILE_TYPE_PREVIEW': 0,
		'GP_FILE_TYPE_NORMAL': 1,
		'GP_FILE_TYPE_RAW': 2,
		'GP_FILE_TYPE_AUDIO': 3,
		'GP_FILE_TYPE_EXIF': 4,
		'GP_FILE_TYPE_METADATA': 5,
	};

	def __init__(self):
		self.canoncontext = G.gp_context_new();
		self.canon = c_void_p();
		self.capture_preview_flag = False;

		G.gp_camera_new(pointer(self.canon));

		retval = G.gp_camera_init(self.canon, self.canoncontext);
		if(retval != self.RetVals['GP_OK']):
			print "ERROR: %s\n" % (GPhotoCamera.ErrorLookup[retval]);
			sys.exit(retval);


	def _lookup_widget(self, widget, key, child):
		ret = G.gp_widget_get_child_by_name(widget, key, child);
		if(ret == GPhotoCamera.RetVals['GP_OK']):
			ret = G.gp_widget_get_child_by_label(widget, key, child);
		return ret;


	def get_config_value_string(self, camera, key, str, context):
		widget = c_void_p();	# CameraWidget
		child = c_void_p();	# CameraWidget
		type = 	c_int();	# CameraWidgetType
		val = c_char_p();

		ret = G.gp_camera_get_config(camera, pointer(widget), context);
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "camera_get_config failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			return ret;

		ret = self._lookup_widget(widget, key, pointer(child));
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "lookup widget failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;

		ret = G.gp_widget_get_type(child, pointer(type));
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "widget get type failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;

		if((type != GPhotoCamera.CameraWidgetTypes['GP_WIDGET_MENU']) and (type != GPhotoCamera.CameraWidgetTypes['GP_WIDGET_RADIO']) and (type != GPhotoCamera.CameraWidgetTypes['GP_WIDGET_TEXT'])):
			print "widget has bad type %d\n" % type;
			ret = GPhotoCamera.RetVals['GP_ERROR_BAD_PARAMETERS'];
			G.gp_widget_free(widget);
			return ret;

		ret = G.gp_widget_get_value(child, pointer(val));
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "could not query widget value: %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;

		str.value = val.value;
		G.gp_widget_free(widget);
		return ret;


	def set_config_value_string(self, camera, key, val, context):
		widget = c_void_p();	# CameraWidget
		child = c_void_p();	# CameraWidget
		type = c_int();		# CameraWidgetType

		ret = G.gp_camera_get_config(camera, pointer(widget), context);
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "camera_get_config failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			return ret;

		ret = self._lookup_widget(widget, key, pointer(child));
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "lookup widget failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;

		ret = G.gp_widget_get_type(child, pointer(type));
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "widget get type failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;
		
		if((type != GPhotoCamera.CameraWidgetTypes['GP_WIDGET_MENU']) and (type != GPhotoCamera.CameraWidgetTypes['GP_WIDGET_RADIO']) and (type != GPhotoCamera.CameraWidgetTypes['GP_WIDGET_TEXT'])):
			print "widget has bad type %d\n" % type;
			ret = GPhotoCamera.RetVals['GP_ERROR_BAD_PARAMETERS'];
			G.gp_widget_free(widget);
			return ret;


		ret = G.gp_widget_set_value(child, val);
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "could not set widget value: %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;

		ret = G.gp_camera_set_config(camera, widget, config);
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "camera_set_config failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			return ret;

		G.gp_widget_free(widget);
		return ret;

	def canon_enable_capture(self, camera, onoff, context):
		widget = c_void_p();	# CameraWidget
		child = c_void_p();	# CameraWidget
		type = 	c_int();	# CameraWidgetType

		ret = G.gp_camera_get_config(camera, pointer(widget), context);
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "camera_get_config failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			return ret;

		ret = self._lookup_widget(widget, "capture", pointer(child));
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "warning: lookup of capture failed %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;

		ret = G.gp_widget_get_type(child, pointer(type));
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "widget get type failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;

		if(type != GPhotoCamera.CameraWidgetTypes['GP_WIDGET_TOGGLE']):
			print "widget has bad type %d\n" % type;
			ret = GPhotoCamera.RetVals['GP_ERROR_BAD_PARAMETERS'];
			G.gp_widget_free(widget);
			return ret;

		# Now set the toggle to the wanted value

		ret = G.gp_widget_set_value(child, pointer(onoff));
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "toggling Canon capture to %d failed with %s\n" % (onoff, GPhotoCamera.ErrorLookup[ret]);
			G.gp_widget_free(widget);
			return ret;

		# OK

		ret = G.gp_camera_set_config(camera, widget, context);
		if(ret < GPhotoCamera.RetVals['GP_OK']):
			print "camera_set_config failed: %s\n" % GPhotoCamera.ErrorLookup[ret];
			G.gp_widget_free(widget);
			return ret;

		G.gp_widget_free(widget);
		self.capture_preview_flag = True;
		return ret;



	def capture_to_file(self, canon, canoncontext, fn):
		canonfile = c_void_p();
		camera_file_path = CameraFilePath();

		print "Capturing.\n";

		camera_file_path.folder = '100EOS7D';
		camera_file_path.name = 'foo1.jpg';
		ret = G.gp_camera_capture(self.canon, GPhotoCamera.CameraCaptureTypes['GP_CAPTURE_IMAGE'], pointer(camera_file_path), self.canoncontext);
		#print "   RetVal: %s\n" % GPhotoCamera.ErrorLookup[ret];

		#print "Pathname on the camera: %s/%s\n" % (camera_file_path.folder, camera_file_path.name);

		fd = open(fn, "wb");
		ret = G.gp_file_new_from_fd(pointer(canonfile), fd.fileno());
		#print "   RetVal: %s\n" % GPhotoCamera.ErrorLookup[ret];

		#print "Getting image.\n";
		ret = G.gp_camera_file_get(self.canon, camera_file_path.folder, camera_file_path.name, GPhotoCamera.CameraFileTypes['GP_FILE_TYPE_NORMAL'], canonfile, self.canoncontext);
		#print "   RetVal: %s\n" % GPhotoCamera.ErrorLookup[ret];

		#print "Deleting.\n";
		#ret = G.gp_camera_file_delete(self.canon, camera_file_path.folder, camera_file_path.name, self.canoncontext);
		#print "   RetVal: %s\n" % GPhotoCamera.ErrorLookup[ret];

#		G.gp_file_free(canonfile);


	def capture_preview(self, output_file):
		file = c_void_p();

		#if(not self.capture_preview_flag):
			# 1 = TRUE
			#self.canon_enable_capture(self.canon, 1, self.canoncontext);

		retval = G.gp_file_new(pointer(file));
		#retval = G.gp_file_new_from_fd(pointer(file), sock.fileno());
		if(retval != GPhotoCamera.RetVals['GP_OK']):
			print "ERROR: gp_file_new: %s\n" % GPhotoCamera.ErrorLookup[retval];
			sys.exit(retval);

		retval = G.gp_camera_capture_preview(self.canon, file, self.canoncontext);
		if(retval != GPhotoCamera.RetVals['GP_OK']):
			print "ERROR: gp_camera_capture_preview: %s\n" % GPhotoCamera.ErrorLookup[retval];
			sys.exit(retval);

		retval = G.gp_file_save(file, output_file);
		if(retval != GPhotoCamera.RetVals['GP_OK']):
			print "ERROR: gp_file_save : %s\n" % GPhotoCamera.ErrorLookup[retval];
			sys.exit(retval);

		G.gp_file_unref(file);
		return retval;

	def capture_image(self, output_file):
		print "Capturing Image!\n";
		return self.capture_to_file(self.canon, self.canoncontext, output_file);


	def __del__(self):
		G.gp_camera_exit(self.canon, self.canoncontext);


if(__name__ == '__main__'):
	cam = GPhotoCamera();
	cam.capture_preview('preview.jpg');
	cam.capture_image('full_image.jpg');

