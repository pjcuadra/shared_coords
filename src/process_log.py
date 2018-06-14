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
import re


detected_obj = dict()

supported_img = ["jpeg", "png"]

data_keywords = ["_guidancePosReady",
                 "gazeDirection",
                 "_lettucePos",
                 "lettuceNormal",
                 "New lettuce position"]

data_shared_coord_keywords = ["_hamPos",
                              "hamNormal",
                              "_breadPos",
                              "canContinue",
                              "Position of ham",
                              "Position of bread",
                              "Camera position when taking image",
                              "Origin point for shared coordinate system",
                              ]

data_shared_coord_keywords_matrix = ["Shared base",
                                     "Inverted shared base"]


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


def check_frame_start(line):
    """Verify if the line is actually a frame start line"""
    return '{"status": "success", "engine_id": "Sandwich"' in line


def get_next_frame_info(content, index):
    """Get the line where the next frame information starts"""

    i = index + 1

    while(i + 1 < len(content) and not check_frame_start(content[i])):
        i = i + 1

    return i


def get_frame_id(line):
    """Get the ID of the frame"""
    data = json.loads(line)
    return data['frame_id']


def get_frame_data_coords(line, json_data):
    """Get coordinates from the case x: a, y: b, z: c"""

    coords_s = line.split(",")

    for coord in coords_s:
        coord_s = coord.split(":")
        json_data[coord_s[0].strip()] = float(coord_s[1].strip())


def get_frame_data_coords_parentesis(line, json_data):
    """Get coordinates from the case (a, b, c)"""
    logging.debug(line)
    # Remove parentesis
    line = line[1:-1]
    coords_s = re.split(' |, |,', line)

    json_data['x'] = float(coords_s[0].strip())
    json_data['y'] = float(coords_s[1].strip())
    json_data['z'] = float(coords_s[2].strip())


def get_json_data(line, json_data):
    """
    Parse JSON like data from log file

    This function handles the following cases;

      * key: (a, b, c)
      * key: value
      * key: x: a, y: b, z: c

    """

    line_s = line.split(':')

    json_data[line_s[0]] = dict()

    if (len(line_s) == 2):
        # For the case were the data comes like - key: (a, b, c)
        if re.match("\(.*\)", line_s[1].strip()):
            get_frame_data_coords_parentesis(line_s[1].strip(),
                                             json_data[line_s[0]])
            return

        # For the normal case - key: value
        json_data[line_s[0]] = line_s[1].strip()
        return

    # For the case - key: x: a, y: b, z: c
    get_frame_data_coords(':'.join(line_s[1:]), json_data[line_s[0]])


def get_matrix(content):
    """Parse a matrix from log"""

    matrix = list(list())

    for line in content:
        line_s = line.split(" ")

        if len(line_s) == 1:
            break

        matrix.append(list())

        for val in line_s:
            matrix[-1].append(float(val))

    return matrix


def get_shared_coords(content):
    """Parse the shared coordinates from log"""

    json_data = dict()

    for idx, line in enumerate(content):

        for key in data_shared_coord_keywords_matrix:
            if key in line:
                json_data[key] = get_matrix(content[idx + 1:])

        for key in data_shared_coord_keywords:
            if key in line:
                get_json_data(line, json_data)

        if "New coordinate system" in line:
            line_s = line.split(":")
            json_data["New coordinate system"] = dict()

            new_line = ":".join(line_s[1:])

            line_s = re.split(",|, |:", new_line)

            i = 0
            while (i < len(line_s)):
                axis_name = line_s[i].strip()
                i += 1

                axis_val = ",".join(line_s[i:i+3])[1:]
                i += 3

                logging.debug(axis_val)

                axis_json = dict()

                get_frame_data_coords_parentesis(axis_val, axis_json)

                json_data["New coordinate system"][axis_name] = axis_json

    return json_data


def get_frame_data_info(content):
    """Get data of a single frame"""

    json_data = dict()
    shared = None

    for line in content:
        for key in data_keywords:
            if key in line:
                get_json_data(line, json_data)

        if "canContinue" in line:

            cc = dict()
            get_json_data(line, cc)

            if cc["canContinue"] in "True":
                logging.debug(cc["canContinue"])
                shared = get_shared_coords(content)

    return json_data, shared


def process_log(log_path, out_path=None):
    """Process an entire log file"""
    content = None
    out_path_full = None

    with open(log_path) as f:
        content = f.readlines()
        content = [x.strip() for x in content]

    if not content:
        return -1

    frame_data_idx = get_next_frame_info(content, 0)
    prev_frame_data_idx = 0

    if out_path:
        out_path_full = os.path.join(out_path, 'coords', 'hl_rc')
        if not os.path.exists(out_path_full):
            os.makedirs(out_path_full)

    # Get the data of each image
    while(frame_data_idx + 1 < len(content)):
        prev_frame_data_idx = frame_data_idx
        frame_data_idx = get_next_frame_info(content, frame_data_idx)

        id = get_frame_id(content[prev_frame_data_idx])

        logging.debug("Frame " + str(id) + " data found")
        logging.debug("   from line " + str(prev_frame_data_idx))
        logging.debug("   to line " + str(frame_data_idx))

        sub_content = content[prev_frame_data_idx:frame_data_idx]

        data, shared = get_frame_data_info(sub_content)

        if not out_path:
            continue

        file_path = os.path.join(out_path_full, str(id) + "_dl_coords.json")
        with open(file_path, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        if shared:
            file_path = os.path.join(out_path_full, "shared_coords.json")
            with open(file_path, 'w') as outfile:
                json.dump(shared, outfile, indent=4)

    return 0


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    in_path = None

    if '-v' in myargs:
        logging.basicConfig(level=logging.DEBUG)

    if '-i' in myargs:
        in_path = myargs['-i']
        logging.debug('Input log at ' + in_path)
    else:
        logging.error('No input log provided')
        exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']

    ret = process_log(in_path, out_path)
    exit(ret)
