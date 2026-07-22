# Rokey Cobot Project 2

![Rokey Cobot setup](resource/img/img1.jpg)

This project is an automated recycling system built with a collaborative robot and vision AI. A RealSense RGB-D camera detects objects, YOLO-based object detection results are converted into the robot coordinate system, and a Doosan collaborative robot picks up each object and moves it to the appropriate sorting location. The system is also connected to a web/Firebase interface to monitor the start condition, emergency stop, trash bin status, and task completion state.

## Project Overview

- Detects recyclable objects from camera images.
- Calculates each object's position and pose, then converts them into robot-graspable coordinates.
- Adjusts the gripping pose by considering both the planar angle and the Z-axis tilt.
- Uses vision to check whether an object contains water and estimates the water level.
- Supports voice commands for pausing, resuming, and selecting target objects.
- Manages robot status and workflow through a Firebase-based web interface.

## System Architecture

![System architecture](resource/img/system_architectur.png)

## Flow Charts

| Web Flow | Robot Flow | Exception Handling Flow |
| --- | --- | --- |
| <img src="resource/img/web_flowchart.png" alt="Web flowchart" width="300"> | <img src="resource/img/robot_flowchart.png" alt="Robot flowchart" width="300"> | <img src="resource/img/exception_flowchart.png" alt="Exception flowchart" width="300"> |

## Demo Video

[Watch the final demo video](<resource/img/최종 영상.mp4>)

## Key Features

### Voice Control

Voice commands can pause or resume robot operation and select specific sorting targets.

### Z Tilting Grip

The system calculates both the object's planar rotation angle and Z-axis tilt angle, then grips the object according to its pose.

![Z tilting grip](resource/img/z_tilting.gif)

### Water Detection

The system determines whether an object contains water and estimates the water level in stages.

| Water O | Water X |
| --- | --- |
| <img src="resource/img/물O.gif" alt="Water detected" width="420"> | <img src="resource/img/물X.gif" alt="Water not detected" width="420"> |

| 0% | 25% | 50% | 75% |
| --- | --- | --- | --- |
| <img src="resource/img/water0.png" alt="Water level 0%" width="210"> | <img src="resource/img/water25.png" alt="Water level 25%" width="210"> | <img src="resource/img/water50.png" alt="Water level 50%" width="210"> | <img src="resource/img/water75.png" alt="Water level 75%" width="210"> |

## Tech Stack

- **Robot**: Doosan M0609 collaborative robot, OnRobot RG gripper
- **Vision**: Intel RealSense RGB-D Camera, OpenCV, YOLO
- **Robot Middleware**: ROS 2, Doosan Robotics ROS 2 package
- **Backend / Control**: Python, Firebase Firestore
- **Auxiliary Features**: STT voice commands, emergency stop, trash bin fullness detection

## Repository Structure

```text
.
├── cobot2/       # Robot control, object detection, coordinate conversion, and Firebase integration
├── resource/     # Calibration data, class information, images, and video assets
├── test/         # ROS 2 package tests
├── package.xml   # ROS 2 package metadata
└── setup.py      # Python package setup
```

## Note

This project was developed using a real collaborative robot, gripper, RGB-D camera, and Firebase environment.
