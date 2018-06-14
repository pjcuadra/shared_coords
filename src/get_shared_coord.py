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
import cv2.aruco as aruco


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


def calc_3d_location_camera(rvec, tvec, marker_3d):
    rotation_matrix, d = cv2.Rodrigues(rvec)

    logging.debug(rotation_matrix)

    reversed_rotation_matrix = np.linalg.inv(rotation_matrix)
    logging.debug(reversed_rotation_matrix)

    # Calculate the reversed tranlation vector
    reversed_translation = np.matmul(reversed_rotation_matrix,
                                     -np.transpose(tvec))

    # Calculate the normal vector by projecting the point (0, 0, 1)
    camera_3d = cv2.gemm(reversed_rotation_matrix,
                         marker_3d,
                         1,
                         reversed_translation,
                         1)

    return camera_3d


def draw_marker_axis(in_img, intrinsics, distortion, rvecs, tvecs):

    if len(rvecs) == 1:
        aruco.drawAxis(in_img,
                       intrinsics,
                       distortion,
                       rvecs,
                       tvecs,
                       0.1)
        return

    for i in range(len(rvecs)):
        aruco.drawAxis(in_img,
                       intrinsics,
                       distortion,
                       rvecs[i],
                       tvecs[i],
                       0.1)


def get_coordinates(in_path,
                    camera,
                    out_path=None,
                    parameters_path=None,
                    show_window=False,
                    marker_size=0.071):
    fs = cv2.FileStorage(camera, cv2.FILE_STORAGE_READ)

    # Read the input image
    input_image = cv2.imread(in_path)

    # Get the camera model
    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    logging.debug('Camera Intrinsics: ')
    logging.debug(intrinsics.mat())
    logging.debug('Camera Distortion: ')
    logging.debug(distortion.mat())

    return get_coordinates_system(input_image,
                                  intrinsics,
                                  distortion,
                                  out_path,
                                  parameters_path,
                                  show_window,
                                  marker_size)


def get_coordinates_system(input_image,
                           intrinsics,
                           distortion,
                           out_path=None,
                           parameters_path=None,
                           show_window=False,
                           marker_size=0.071):

    # Detect the Aruco Markers
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
    parameters = aruco.DetectorParameters_create()
    parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX

    corners, ids, rejectedImgPoints = aruco.detectMarkers(input_image,
                                                          aruco_dict,
                                                          intrinsics.mat(),
                                                          distortion.mat(),
                                                          parameters=parameters
                                                          )
    if len(corners) == 0:
        return None, None, None

    logging.debug("Detected Markers: ")
    logging.debug(" -> Ids: ")
    logging.debug(ids)
    logging.debug(" -> Corners: ")
    logging.debug(corners)
    logging.debug(" -> Centers: ")

    centers = list()

    # Calculate the centers
    for marker_corners in corners:
        logging.debug('Marker Corners -> {}'.format(marker_corners[0]))
        logging.debug('Marker Center -> {}'.format(np.mean(marker_corners[0],
                                                           axis=0).tolist()))
        centers.append(np.mean(marker_corners[0],
                               axis=0).tolist())

    logging.debug('Centers {}'.format(centers))

    # Detect the camera pose
    rvecs, tvecs, n = aruco.estimatePoseSingleMarkers(corners,
                                                      marker_size,
                                                      intrinsics.mat(),
                                                      distortion.mat())

    logging.debug("Camera Pose: ")
    logging.debug(" -> Rotation Vector: ")
    logging.debug(rvecs)
    logging.debug(" -> Translation Vector: ")
    logging.debug(tvecs)

    rrvecs = list()
    rtvecs = list()
    nvecs = list()
    xvecs = list()

    # Calculte normal vector for each marker
    for i in range(0, len(rvecs)):
        # Reverse the pose
        # Calculate the reversed Rotation matrix
        rotation_matrix, d = cv2.Rodrigues(rvecs[i])

        logging.debug(rotation_matrix)

        reversed_rotation_matrix = np.linalg.inv(rotation_matrix)
        logging.debug(reversed_rotation_matrix)

        # Calculate the reversed tranlation vector
        reversed_translation = np.matmul(reversed_rotation_matrix,
                                         -np.transpose(tvecs[i]))

        rod, d = cv2.Rodrigues(reversed_rotation_matrix)
        rrvecs.append(np.transpose(rod))
        rtvecs.append(np.transpose(reversed_translation))

        normal = calc_3d_location_camera(rvecs[i], tvecs[i], (0, 0, 1))

        normal -= reversed_translation

        nvecs.append(normal)

    # Caculate the x axis unit vector
    for i in range(0, len(rvecs)):
        # Reverse the pose
        # Calculate the reversed Rotation matrix
        rotation_matrix, d = cv2.Rodrigues(rvecs[i])

        logging.debug(rotation_matrix)

        reversed_rotation_matrix = np.linalg.inv(rotation_matrix)
        logging.debug(reversed_rotation_matrix)

        # Calculate the reversed tranlation vector
        reversed_translation = np.matmul(reversed_rotation_matrix,
                                         -np.transpose(tvecs[i]))

        rod, d = cv2.Rodrigues(reversed_rotation_matrix)
        rrvecs.append(np.transpose(rod))
        rtvecs.append(np.transpose(reversed_translation))

        xaxis = calc_3d_location_camera(rvecs[i], tvecs[i], (1, 0, 0))

        xaxis -= reversed_translation

        xvecs.append(xaxis)

    logging.debug("Marker Pose: ")
    logging.debug(" -> Rotation Vector: ")
    logging.debug(rrvecs)
    logging.debug(" -> Translation Vector: ")
    logging.debug(rtvecs)

    logging.debug("Normal Vectors: ")
    logging.debug(nvecs)

    # Prepare the output image
    output_image = aruco.drawDetectedMarkers(input_image, corners)
    draw_marker_axis(input_image, intrinsics.mat(), distortion.mat(),
                     rvecs,
                     tvecs)

    # Show the window
    if show_window:
        cv2.imshow('Window', output_image)
        cv2.waitKey(0)

    # Write the image to the output path
    if out_path:
        cv2.imwrite(out_path, output_image)

    # Add data to JSON
    json_content = dict()

    json_content["ids"] = ids.tolist()
    json_content["m_c"] = list()
    json_content["m_c_3d"] = list()
    json_content["n_vector"] = list()
    json_content["xaxis_vector"] = list()
    json_content["rvecs"] = list()
    json_content["tvecs"] = list()

    for i in range(0, len(rvecs)):

        # logging.warning(tvecs[i])
        json_content["m_c"].append(centers[i])
        json_content["m_c_3d"].append(rtvecs[i].tolist())
        json_content["n_vector"].append(nvecs[i].tolist())
        json_content["xaxis_vector"].append(xvecs[i].tolist())
        json_content["rvecs"].append(rvecs[i].tolist())
        json_content["tvecs"].append(tvecs[i].tolist())

    logging.debug(json.dumps(json_content))

    if parameters_path:
        with open(parameters_path, 'w') as outfile:
            json.dump(json_content, outfile, indent=4)

    return ids, corners, json_content


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    in_path = None
    params_path = None
    show_window = False
    marker_size = 0.071

    if '-v' in myargs:
        logging.basicConfig(level=logging.debug)

    if '-s' in myargs:
        show_window = True

    if '-i' in myargs:
        in_path = myargs['-i']
        logging.debug('Input image at ' + in_path)
    else:
        logging.error('No input image provided')
        exit(-1)

    if '-p' in myargs:
        params_path = myargs['-p']
        logging.debug('Parameters to be writte to ' + params_path)

    if '-c' in myargs:
        camera = myargs['-c']
        logging.debug('Camera Distortion model at ' + camera)
    else:
        logging.error('No Camera Distortion model provided')
        exit(-1)

    if '-o' in myargs:
        out_path = myargs['-o']
    else:
        logging.debug('No output image path provided')

    if '-m' in myargs:
        marker_size = myargs['-m']

    get_coordinates(in_path,
                    camera,
                    out_path,
                    params_path,
                    show_window,
                    float(marker_size))
