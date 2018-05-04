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


def get_coordinates(in_path,
                    out_path,
                    camera,
                    parameters_path=None,
                    show_window=False,
                    marker_size=0.071):
    fs = cv2.FileStorage(camera, cv2.FILE_STORAGE_READ)

    # Read the input image
    input_image = cv2.imread(in_path)

    # Get the camera model
    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    logging.info('Camera Intrinsics: ')
    logging.info(intrinsics.mat())
    logging.info('Camera Distortion: ')
    logging.info(distortion.mat())

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
    logging.info("Detected Markers: ")
    logging.info(" -> Ids: ")
    logging.info(ids)
    logging.info(" -> Corners: ")
    logging.info(corners)
    logging.info(" -> Centers: ")

    centers = list()

    # Calculate the centers
    for marker_corners in corners[0]:
        sum = [0, 0]
        # logging.info(marker_corners)
        for corner in marker_corners:
            sum += corner

        # logging.info(sum/4)
        centers.append(sum/4)

    logging.info(centers)

    # Detect the camera pose
    rvecs, tvecs, n = aruco.estimatePoseSingleMarkers(corners,
                                                      marker_size,
                                                      intrinsics.mat(),
                                                      distortion.mat())

    logging.info("Camera Pose: ")
    logging.info(" -> Rotation Vector: ")
    logging.info(rvecs)
    logging.info(" -> Translation Vector: ")
    logging.info(tvecs)

    rrvecs = list()
    rtvecs = list()
    nvecs = list()

    for i in range(0, len(rvecs)):
        # Reverse the pose
        # Calculate the reversed Rotation matrix
        rotation_matrix, d = cv2.Rodrigues(rvecs[i])

        logging.info(rotation_matrix)

        reversed_rotation_matrix = np.linalg.inv(rotation_matrix)
        logging.info(reversed_rotation_matrix)

        # Calculate the reversed tranlation vector
        reversed_translation = np.matmul(reversed_rotation_matrix,
                                         -np.transpose(tvecs[i]))

        rod, d = cv2.Rodrigues(reversed_rotation_matrix)
        rrvecs.append(np.transpose(rod))
        rtvecs.append(np.transpose(reversed_translation))

        # Calculate the normal vector by projecting the point (0, 0, 1)
        normal = cv2.gemm(reversed_rotation_matrix,
                          (0, 0, 1),
                          1,
                          reversed_translation,
                          1)

        normal -= reversed_translation

        nvecs.append(normal)

    logging.info("Marker Pose: ")
    logging.info(" -> Rotation Vector: ")
    logging.info(rrvecs)
    logging.info(" -> Translation Vector: ")
    logging.info(rtvecs)

    logging.info("Normal Vectors: ")
    logging.info(nvecs)

    # Prepare the output image
    output_image = aruco.drawDetectedMarkers(input_image, corners)
    aruco.drawAxis(output_image,
                   intrinsics.mat(),
                   distortion.mat(),
                   rvecs,
                   tvecs,
                   0.1)
    cv2.circle(output_image,
               (int(centers[0][0]), int(centers[0][1])),
               5,
               (0, 0, 255))

    # Show the window
    if show_window:
        cv2.imshow('Window', output_image)
        cv2.waitKey(0)

    # Write the image to the output path
    if out_path:
        cv2.imwrite(out_path, output_image)

    # Add data to JSON
    if not parameters_path:
        return

    json_content = dict()

    json_content["ids"] = ids.tolist()
    json_content["m_c"] = centers
    json_content["m_c_3d"] = rtvecs
    json_content["n_vector"] = nvecs

    for i in range(0, len(rvecs)):
        json_content["m_c"][i] = json_content["m_c"][i].tolist()
        json_content["m_c_3d"][i] = json_content["m_c_3d"][i].tolist()
        json_content["n_vector"][i] = json_content["n_vector"][i].tolist()

    logging.info(json.dumps(json_content))

    with open(parameters_path, 'w') as outfile:
        json.dump(json_content, outfile)


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    id = 23
    params_path = None
    show_window = False
    marker_size = 200

    if '-v' in myargs:
        logging.basicConfig(level=logging.INFO)

    if '-s' in myargs:
        show_window = True

    if '-i' in myargs:
        id = int(myargs['-i'])

    logging.info('Marker Id ' + str(id))

    if '-o' in myargs:
        out_path = myargs['-o']
    else:
        logging.info('No output image path provided')

    if '-m' in myargs:
        marker_size = int(myargs['-m'])

    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
    markerImage = cv2.aruco.drawMarker(aruco_dict, id, marker_size, 1)

    # Show the window
    if show_window:
        cv2.imshow('Window', markerImage)
        cv2.waitKey(0)

    if out_path:
        cv2.imwrite(out_path, markerImage)
