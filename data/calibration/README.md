Calibration is done with OpenCV examples as follows;

1. Build OpenCV with examples with *-D BUILD_EXAMPLES ON*
2. Take several pictures of the chessboard with your camera
3. Measure the size of the chessboard squares in meters
4. From the chessboard, count the amount of intersection of 4 full squares
   horizontally and vertically.
5. Put all the images in a directory
6. Run imagelist_create OpenCV example as follows;

```

./bin/cpp-example-imagelist_creator images.xml <path-to-images>*.JPG

```

7. Run the calibration example with as follows;


```

./bin/cpp-example-calibration -o=camera.yml  -s=<size-of-squares-in-meters> -pt=chessboard -w=<horizontal-intersections> -h=<vertical-intersections> images.xml

```
