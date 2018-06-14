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
import imghdr
import os
from get_shared_coord import get_coordinates, calc_3d_location_camera
import math

detected_obj = dict()

supported_img = ["jpeg", "png"]

object_name_map = {3.0: "ham",
                   4.0: "lettuce",
                   8.0: "bread"}

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


def get_obj_locations_marker_sys(in_path, img_file, camera, params,
                                 corners, ids, marker_size=0.071):
    marker_pixel_size = 150
    pixels_per_cm = marker_pixel_size / (marker_size * 100)
    pixels_per_m = pixels_per_cm * 100
    detection_data = get_detection_data(in_path, img_file)
    img_path = os.path.join(in_path, img_file)
    marker_json_file = get_base_file(img_file) + "_marker.json"
    obj_detect_coords_path = os.path.join(in_path,
                                          "coords",
                                          "marker",
                                          marker_json_file)
    marker_height = 0.01
    lettuce_height = 0.018
    out_img_scale = 2

    sys_corners, id_m, idx_m = get_marker_sys_corners(ids, corners)

    logging.debug("Selected marker id is {}".format(id_m))

    fs = cv2.FileStorage(camera, cv2.FILE_STORAGE_READ)

    # Get the camera model
    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    input_image = cv2.imread(img_path)

    height, width, channels = input_image.shape

    center_x = int((out_img_scale * width)/2)
    center_y = int((out_img_scale * height)/2)

    # Rectify the image
    rectified_marker_corners = np.array([[(center_x - marker_pixel_size/2),
                                         (center_y + marker_pixel_size/2)],
                                         [(center_x + marker_pixel_size/2),
                                          (center_y + marker_pixel_size/2)],
                                         [(center_x + marker_pixel_size/2),
                                          (center_y - marker_pixel_size/2)],
                                         [(center_x - marker_pixel_size/2),
                                          (center_y - marker_pixel_size/2)]])
    newCamMatrix, r = cv2.getOptimalNewCameraMatrix(intrinsics.mat(),
                                                    distortion.mat(),
                                                    (width, height),
                                                    1,
                                                    (width, height))

    # logging.warning(input_image)
    undistortedMarkersCorners = sys_corners
    undistortedMarkersCorners = cv2.undistortPoints(undistortedMarkersCorners,
                                                    intrinsics.mat(),
                                                    distortion.mat(),
                                                    P=newCamMatrix)

    H_plane, _ = cv2.findHomography(undistortedMarkersCorners,
                                    rectified_marker_corners,
                                    cv2.RANSAC)

    logging.debug('Homography Plane -> {}'.format(H_plane))

    second_marker_corners = np.array([[(-marker_size/2),
                                       (marker_size/2),
                                       marker_height],
                                      [(marker_size/2),
                                       (marker_size/2),
                                       marker_height],
                                      [(marker_size/2),
                                       (-marker_size/2),
                                       marker_height],
                                      [(-marker_size/2),
                                       (-marker_size/2),
                                       marker_height]])
    lettuce_corners = np.array([[(-marker_size/2),
                                 (marker_size/2),
                                 lettuce_height],
                                [(marker_size/2),
                                 (marker_size/2),
                                 lettuce_height],
                                [(marker_size/2),
                                 (-marker_size/2),
                                 lettuce_height],
                                [(-marker_size/2),
                                 (-marker_size/2),
                                 lettuce_height]])

    undistortedMarkersCorners = cv2.projectPoints(second_marker_corners,
                                                  np.array(
                                                   params['rvecs'][idx_m]),
                                                  np.array(
                                                   params['tvecs'][idx_m]),
                                                  intrinsics.mat(),
                                                  distortion.mat())
    undistortedMarkersCorners = cv2.undistortPoints(
                                  undistortedMarkersCorners[0],
                                  intrinsics.mat(),
                                  distortion.mat(),
                                  P=newCamMatrix)

    H_marker, _ = cv2.findHomography(undistortedMarkersCorners,
                                     rectified_marker_corners,
                                     cv2.RANSAC)

    logging.debug('Homography Marker-> {}'.format(H_marker))

    undistortedMarkersCorners = cv2.projectPoints(lettuce_corners,
                                                  np.array(
                                                   params['rvecs'][idx_m]),
                                                  np.array(
                                                   params['tvecs'][idx_m]),
                                                  intrinsics.mat(),
                                                  distortion.mat())
    undistortedMarkersCorners = cv2.undistortPoints(
                                 undistortedMarkersCorners[0],
                                 intrinsics.mat(),
                                 distortion.mat(),
                                 P=newCamMatrix)

    H_lettuce, _ = cv2.findHomography(undistortedMarkersCorners,
                                      rectified_marker_corners,
                                      cv2.RANSAC)

    logging.debug('Homography Marker-> {}'.format(H_marker))

    data = dict()

    for idx, id in enumerate(ids):
        if check_marker_sys(id):
            continue

        logging.debug('Corners {}'.format(corners[idx]))
        obj_center = np.mean(corners[idx],
                             axis=1)
        obj_center = np.array([obj_center])

        obj_center = cv2.undistortPoints(obj_center,
                                         intrinsics.mat(),
                                         distortion.mat(),
                                         P=newCamMatrix)
        # obj_center = np.transpose(obj_center)
        # obj_center = np.array([[]])

        logging.debug('Center {}'.format(obj_center))

        # Obtain the 2D location with respect to the marker
        location_2d = cv2.perspectiveTransform(obj_center, H_marker)
        location_2d -= np.array([[center_x, center_y]])
        location_2d = location_2d / pixels_per_m

        x_marker_coord = location_2d.item(0)
        y_marker_coord = location_2d.item(1)

        location_3d = np.array([[x_marker_coord, y_marker_coord, 0]])
        data["lettuce_maker"] = dict()
        data["lettuce_maker"]["marker_location"] = location_3d.tolist()

    with open(obj_detect_coords_path, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    if not detection_data:
        return

    for box in detection_data:
        obj_center = np.array([[(box[0] + box[2])/2,
                               (box[1] + box[3])/2]], dtype='float32')
        obj_center = np.array([obj_center])

        # logging.debug('Center {}'.format(obj_center))

        # Obtain the 2D location with respect to the marker
        location_2d = cv2.perspectiveTransform(obj_center, H_lettuce)
        location_2d -= np.array([[center_x, center_y]])
        location_2d = location_2d / pixels_per_m

        x_marker_coord = location_2d.item(0)
        y_marker_coord = location_2d.item(1)

        location_3d = np.array([[x_marker_coord, y_marker_coord, 0]])

        obj_name = object_name_map[box[5]]
        data[obj_name] = dict()
        data[obj_name]["dl_center"] = obj_center.tolist()
        data[obj_name]["marker_location"] = location_3d.tolist()

        point_3d = calc_3d_location_camera(np.array(params['rvecs'][0]),
                                           np.array(params['tvecs'][0]),
                                           tuple(map(tuple, location_3d))[0])

        data[obj_name]["camera_location"] = point_3d.reshape((1, 3)).tolist()

    with open(obj_detect_coords_path, 'w') as outfile:
        json.dump(data, outfile, indent=4)


def create_augmented_img(in_path, img_file, camera, marker_size=0.071):

    img_path = os.path.join(in_path, img_file)
    out_img_file = os.path.join(in_path,
                                "augmented",
                                get_augmented_file(img_file))
    answer_file = os.path.join(in_path,
                               get_answer_file(img_file))

    detection_data = get_detection_data(in_path, img_file)

    if not os.path.exists(answer_file):
        logging.warning("No answer file found for " + img_file)
        return None

    answer_data = open(answer_file).read()
    answer_data = json.loads(answer_data)

    if not detection_data:
        return

    output_image = cv2.imread(img_path)
    output_image = draw_bounding_boxes(output_image, detection_data)
    output_image = draw_marker_coord_sys(output_image, camera, marker_size)

    data = draw_objs_sys(output_image, answer_data, camera)

    file_path = os.path.join(in_path,
                             "coords",
                             "hl_dl",
                             get_base_file(img_file) + "_camera.json")

    with open(file_path, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    cv2.imwrite(out_img_file, output_image)


def draw_bounding_boxes(in_img, detection_data):

    for box in detection_data:
        up_left = (int(box[0]), int(box[1]))
        down_right = (int(box[2]), int(box[3]))
        orginal_center = (int((box[0] + box[2])/2), int((box[1] + box[3])/2))
        output_image = cv2.rectangle(in_img,
                                     up_left,
                                     down_right,
                                     (0, 0, 255))
        output_image = cv2.circle(output_image,
                                  (orginal_center[0], orginal_center[1]),
                                  5,
                                  (0, 255, 0), -1)
    return output_image


def draw_marker_coord_sys_axis(in_img, intrinsics, distortion, rvecs, tvecs):

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


def draw_marker_coord_sys(in_img, camera, marker_size=0.071):

    fs = cv2.FileStorage(camera, cv2.FILE_STORAGE_READ)

    intrinsics = fs.getNode("camera_matrix")
    distortion = fs.getNode("distortion_coefficients")

    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
    parameters = aruco.DetectorParameters_create()
    parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX

    corners, ids, rejectedImgPoints = aruco.detectMarkers(in_img,
                                                          aruco_dict,
                                                          intrinsics.mat(),
                                                          distortion.mat(),
                                                          parameters=parameters
                                                          )

    if len(corners) == 0:
        return in_img

    # Detect the camera pose
    rvecs, tvecs, n = aruco.estimatePoseSingleMarkers(corners,
                                                      marker_size,
                                                      intrinsics.mat(),
                                                      distortion.mat())
    logging.debug(rvecs)
    logging.debug(tvecs)
    # Prepare the output image
    output_image = aruco.drawDetectedMarkers(in_img, corners)
    draw_marker_coord_sys_axis(output_image, intrinsics.mat(),
                               distortion.mat(), rvecs, tvecs)

    return output_image


def get_camera_cord(u, v, depth, intrinsics):
    cx = intrinsics[0][2]
    fx = intrinsics[0][0]
    cy = intrinsics[1][2]
    fy = intrinsics[1][1]
    hx = (u - cx) / fx
    hy = (v - cy) / fy

    z = math.sqrt(math.pow(depth, 2)/(math.pow(hx, 2) + math.pow(hy, 2) + 1))
    x = hx * z
    y = hy * z

    return x, y, z


def get_camera_hom_cord(u, v, depth, intrinsics):
    cx = intrinsics[0][2]
    fx = intrinsics[0][0]
    cy = intrinsics[1][2]
    fy = intrinsics[1][1]
    hx = (u - cx) / fx
    hy = (v - cy) / fy

    z = 1
    x = hx
    y = hy

    return x, y, z


all_detected_obj_data = dict()


def draw_objs_sys(in_img, answer_data, camera):
    # logging.debug("Answer Data:")
    # logging.debug(answer_data)

    detected_obj_data = dict()

    fs = cv2.FileStorage(camera, cv2.FILE_STORAGE_READ)

    intrinsics = fs.getNode("camera_matrix")
    # distortion = fs.getNode("distortion_coefficients")

    logging.debug(answer_data['all_objects'])

    logging.debug("--------All Objects------")
    for key, obj in answer_data['all_objects'].items():
        logging.debug("Object Name:")
        logging.debug(key)

        x, y, z = get_camera_cord(obj['x'],
                                  obj['y'],
                                  obj['depth'],
                                  intrinsics.mat())
        detected_obj_data[key] = dict()

        detected_obj_data[key]['location'] = dict()
        detected_obj_data[key]['location']['x'] = x
        detected_obj_data[key]['location']['y'] = y
        detected_obj_data[key]['location']['z'] = z

        x, y, z = get_camera_hom_cord(obj['x'],
                                      obj['y'],
                                      obj['depth'],
                                      intrinsics.mat())
        curr_key = '{}_homo'.format(key)
        detected_obj_data[curr_key] = dict()

        detected_obj_data[curr_key]['location'] = dict()
        detected_obj_data[curr_key]['location']['x'] = x
        detected_obj_data[curr_key]['location']['y'] = y
        detected_obj_data[curr_key]['location']['z'] = z

        curr_key = '{}_o'.format(key)

        detected_obj_data[curr_key] = dict()

        detected_obj_data[curr_key]['location'] = dict()
        detected_obj_data[curr_key]['location']['u'] = obj['x']
        detected_obj_data[curr_key]['location']['v'] = obj['y']
        detected_obj_data[curr_key]['location']['depth'] = obj['depth']

    return detected_obj_data


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


def get_base_file(img_file):
    base = os.path.splitext(img_file)[0]
    return base


def get_detection_file(img_file):
    base = os.path.splitext(img_file)[0]
    return base + "_detection.txt"


def get_detection_data(in_path, img_file):
    det_file = os.path.join(in_path, get_detection_file(img_file))

    if not os.path.exists(det_file):
        logging.warning("No detection file found for " + img_file)
        return None

    json_data = open(det_file).read()

    return json.loads(json_data)


def get_answer_file(img_file):
    base = os.path.splitext(img_file)[0]
    return base + "_answer.json"


def get_augmented_file(img_file):
    base = os.path.splitext(img_file)[0]
    ext = os.path.splitext(img_file)[1]
    return os.path.join(base + "_augmented" + ext)


def check_marker_sys(ids):
    for idx, val in enumerate(ids):
        if val == 23:
            return True

    return False


def get_marker_sys_corners(ids, corners):
    if len(ids) > 1:
        for idx, val in enumerate(ids):
            if val == 23:
                return corners[idx], val, idx

    return corners[0], 23, 0


if __name__ == '__main__':
    myargs = getopts(argv)
    out_path = None
    in_path = None
    params_path = None
    marker_size = 0.068

    if '-l' in myargs:
        logging.basicConfig(level=llevel_mapping[myargs['-l']])
    else:
        logging.basicConfig(level=logging.WARNING)

    if '-i' in myargs:
        in_path = myargs['-i']
        logging.info('Input folder at ' + in_path)
    else:
        logging.error('No input folder provided')
        exit(-1)

    if '-c' in myargs:
        camera = myargs['-c']
        logging.info('Camera Distortion model at ' + camera)
    else:
        logging.error('No Camera Distortion model provided')
        exit(-1)

    if '-m' in myargs:
        marker_size = float(myargs['-m'])
    else:
        marker_size = 0.071

    img_list = create_img_list(in_path)

    augmented_path = os.path.join(in_path, "augmented")
    if not os.path.exists(augmented_path):
        os.makedirs(augmented_path)

    obj_detect_coords_path = os.path.join(in_path, "coords")
    if not os.path.exists(obj_detect_coords_path):
        os.makedirs(obj_detect_coords_path)

    obj_detect_coords_path = os.path.join(in_path, "coords", "marker")
    if not os.path.exists(obj_detect_coords_path):
        os.makedirs(obj_detect_coords_path)

    obj_detect_coords_path = os.path.join(in_path, "coords", "hl_dl")
    if not os.path.exists(obj_detect_coords_path):
        os.makedirs(obj_detect_coords_path)

    for img in img_list:
        logging.debug(img)
        full_in_img_path = os.path.join(in_path, img)
        create_augmented_img(in_path, img, camera, marker_size)

        file_path = os.path.join(in_path,
                                 "coords",
                                 "marker",
                                 get_base_file(img) + "_camera.json")

        # Get the coordinates reference frame of marker
        id, corners, params = get_coordinates(full_in_img_path,
                                              camera,
                                              parameters_path=file_path,
                                              marker_size=marker_size)

        if id is None:
            continue

        if len(id) == 0:
            logging.warning("No marker found in image " + img)
            continue

        if not check_marker_sys(id):
            continue

        get_obj_locations_marker_sys(in_path,
                                     img,
                                     camera,
                                     params,
                                     corners,
                                     id,
                                     marker_size)

        logging.debug("Distance to object from camera")
        logging.debug(np.linalg.norm(params['m_c_3d'][0][0]))
