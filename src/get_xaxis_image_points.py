# Copyright 2018 Pedro Cuadra - pjcuadra@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from sys import argv
import logging
import cv2
import numpy as np
from get_shared_coord import get_coordinates_system


def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] is '-':  # Found a "-name value" pair.
            if len(argv) > 1:
                if argv[1][0] != '-':
                    opts[argv[0]] = argv[1]
                else:
                    opts[argv[0]] = True
            elif len(argv) == 1:
                opts[argv[0]] = True

        # Reduce the argument list by copying it starting from index 1.
        argv = argv[1:]
    return opts

def get_id_list(input_image, camera, marker_size, out_path=None):
    """
    Perform marker recognition of the image and return the data
    for markers found.

    :param input_image: the image to run marker recognition on
    :param camera: the path to the camera calibration file
    :param marker_size: the size of the marker's sides (in meters)
    :param output_path: (optional) path to image file. If not None, 
        a copy of the input image with markers and coordinate 
        systems drawn into it will be written to this file
    
    :return: upon failure, None, None, None will be returned. Upon
        success, the method returns three objects:
        1 - A list of all marker IDs detected. Each marker is contained
            in it's own list: [[33], [18], [66], ...]
        2 - The data belonging to those IDs. Have a look at a method like
            get_xaxis_image_points to see how to retrieve it.
        3 - An OpenCV FileSystem object (or, rather, handle). This is used
            by OpenCV to access the file system and should be closed once
            we are done using it.
    """
    fs = cv2.FileStorage(camera, cv2.FILE_STORAGE_READ)
    # Get the camera model
    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    logging.debug('Camera Intrinsics: ')
    logging.debug(intrinsics.mat())
    logging.debug('Camera Distortion: ')
    logging.debug(distortion.mat())

    ids, _, json_content = get_coordinates_system(input_image,
                                                  intrinsics,
                                                  distortion,
                                                  marker_size=marker_size,
                                                  out_path=out_path)
    if ids is None:
        return None, None, None
    return ids.tolist(), json_content, fs

def get_marker_position(target_id, ids, json_content):
    if target_id not in ids:
        return None
    id = ids.index(target_id)
    return json_content["m_c"][id]

def get_xaxis_image_points(target_id, ids, json_content, fs, marker_size):
    """
    Try to extract two positions in the image from a single marker.

    If target_id is found in the id list given to this method, it
    will return two points in the image: The center point of the 
    marker and a second point, moved along its x axis.

    :param target_id: the ID of the target marker
    :param ids: the ID list as returned by get_id_list
    :param json_content: the marker data as returned by get_id_list
    :param fs: the OpenCV FileSystem handle returned by get_id_list
    :param float marker_size: The size of the marker's sides (in meters)

    :return: None, None if the marker with ID target_id was not found; 
        otherwise, returns the position of the marker's center point 
        and a second position moved along its x axis
    """
    if ids is None or json_content is None:
        return None, None
    if [target_id] not in ids:
        return None, None

    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    id = ids.index([target_id])

    center = json_content["m_c"][id]
    rvecs = json_content["rvecs"]
    tvecs = json_content["tvecs"]

    logging.debug('Received Centers -> {}'.format(json_content["m_c"]))

    rvec = np.array(rvecs[id])
    tvec = np.array(tvecs[id])

    xaxis_end_marker = np.array([[0, marker_size, 0]])

    logging.debug(xaxis_end_marker)
    logging.debug(rvec)
    logging.debug(tvec)

    xaxis_end, _ = cv2.projectPoints(xaxis_end_marker,
                                     rvec,
                                     tvec,
                                     intrinsics.mat(),
                                     distortion.mat())

    logging.debug('X Axis Start -> {}'.format(center))
    logging.debug('X Axis End -> {}'.format(xaxis_end[0][0]))

    return center, xaxis_end[0][0]

def get_marker_system(target_id, ids, json_content, fs, marker_size):
    """
    Retrieve the axes of the coordinate system centered on the marker with
    ID target_id.

    :param target_id: the ID of the target marker
    :param ids: the ID list as returned by get_id_list
    :param json_content: the marker data as returned by get_id_list
    :param fs: the OpenCV FileSystem handle returned by get_id_list
    :param float marker_size: The size of the marker's sides (in meters)

    :return: four pairs of float, denoting the center point of the marker
        and one point moved along one of the coordinate system's axes. If
        target_id was not found, returns None, None, None, None
    """
    if ids is None or json_content is None:
        return None, None, None, None
    if [target_id] not in ids:
        return None, None, None, None

    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    id = ids.index([target_id])

    rvecs = json_content["rvecs"]
    tvecs = json_content["tvecs"]

    rvec = np.array(rvecs[id])
    tvec = np.array(tvecs[id])

    points = np.array([
        [0, 0, 0],          # origin
        [marker_size, 0, 0],# x axis
        [0, marker_size, 0],# y axis
        [0, 0, marker_size] # z axis
    ])

    logging.debug(points)
    logging.debug(rvec)
    logging.debug(tvec)

    projected_axes, _ = cv2.projectPoints(points,
                                     rvec,
                                     tvec,
                                     intrinsics.mat(),
                                     distortion.mat())
    # center, x axis, y axis, z axis
    return projected_axes[0][0], projected_axes[1][0], projected_axes[3][0], projected_axes[2][0]

def _get_xaxis_image_points(input_image, camera, marker_size, out_path=None):
    """
    Original, all-in-one implementation of get_xaxis_image_points.
    """
    fs = cv2.FileStorage(camera, cv2.FILE_STORAGE_READ)
    # Get the camera model
    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    logging.debug('Camera Intrinsics: ')
    logging.debug(intrinsics.mat())
    logging.debug('Camera Distortion: ')
    logging.debug(distortion.mat())

    ids, _, json_content = get_coordinates_system(input_image,
                                                  intrinsics,
                                                  distortion,
                                                  marker_size=marker_size,
                                                  out_path=out_path)
    if ids is None:
        return None, None
    ids = ids.tolist()
    logging.debug(ids)

    # 23 is the ID of the marker we use to construct the coordinate system.
    # We also use the marker with the ID 66 to signal the lettuce object
    # either not yet having been placed on the table or being moved, so we
    # can use the presence of this marker ID to determine if we should 
    # continue processing or discard the image.
    if [23] not in ids:
        return None, None

    id = ids.index([23])

    center = json_content["m_c"][id]
    rvecs = json_content["rvecs"]
    tvecs = json_content["tvecs"]

    logging.debug('Received Centers -> {}'.format(json_content["m_c"]))

    rvec = np.array(rvecs[id])
    tvec = np.array(tvecs[id])

    xaxis_end_marker = np.array([[0, marker_size, 0]])

    logging.debug(xaxis_end_marker)
    logging.debug(rvec)
    logging.debug(tvec)

    xaxis_end, _ = cv2.projectPoints(xaxis_end_marker,
                                     rvec,
                                     tvec,
                                     intrinsics.mat(),
                                     distortion.mat())

    logging.debug('X Axis Start -> {}'.format(center))
    logging.debug('X Axis End -> {}'.format(xaxis_end[0][0]))

    return center, xaxis_end[0][0]


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    in_path = None
    params_path = None
    show_window = False
    save_image = False
    marker_size = 0.071

    if '-v' in myargs:
        logging.basicConfig(level=logging.DEBUG)

    if '-i' in myargs:
        in_path = myargs['-i']
        logging.debug('Input image at ' + in_path)
    else:
        logging.error('No input image provided')
        exit(-1)

    if '-c' in myargs:
        camera = myargs['-c']
        logging.debug('Camera Distortion model at ' + camera)
    else:
        logging.error('No Camera Distortion model provided')
        exit(-1)

    if '-m' in myargs:
        marker_size = myargs['-m']

    # Read the input image
    input_image = cv2.imread(in_path)

    xaxis_start, xaxis_end = _get_xaxis_image_points(input_image,
                                                    camera,
                                                    marker_size)

    xaxis_start = (int(xaxis_start[0]), int(xaxis_start[1]))
    xaxis_end = (int(xaxis_end[0]), int(xaxis_end[1]))
    cv2.circle(input_image, xaxis_start, 5, (255, 0, 0), 3, 8, 0)
    cv2.circle(input_image, xaxis_end, 5, (0, 255, 0), 3, 8, 0)

    # Show the window
    if show_window:
        cv2.imshow('Augmented', input_image)
        cv2.waitKey(0)
    if save_image:
        cv2.imwrite("output.jpg", input_image)
