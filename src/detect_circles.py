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


def detect_circles_read_img(in_path,
                            out_path,
                            show_window=False):

    # Read the input image
    input_image = cv2.imread(in_path)

    return detect_circles(input_image, out_path, show_window)


def detect_circles(input_image,
                   out_path,
                   show_window=False):

    input_image_gray = cv2.cvtColor(input_image,
                                    cv2.COLOR_BGR2GRAY)

    input_image_gray = cv2.GaussianBlur(input_image_gray, (9, 9), 2, 2)

    height, width = input_image_gray.shape

    # Apply the Hough Transform to find the circles
    circles = cv2.HoughCircles(input_image_gray,
                               cv2.HOUGH_GRADIENT,
                               1,
                               width/8)

    logging.info(circles[0])

    # Draw the circles detected
    for circle in circles[0]:

        center = (int(circle[0]), int(circle[1]))
        radius = int(circle[2])
        input_image = cv2.circle(input_image,
                                 center, radius, (0, 0, 255), 3, 8, 0)

    # Show the window
    if show_window:
        cv2.imshow('Window', input_image)
        cv2.waitKey(0)

    # Write the image to the output path
    if out_path:
        cv2.imwrite(out_path, input_image)

    return circles[0]


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    detection_path = None
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

    # if '-d' in myargs:
    #     detection_path = myargs['-d']
    # else:
    #     logging.info('No detection file path provided')
    #     exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']
    else:
        logging.info('No output image path provided')

    detect_circles_read_img(in_path,
                            out_path,
                            show_window)
