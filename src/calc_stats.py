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
import numpy as np
# import re


detected_obj = dict()

supported_img = ["jpeg", "png"]


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


def xyz_to_numpy(xyz):
    return np.array([xyz['x'], xyz['y'], xyz['z']])


def uvd_to_numpy(uvd):
    return np.array([uvd['u'], uvd['v'], uvd['depth']])


def calc_hl_dl_stats(in_path, out_path):
    hl_dl_in_path = os.path.join(in_path, 'coords', 'hl_dl')
    stats_out_path = os.path.join(out_path, 'hl_dl.json')

    pos = dict()
    pos['lettuce'] = list()
    pos['ham'] = list()
    pos['bread'] = list()

    pos['lettuce_o'] = list()
    pos['ham_o'] = list()
    pos['bread_o'] = list()

    pos['lettuce_homo'] = list()
    pos['ham_homo'] = list()
    pos['bread_homo'] = list()

    for filename in os.listdir(hl_dl_in_path):
        hl_dl_in_path_full = os.path.join(hl_dl_in_path, filename)
        logging.debug('Analyzing {}'.format(hl_dl_in_path_full))

        with open(hl_dl_in_path_full) as f:
            json_data = json.loads(f.read())

        for key, val in json_data.items():
            logging.debug('Gathering {} - {}'.format(key, val))
            if '_o' in key:
                pos[key].append(uvd_to_numpy(val['location']))
                continue

            pos[key].append(xyz_to_numpy(val['location']))

    njson = dict()

    for key, val in json_data.items():
        njson[key] = dict() 
        njson[key]["mean"] = np.mean(pos[key],
                                     axis=0).tolist()
        njson[key]["std_dev"] = np.std(pos[key],
                                       axis=0).tolist()
        njson[key]["max"] = np.max(pos[key],
                                   axis=0).tolist()
        njson[key]["min"] = np.min(pos[key],
                                   axis=0).tolist()

        for idx, sval in enumerate(pos[key]):
            pos[key][idx] = sval.tolist()

        njson[key]['all'] = pos[key]

    with open(stats_out_path, 'w') as f:
        json.dump(njson, f, indent=4)


def calc_hl_rc_stats(in_path, out_path):
    hl_rc_in_path = os.path.join(in_path, 'coords', 'hl_rc')
    stats_out_path = os.path.join(out_path, 'hl_rc.json')

    lettuce_pos = list()

    for filename in os.listdir(hl_rc_in_path):

        if "shared_coords.json" in filename:
            continue

        hl_rc_in_path_full = os.path.join(hl_rc_in_path, filename)

        with open(hl_rc_in_path_full) as f:
            json_data = json.loads(f.read())

        if 'New lettuce position' in json_data:
            # logging.debug(json_data['New lettuce position'])
            lettuce_pos.append(xyz_to_numpy(json_data['New lettuce position']))

    json_data = dict()
    json_data['lettuce'] = dict()

    json_data['lettuce']["mean"] = np.mean(lettuce_pos, axis=0).tolist()
    json_data['lettuce']["std_dev"] = np.std(lettuce_pos, axis=0).tolist()
    json_data['lettuce']["max"] = np.max(lettuce_pos, axis=0).tolist()
    json_data['lettuce']["min"] = np.min(lettuce_pos, axis=0).tolist()

    for idx, pos in enumerate(lettuce_pos):
        lettuce_pos[idx] = pos.tolist()

    json_data['lettuce']["all"] = lettuce_pos

    with open(stats_out_path, 'w') as f:
        json.dump(json_data, f, indent=4)

    # logging.debug(np.min(lettuce_pos, axis=0))


def calc_marker_stats(in_path, out_path):
    coords_in_path = os.path.join(in_path, 'coords', 'marker')
    stats_out_path = os.path.join(out_path, 'marker.json')

    camera_pos = dict()
    camera_pos['lettuce'] = list()
    camera_pos['bread'] = list()
    camera_pos['ham'] = list()

    marker_pos = dict()
    marker_pos['lettuce'] = list()
    marker_pos['bread'] = list()
    marker_pos['ham'] = list()

    for filename in os.listdir(coords_in_path):

        if '_marker.json' not in filename:
            continue

        coords_in_path_full = os.path.join(coords_in_path, filename)

        with open(coords_in_path_full) as f:
            json_data = json.loads(f.read())

        for key, val in json_data.items():
            data_array = np.array(val['camera_location'])
            camera_pos[key].append(data_array)
            data_array = np.array(val['marker_location'])
            marker_pos[key].append(data_array)

    json_data = dict()

    for key, val in camera_pos.items():
        if len(val) == 0:
            continue

        key_cam = key + "_cam"
        json_data[key_cam] = dict()
        json_data[key_cam]["mean"] = np.mean(val, axis=0).tolist()
        json_data[key_cam]["std_dev"] = np.std(val, axis=0).tolist()
        json_data[key_cam]["max"] = np.max(val, axis=0).tolist()
        json_data[key_cam]["min"] = np.min(val, axis=0).tolist()

        for idx, pos in enumerate(val):
            val[idx] = pos.tolist()

        json_data[key_cam]['all'] = val

    for key, val in marker_pos.items():
        if len(val) == 0:
            continue

        key_marker = key + "_marker"
        json_data[key_marker] = dict()
        json_data[key_marker]["mean"] = np.mean(val, axis=0).tolist()
        json_data[key_marker]["std_dev"] = np.std(val, axis=0).tolist()
        json_data[key_marker]["max"] = np.max(val, axis=0).tolist()
        json_data[key_marker]["min"] = np.min(val, axis=0).tolist()

        for idx, pos in enumerate(val):
            val[idx] = pos.tolist()

        json_data[key_marker]['all'] = val

    with open(stats_out_path, 'w') as f:
        json.dump(json_data, f, indent=4)


def calc_stats(in_path, out_path):
    stats_out_path = os.path.join(out_path, 'stats')

    if not os.path.exists(stats_out_path):
        os.makedirs(stats_out_path)

    calc_hl_rc_stats(in_path, stats_out_path)

    calc_hl_dl_stats(in_path, stats_out_path)

    calc_marker_stats(in_path, stats_out_path)

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
        out_path = in_path
        logging.info('Input directory at ' + in_path)
    else:
        logging.error('No input directory provided')
        exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']

    ret = calc_stats(in_path, out_path)
    exit(ret)
