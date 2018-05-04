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
from get_shared_coord import get_coordinates
from detect_circles import detect_circles
from sys import argv
import logging
import cv2
import numpy as np


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


def circles_distance(in_path,
                     out_path,
                     camera,
                     show_window=False,
                     marker_size=0.071):

    marker_pixel_size = 150
    pixels_per_cm = marker_pixel_size / (marker_size * 100)
    out_img_scale = 2

    ids, corners = get_coordinates(in_path,
                                   out_path,
                                   camera,
                                   None,
                                   False,
                                   marker_size)

    logging.info(ids)

    fs = cv2.FileStorage(camera, cv2.FILE_STORAGE_READ)

    # Get the camera model
    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    logging.info('Camera Intrinsics: ')
    logging.info(intrinsics.mat())
    logging.info('Camera Distortion: ')
    logging.info(distortion.mat())

    input_image = cv2.imread(in_path)

    height, width, channels = input_image.shape

    # Blank image
    output_image = np.ones((out_img_scale*height,
                            out_img_scale*width,
                            channels),
                           np.uint8) * 255

    center_x = int((out_img_scale * width)/2)
    center_y = int((out_img_scale * height)/2)
    # Rectify the image
    rectified_marker_corners = np.array([[(center_x - marker_pixel_size/2),
                                         (center_y - marker_pixel_size/2)],
                                         [(center_x - marker_pixel_size/2),
                                         (center_y + marker_pixel_size/2)],
                                         [(center_x + marker_pixel_size/2),
                                          (center_y + marker_pixel_size/2)],
                                         [(center_x + marker_pixel_size/2),
                                          (center_y - marker_pixel_size/2)]])

    # logging.info([rectified_marker_corners])

    newCamMatrix, r = cv2.getOptimalNewCameraMatrix(intrinsics.mat(),
                                                    distortion.mat(),
                                                    (width, height),
                                                    1,
                                                    (width, height))

    undistortedImage = cv2.undistort(input_image,
                                     intrinsics.mat(),
                                     distortion.mat(),
                                     newCameraMatrix=newCamMatrix)

    undistortedMarkersCorners = cv2.undistortPoints(corners,
                                                    intrinsics.mat(),
                                                    distortion.mat(),
                                                    P=newCamMatrix)
    logging.info(undistortedMarkersCorners)

    H, _ = cv2.findHomography(undistortedMarkersCorners,
                              rectified_marker_corners,
                              cv2.RANSAC)
    logging.info(H)

    # output_image[0:height, 0:width] = undistortedImage
    output_image = cv2.warpPerspective(undistortedImage,
                                       H,
                                       dsize=(out_img_scale*width,
                                              out_img_scale*height))

    circles = detect_circles(output_image, None, False)

    for i in range(0, len(circles)):
        if circles[i][2] > 100:
            continue

        for j in range(0, len(circles)):
            if i == j:
                continue

            if circles[j][2] > 100:
                continue

            diff = np.subtract(circles[i], circles[j])
            diff[2] = 0

            logging.info("Distance circles " + str(i) + " - " + str(j))
            logging.info(np.linalg.norm(diff) / pixels_per_cm)

    if show_window:
        cv2.imshow('Rectified', undistortedImage)
        cv2.waitKey(0)

    # Write the image to the output path
    if out_path:
        cv2.imwrite(out_path, output_image)


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    in_path = None
    params_path = None
    show_window = False
    marker_size = 0.071

    if '-v' in myargs:
        logging.basicConfig(level=logging.INFO)

    if '-s' in myargs:
        show_window = True

    if '-i' in myargs:
        in_path = myargs['-i']
        logging.info('Input image at ' + in_path)
    else:
        logging.error('No input image provided')
        exit(-1)

    if '-c' in myargs:
        camera = myargs['-c']
        logging.info('Camera Distortion model at ' + camera)
    else:
        logging.error('No Camera Distortion model provided')
        exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']
    else:
        logging.info('No output image path provided')

    if '-m' in myargs:
        marker_size = myargs['-m']

    circles_distance(in_path,
                     out_path,
                     camera,
                     show_window,
                     float(marker_size))
