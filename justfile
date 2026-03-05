help:
  @just --list

install:
    pixi install && \
    pixi run -e humble build-libserial

build:
    cd ~/ros2_ws 
    colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DPython_FIND_VIRTUALENV=ONLY -DPython3_FIND_VIRTUALENV=ONLY

lns:
    ros2 run diffbot_control diff_drive_node --ros-args -p use_sim:=false -p esp_port:=/dev/ttyUSB0

lys:
    ros2 run diffbot_control diff_drive_node --ros-args -p use_sim:=true 

sd:
    docker run -it \
    --net=host \
    -v $(pwd):/home/ros/ros2_ws \
    --name my_ros_container \
    --user ros \
    --env="DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    ros2_container

nd:
    docker exec -it my_ros_container /bin/bash \

bd:
    docker build -t ros2_container .

rosdep:
    sudo rosdep update \
    rosdep install --from-paths src --ignore-src -y

rmd:
    docker rm my_ros_container
screen:
    xhost +local:root