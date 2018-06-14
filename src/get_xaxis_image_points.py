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


def get_xaxis_image_points(input_image, camera, marker_size):
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
                                                  marker_size=marker_size)
    ids = ids.tolist()
    logging.debug(ids)

    if [23] not in ids:
        return None

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

    xaxis_start, xaxis_end = get_xaxis_image_points(input_image,
                                                    camera,
                                                    marker_size)

    xaxis_start = (int(xaxis_start[0]), int(xaxis_start[1]))
    xaxis_end = (int(xaxis_end[0]), int(xaxis_end[1]))
    cv2.circle(input_image, xaxis_start, 5, (255, 0, 0), 3, 8, 0)
    cv2.circle(input_image, xaxis_end, 5, (0, 255, 0), 3, 8, 0)

    # Show the window
    # if show_window:
    cv2.imshow('Augmented', input_image)
    cv2.waitKey(0)
