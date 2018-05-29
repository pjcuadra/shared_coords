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
from shutil import copyfile
import logging
import json
import os
# import re


detected_obj = dict()

supported_img = ["jpeg", "png"]


def getopts(argv):
    """Parse the command line options"""
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


def copy_augmented_images(pic_name, in_path, position_path):
    """Copy Augmented Images to destination path"""
    new_filename, _ = os.path.splitext(pic_name)
    new_filename += "_augmented.jpg"
    aug_path = os.path.join(position_path, 'augmented')
    src_aug_path_full = os.path.join(in_path, 'augmented', new_filename)
    dst_aug_path_full = os.path.join(aug_path, new_filename)

    if not os.path.exists(aug_path):
        os.makedirs(aug_path)

    copyfile(src_aug_path_full, dst_aug_path_full)


def copy_sub_coords_files(pic_name, in_path, position_path, sub_dir,
                          file_append):
    new_filename, _ = os.path.splitext(pic_name)
    new_filename += file_append
    coords_path = os.path.join(position_path, sub_dir)
    src_coords_path_full = os.path.join(in_path, sub_dir, new_filename)
    dst_coords_path_full = os.path.join(coords_path, new_filename)

    if not os.path.exists(coords_path):
        os.makedirs(coords_path)

    copyfile(src_coords_path_full, dst_coords_path_full)


def copy_hl_coords_files(pic_name, in_path, position_path):
    copy_sub_coords_files(pic_name,
                          in_path,
                          position_path,
                          'hl_dl',
                          '_camera.json')


def copy_hl_rc_coords_files(pic_name, in_path, position_path):
    copy_sub_coords_files(pic_name,
                          in_path,
                          position_path,
                          'hl_rc',
                          '_dl_coords.json')
    src_coords_path_full = os.path.join(in_path,
                                        'hl_rc',
                                        'shared_coords.json')
    dst_coords_path_full = os.path.join(position_path,
                                        'hl_rc',
                                        'shared_coords.json')
    copyfile(src_coords_path_full, dst_coords_path_full)


def copy_marker_coords_files(pic_name, in_path, position_path):
    copy_sub_coords_files(pic_name,
                          in_path,
                          position_path,
                          'marker',
                          '_camera.json')
    copy_sub_coords_files(pic_name,
                          in_path,
                          position_path,
                          'marker',
                          '_marker.json')


def copy_coords_files(pic_name, in_path, position_path):

    coords_path = os.path.join(position_path, 'coords')
    src_coords_path_full = os.path.join(in_path, 'coords')
    dst_coords_path_full = os.path.join(coords_path)

    if not os.path.exists(coords_path):
        os.makedirs(coords_path)

    copy_hl_coords_files(pic_name,
                         src_coords_path_full,
                         dst_coords_path_full)
    copy_hl_rc_coords_files(pic_name,
                            src_coords_path_full,
                            dst_coords_path_full)
    copy_marker_coords_files(pic_name,
                             src_coords_path_full,
                             dst_coords_path_full)


def separate_by_position(json_info, in_path, out_path):
    """
    Go thru the JSON separation file and separates the data as specified
    """

    with open(json_info) as f:
        json_data = f.read()

    data = json.loads(json_data)

    for key, value in data.items():

        out_path_full = os.path.join(out_path, key)

        if not os.path.exists(out_path_full):
            os.makedirs(out_path_full)

        for pic in value:

            filename, _ = os.path.splitext(pic)

            # Copy the image
            src_path_full = os.path.join(in_path, pic)
            dst_path_full = os.path.join(out_path_full, pic)
            copyfile(src_path_full, dst_path_full)

            # Copy detection file
            tmp_filename = filename + "_detection.txt"

            src_path_full = os.path.join(in_path, tmp_filename)
            dst_path_full = os.path.join(out_path_full, tmp_filename)
            copyfile(src_path_full, dst_path_full)

            # Copy json file
            tmp_filename = filename + ".json"

            src_path_full = os.path.join(in_path, tmp_filename)
            dst_path_full = os.path.join(out_path_full, tmp_filename)
            copyfile(src_path_full, dst_path_full)

            # Copy answer json file
            tmp_filename = filename + "_answer.json"

            src_path_full = os.path.join(in_path, tmp_filename)
            dst_path_full = os.path.join(out_path_full, tmp_filename)
            copyfile(src_path_full, dst_path_full)

            # Augmented images
            copy_augmented_images(pic, in_path, out_path_full)
            copy_coords_files(pic, in_path, out_path_full)

    return 0


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    in_path = None
    separate_file = None

    if '-v' in myargs:
        logging.basicConfig(level=logging.DEBUG)

    if '-i' in myargs:
        in_path = myargs['-i']
        logging.debug('Input directory at ' + in_path)
    else:
        logging.error('No input directory provided')
        exit(-1)

    if '-s' in myargs:
        separate_file = myargs['-s']
        logging.debug('Input separete file at ' + separate_file)
    else:
        logging.error('No input separete file provided')
        exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']
    else:
        logging.error('No output directory provided')
        exit(-1)

    ret = separate_by_position(separate_file, in_path, out_path)
    exit(ret)
