# Shared Coordinates

This repository holds a set of tools to help us analyze the data set obtained from the Microsoft Hololens. The aim is to be able to create a shared coordinates systems to optimize data processing and network bandwidth.

## How to analyze a data set

You can find an example of a data set at `data/process_log`. The process to analyze the data set is as follows;

1. Run `process_data_set.py` to obtain augmented images, marker-based coordinates data, and detection coordinates data.
2. Run `process_log.py` to obtain raycast-based coordinates data.
3. Run `separate_by_position.py` to separate images and data from the different positions into different directories.
4. Run `calc_stats.py` to calculate the statistics of the previously obtained coordinates.

## Create Marker

### Usage

#### Command Line

```bash
python create_marker.py [-i <id>] [-v] [-s] [-o <output_image>] [-m <size-in-pixels>]

```

* ```-i```: ID of the marker to be created
* ```-v```: Verbose mode
* ```-s```: Show window with original image augmented with marker coordinates
  system axis
* ```-o```: Path to where the marker image will be written
* ```-m```: Size of the marker image in pixels

## Get Shared Coordinates

A data set of picture for testing this is provided at `data/original`.

### Usage

#### Command Line

```bash
python get_shared_coord.py -i <input_image> -c <camera_config_file> [-v] [-s] [-o <output_image>] [-p <params_file>] [-m <size-in-meters>]

```

* ```-i```: Path to the input image
* ```-c```: Path to the camera calibration file
* ```-v```: Verbose mode
* ```-s```: Show window with original image augmented with marker coordinates
  system axis
* ```-o```: Path to where the augmented image will be written
* ```-p```: Path to where the JSON file containing the following information
  will be written;
  * ID of each of the detected marker
  * Pixel location of the center point of each of the detected marker
  * 3D location of the center point of each of the detected marker
  * Normal vector with respect to each detected marker
* ```-m```: Size of the printed marker in meters

#### Programmatically

```
def get_coordinates(in_path,
                    camera,
                    out_path,
                    parameters_path=None,
                    show_window=False,
                    marker_size=0.071):
```

* ```in_path```: Path to the input image
* ```camera```: Path to the camera calibration file
* ```show_window```: Show window with original image augmented with marker
  coordinates system axis
* ```out_path```: Path to where the augmented image will be written
* ```parameters_path```: Path to where the JSON file containing the following
  information will be written;
  * ID of each of the detected marker
  * Pixel location of the center point of each of the detected marker
  * 3D location of the center point of each of the detected marker
  * Normal vector with respect to each detected marker
* ```marker_size```: Size of the printed marker in meters


## Circles Distance

A data set of picture for testing this is provided at `data/circles_distance`.

### Usage

#### Command Line

```bash
python circles_distance.py -i <input_image> -c <camera_config_file> [-v] [-s] [-o <output_image>] [-m <size-in-meters>]

```

* ```-i```: Path to the input image
* ```-c```: Path to the camera calibration file
* ```-v```: Verbose mode
* ```-s```: Show window with original image augmented with marker coordinates
  system axis
* ```-o```: Path to where the augmented image will be written
* ```-m```: Size of the printed marker in meters

#### Programmatically

```
def circles_distance(in_path,
                     out_path,
                     camera,
                     show_window=False,
                     marker_size=0.071):
```

* ```in_path```: Path to the input image
* ```camera```: Path to the camera calibration file
* ```show_window```: Show window with original image augmented with marker
  coordinates system axis
* ```out_path```: Path to where the augmented image will be written
* ```marker_size```: Size of the printed marker in meters

## Process Data Set

This command assumes that the data set contains multiple images stored in a folder (input path) and with the following files;

* *<image-name>.jpg* : Image file
* *<image-name>.json* : Server data response
* *<image-name>\_answer.json* : Detected objects and their center position
* *<image-name>\_detection.txt* : Bounding box information returned by the Deep Learning algorithm

You can find an example of this data set at `data/process_data`.

### Usage


```bash
python process_data_set.py -i <input_path> -c <camera_config_file> [-l <level>] [-m <marker-size-in-meters>]

```

* ```-i```: Path to the input data set
* ```-c```: Path to the camera calibration file. For the data set at `data/process_data`, `data/calibration/hololens/hololens.yml` can be used.
* ```-l```: Logging level possible values are; `info`, `debug`, `warning` and `error`.
* ```-m```: Size of the printed marker in meters

## Process Log

This script processes a log as the one at `data/process_data/data.log`.

### Usage

```bash
python process_log.py -i <input_log> [-v] -o <output-path>

```

* ```-i```: Path to the input log file
* ```-v```: Verbose mode
* ```-o```: Output path to where the obtained information will be placed

## Separate By Position

This script separates the images and their corresponding data into different folders. Useful for further analysis. For example, to use the `calc_stats.py` script.

### Usage


```bash
python separate_by_position.py -i <input_path> [-v] -s <path-to-sep-file> -o <output-path>

```

* ```-i```: Path to the input data set
* ```-v```: Verbose mode
* ```-o```: Output path to where the separated data will be placed
* ```-s```: Path to separation file

## Calculate Stats

This scripts calculates statistics from the coordinates of a data set.

### Usage


```bash
python calc_stats.py -i <input_path> [-v] -o <output-path>

```

* ```-i```: Path to the input data set
* ```-v```: Verbose mode
* ```-o```: Output path to where the statistics output files will be placed
