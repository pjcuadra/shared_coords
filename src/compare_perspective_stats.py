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


def xyz_to_numpy(xyz):
    return np.array([xyz['x'], xyz['y'], xyz['z']])


def uvd_to_numpy(uvd):
    return np.array([uvd['u'], uvd['v'], uvd['depth']])


def get_stats(stats_file_path):
    if not os.path.exists(stats_file_path):
        return None

    json_data = open(stats_file_path).read()
    json_data = json.loads(json_data)

    return json_data


def is_marker_coords(stats_key):
    return '_marker' in stats_key


def compare_coords_sets(set_0, set_1):

    deltas = list()

    for d0 in set_0:
        for d1 in set_1:
            d0_a = np.array(d0)
            d1_a = np.array(d1)
            delta = d0_a - d1_a
            deltas.append(delta)

    res = {}

    res['deltas'] = deltas
    res['mean'] = np.mean(deltas,
                          axis=0).tolist()
    res['std_dev'] = np.std(deltas,
                            axis=0).tolist()
    res['max'] = np.max(deltas,
                        axis=0).tolist()
    res['min'] = np.min(deltas,
                        axis=0).tolist()

    for idx, val in enumerate(deltas):
        res['deltas'][idx] = val.tolist()

    return res


def compare_marker_stats(stats_0, stats_1):
    all_obj_res = {}

    for key, value in stats_0.items():
        if key not in stats_1:
            continue

        if not is_marker_coords(key):
            continue

        stats_0_vals = value["all"]
        stats_1_vals = stats_1[key]["all"]

        msg = 'Object {}: all_0: {} all_1: {}'.format(key,
                                                      stats_0_vals,
                                                      stats_1_vals)
        logging.debug(msg)

        res = compare_coords_sets(stats_0_vals, stats_1_vals)

        all_obj_res[key] = res

    return all_obj_res


def compare_hl_rc_stats(stats_0, stats_1):
    all_obj_res = {}

    if 'lettuce' not in stats_0:
        return all_obj_res

    if 'lettuce' not in stats_1:
        return all_obj_res

    stats_0_vals = stats_0['lettuce']['all']
    stats_1_vals = stats_1['lettuce']['all']

    msg = 'Object {}: all_0: {} all_1: {}'.format('lettuce',
                                                  stats_0_vals,
                                                  stats_1_vals)
    logging.debug(msg)

    res = compare_coords_sets(stats_0_vals, stats_1_vals)

    all_obj_res['lettuce'] = res

    return all_obj_res


def compare_hl_rc_coords(in_path_0, in_path_1, out_path):
    stats_file_0 = os.path.join(in_path_0, 'hl_rc.json')
    stats_file_1 = os.path.join(in_path_1, 'hl_rc.json')
    stats_out_path = os.path.join(out_path, 'comparison_rc.json')

    if not os.path.exists(stats_file_0):
        logging.error('Stats file not found - {}'.format(stats_file_0))
        return -1
    if not os.path.exists(stats_file_1):
        logging.error('Stats file not found - {}'.format(stats_file_1))
        return -1

    stats_0 = get_stats(stats_file_0)
    stats_1 = get_stats(stats_file_1)

    res = compare_hl_rc_stats(stats_0, stats_1)

    with open(stats_out_path, 'w') as f:
        json.dump(res, f, indent=4)

    return 0


def compare_marker_coords(in_path_0, in_path_1, out_path):
    stats_file_0 = os.path.join(in_path_0, 'marker.json')
    stats_file_1 = os.path.join(in_path_1, 'marker.json')
    stats_out_path = os.path.join(out_path, 'comparison_marker.json')

    if not os.path.exists(stats_file_0):
        logging.error('Stats file not found - {}'.format(stats_file_0))
        return -1
    if not os.path.exists(stats_file_1):
        logging.error('Stats file not found - {}'.format(stats_file_1))
        return -1

    stats_0 = get_stats(stats_file_0)
    stats_1 = get_stats(stats_file_1)

    res = compare_marker_stats(stats_0, stats_1)

    with open(stats_out_path, 'w') as f:
        json.dump(res, f, indent=4)

    return 0


def compare_perspective_stats(in_path_0, in_path_1, out_path):
    stats_in_path_0 = os.path.join(in_path_0, 'stats')
    stats_in_path_1 = os.path.join(in_path_1, 'stats')

    if not os.path.exists(stats_in_path_0):
        logging.error('Stats directory not found - {}'.format(stats_in_path_0))
        return -1

    if not os.path.exists(stats_in_path_1):
        logging.error('Stats directory not found - {}'.format(stats_in_path_1))
        return -1

    ret = compare_marker_coords(stats_in_path_0, stats_in_path_1, out_path)
    ret |= compare_hl_rc_coords(stats_in_path_0, stats_in_path_1, out_path)

    return ret


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    in_path_0 = None
    in_path_1 = None
    separate_file = None
    position = ''

    if '-l' in myargs:
        logging.basicConfig(level=llevel_mapping[myargs['-l']])
    else:
        logging.basicConfig(level=logging.WARNING)

    if '-i' in myargs:
        in_path_0 = myargs['-i']
        logging.info('Input directory at ' + in_path_0)
    else:
        logging.error('No input directory provided')
        exit(-1)

    if '-r' in myargs:
        in_path_1 = myargs['-r']
        logging.info('Input directory at ' + in_path_1)
    else:
        logging.error('No input directory provided')
        exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']
    else:
        logging.error('No output directory provided')
        exit(-1)

    if '-p' in myargs:
        position = myargs['-p']

    in_path_0 = os.path.join(in_path_0, position)
    in_path_1 = os.path.join(in_path_1, position)
    out_path = os.path.join(out_path, position)

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    ret = compare_perspective_stats(in_path_0, in_path_1, out_path)
    exit(ret)
