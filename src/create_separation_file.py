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
import json
import os
import imghdr
import cv2
import cv2.aruco as aruco

supported_img = ["jpeg", "png"]

llevel_mapping = {'info': logging.INFO,
                  'warning': logging.WARNING,
                  'debug': logging.DEBUG,
                  'error': logging.ERROR}


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


def create_img_list(in_path):
    img_list = list()
    for filename in os.listdir(in_path):
        full_path = os.path.join(in_path, filename)
        if os.path.isdir(full_path):
            continue

        im_type = imghdr.what(full_path)
        if im_type in supported_img:
            img_list.append(filename)

    return img_list


def detect_sep_marker(img_file, marker_id):
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
    parameters = aruco.DetectorParameters_create()
    parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX

    input_image = cv2.imread(img_file)

    corners, ids, rejectedImgPoints = aruco.detectMarkers(input_image,
                                                          aruco_dict,
                                                          parameters=parameters
                                                          )

    if ids is None:
        return False

    if len(ids) == 0:
        return False

    if marker_id in ids:
        logging.info('Separation Marker Found in {}'.format(img_file))
        return True

    return False


def get_base_file(img_file):
    base = os.path.splitext(img_file)[0]
    return base


def is_within_sep_imgs(img_file, prev_pos, next_pos):
    curr_img_id = int(get_base_file(img_file))

    if curr_img_id >= next_pos:
        return False

    if curr_img_id <= prev_pos:
        return False

    return True


def create_separation_file(in_path, marker_id, out_path):
    ret = 0

    img_list = create_img_list(in_path)
    sep_imgs = list()
    sep_file_cont = {}
    pos_counter = 0
    prev_sep = 0

    for img_file in img_list:
        img_full = os.path.join(in_path, img_file)

        if detect_sep_marker(img_full, marker_id):
            sep_imgs.append(int(get_base_file(img_file)))

    sep_imgs.sort()

    logging.debug('Sorted Separation Images {}'.format(sep_imgs))

    prev_sep = sep_imgs[0]
    del sep_imgs[0]

    for next_sep in sep_imgs:
        tmp_list = list()

        for img_file in img_list:
            if is_within_sep_imgs(img_file, prev_sep, next_sep):
                tmp_list.append(img_file)

        if len(tmp_list) > 1:
            sep_file_cont[pos_counter] = tmp_list
            pos_counter += 1

        prev_sep = next_sep

    file_path = os.path.join(out_path, "sep.json")
    with open(file_path, 'w') as outfile:
        json.dump(sep_file_cont, outfile, indent=4)

    return ret


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    in_path = None
    separate_file = None
    marker_id = 1

    if '-l' in myargs:
        logging.basicConfig(level=llevel_mapping[myargs['-l']])
    else:
        logging.basicConfig(level=logging.WARNING)

    if '-i' in myargs:
        in_path = myargs['-i']
        logging.info('Input directory at ' + in_path)
    else:
        logging.error('No input directory provided')
        exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']
    else:
        logging.error('No output directory provided')
        exit(-1)

    if '-m' in myargs:
        marker_id = int(myargs['-m'])

    ret = create_separation_file(in_path, marker_id, out_path)
    exit(ret)
