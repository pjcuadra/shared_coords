# Shared Coordinates

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
                    out_path,
                    camera,
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
