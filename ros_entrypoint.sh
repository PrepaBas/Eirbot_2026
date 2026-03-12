#!/bin/bash
set -e
source "/opt/ros/humble/setup.bash"
if [ -f "/home/ros/ros2_ws/install/setup.bash" ]; then
  source "/home/ros/ros2_ws/install/setup.bash"
fi


WS_SETUP="/home/ros/ros2_ws/install/setup.bash"
if [ -f "/home/ros/ros2_ws/install/setup.bash" ]; then
    source "/home/ros/ros2_ws/install/setup.bash"
else
    echo "Note: install/setup.bash not found. Did you build the workspace?"
fi
exec "$@"