#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/ros/ros2_ws/install/setup.bash

# Optionnel : attendre que les ports série (Lidar/Moteurs) soient prêts
sleep 5

ros2 launch eirbot_bringup rasp.launch.py