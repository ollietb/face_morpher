"""
Locate face points
"""

import cv2
import numpy as np

import subprocess
import sys
import os.path as path

from facemorpher import cvver
FILE_DIR = path.dirname(path.realpath(__file__))
DATA_DIR = path.join(FILE_DIR, 'data')
BIN_DIR = path.join(FILE_DIR, 'bin')

try:
  import dlib
  dlib_detector = dlib.get_frontal_face_detector()
  dlib_predictor = dlib.shape_predictor(path.join(DATA_DIR, 'shape_predictor_68_face_landmarks.dat'))
except:
  pass

# Stasm util binary in `bin` folder available for these platforms
SUPPORTED_PLATFORMS = {
  'linux': 'linux',
  'linux2': 'linux',
  'darwin': 'osx'
}


def boundary_points(points, width_percent=0.1, height_percent=0.1):
  """ Produce additional boundary points
  :param points: *m* x 2 array of x,y points
  :param width_percent: [-1, 1] percentage of width to taper inwards. Negative for opposite direction
  :param height_percent: [-1, 1] percentage of height to taper downwards. Negative for opposite direction
  :returns: 2 additional points at the top corners
  """
  x, y, w, h = cv2.boundingRect(np.array([points], np.int32))
  spacerw = int(w * width_percent)
  spacerh = int(h * height_percent)
  return [[x+spacerw, y+spacerh],
          [x+w-spacerw, y+spacerh]]

def face_points_dlib(imgpath, add_boundary_points=True):
  """ Locates 68 face points using dlib (http://dlib.net)

  :param imgpath: an image path to extract the 68 face points
  :param add_boundary_points: bool to add additional boundary points
  :returns: Array of x,y face points. Empty array if no face found
  """
  try:
    points = []
    image = cv2.imread(imgpath)
    rgbimg = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rects = dlib_detector(rgbimg, 1)

    if rects and len(rects) > 0:
      # We only take the first found face
      shapes = dlib_predictor(rgbimg, rects[0])
      points = np.array([(shapes.part(i).x, shapes.part(i).y) for i in range(68)], np.int32)

      if add_boundary_points:
        # Add more points inwards and upwards as dlib only detects up to eyebrows
        points = np.vstack([
          points,
          boundary_points(points, 0.1, -0.03),
          boundary_points(points, 0.13, -0.05),
          boundary_points(points, 0.15, -0.08),
          boundary_points(points, 0.33, -0.12)])

  points = points.astype(np.int32)
  if len(points) == 0:
    return points
  except Exception as e:
    print(e)
    return []

def face_points(imgpath, add_boundary_points=True):
  """ High-level function to detect face points using dlib

  :param imgpath: an image path to extract face points
  :param add_boundary_points: bool to add additional boundary points
  :returns: Array of x,y face points. Empty array if no face found
  """
  points = face_points_dlib(imgpath, add_boundary_points)
  return points

  if add_boundary_points:
    return np.vstack([points, boundary_points(points)])

  return points

def average_points(point_set):
  """ Averages a set of face points from images

  :param point_set: *n* x *m* x 2 array of face points. \\
  *n* = number of images. *m* = number of face points per image
  """
  return np.mean(point_set, 0).astype(np.int32)

def weighted_average_points(start_points, end_points, percent=0.5):
  """ Weighted average of two sets of supplied points

  :param start_points: *m* x 2 array of start face points.
  :param end_points: *m* x 2 array of end face points.
  :param percent: [0, 1] percentage weight on start_points
  :returns: *m* x 2 array of weighted average points
  """
  if percent <= 0:
    return end_points
  elif percent >= 1:
    return start_points
  else:
    return np.asarray(start_points*percent + end_points*(1-percent), np.int32)
