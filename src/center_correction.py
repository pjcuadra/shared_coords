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
import json


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


def correct_center(in_path,
                   out_path,
                   detection_path,
                   show_window=False):

    box_correction_ration = 1.07

    # Read the input image
    input_image = cv2.imread(in_path)

    detection_data = None
    with open(detection_path) as detection:
        detection_data = json.loads(detection.read())
        logging.info(detection_data)

    output_image = np.array(input_image)

    i = 0

    for box in detection_data:
        up_left = (int(box[0]), int(box[1]))
        down_right = (int(box[2]), int(box[3]))
        orginal_center = (int((box[0] + box[2])/2), int((box[1] + box[3])/2))
        corrected_up_left = (int(box[0]/box_correction_ration),
                             int(box[1]/box_correction_ration))
        corrected_down_right = (int(box[2]*box_correction_ration),
                                int(box[3]*box_correction_ration))
        output_image = cv2.rectangle(output_image,
                                     up_left,
                                     down_right,
                                     (0, 0, 255))
        output_image = cv2.rectangle(output_image,
                                     corrected_up_left,
                                     corrected_down_right,
                                     (0, 255, 0))
        output_image = cv2.circle(output_image,
                                  (orginal_center[0], orginal_center[1]),
                                  5,
                                  (0, 255, 0), -1)

        h = abs(corrected_down_right[1] - corrected_up_left[1])
        w = abs(corrected_down_right[0] - corrected_up_left[0])
        subimage = input_image[corrected_up_left[1]:corrected_up_left[1]+h,
                               corrected_up_left[0]:corrected_up_left[0]+w]

        psubimage = np.array(subimage)

        Z = subimage.reshape((-1, 3))
        Z = np.float32(Z)

        # Define criteria = ( type, max_iter = 10 , epsilon = 1.0 )
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    10,
                    1.0)

        # Set flags (Just to avoid line break in the code)
        flags = cv2.KMEANS_RANDOM_CENTERS

        # Apply KMeans
        compactness, labels, centers = cv2.kmeans(Z,
                                                  2,
                                                  None,
                                                  criteria,
                                                  10,
                                                  flags)

        center = np.uint8(centers)
        res = center[labels.flatten()]
        psubimage = res.reshape((psubimage.shape))

        kernel = np.ones((5, 5), np.uint8)
        psubimage = cv2.morphologyEx(psubimage, cv2.MORPH_CLOSE, kernel)

        # Chage to gray scale
        psubimage = cv2.cvtColor(psubimage, cv2.COLOR_BGR2GRAY)
        psubimage = cv2.GaussianBlur(psubimage, (5, 5), 0)

        ret, psubimage = cv2.threshold(psubimage,
                                       0,
                                       255,
                                       cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Detect the edges
        thresh = 100

        # Find the countours
        psubimage = cv2.Canny(psubimage, thresh, thresh*2, 3)
        cnts = cv2.findContours(np.array(psubimage),
                                cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)

        for c in cnts[1]:
            cv2.drawContours(subimage, [c], -1, (0, 255, 0), 2)

            ellipse = cv2.fitEllipse(c)

            cv2.ellipse(subimage, ellipse, (255, 0, 0), 2, 8)
            cv2.circle(subimage,
                       (int(ellipse[0][0]), int(ellipse[0][1])),
                       5,
                       (255, 0, 0),
                       -1)

            cv2.circle(output_image,
                       (int(ellipse[0][0]) + corrected_up_left[0],
                        int(ellipse[0][1] + corrected_up_left[1])),
                       5,
                       (255, 0, 0),
                       -1)

        i += 1
        cv2.imshow('Sub-picture Object ' + str(box[5]), subimage)

    # Show the window
    if show_window:
        cv2.imshow('Window', output_image)
        cv2.waitKey(0)

    # Write the image to the output path
    if out_path:
        cv2.imwrite(out_path, output_image)


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

    if '-d' in myargs:
        detection_path = myargs['-d']
    else:
        logging.info('No detection file path provided')
        exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']
    else:
        logging.info('No output image path provided')

    correct_center(in_path,
                   out_path,
                   detection_path,
                   show_window)
