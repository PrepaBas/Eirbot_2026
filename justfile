help:
  @just --list

install:
    pixi install && \
    pixi run -e humble build-libserial

build:
    cd ~/ros2_ws 
    colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DPython_FIND_VIRTUALENV=ONLY -DPython3_FIND_VIRTUALENV=ONLY

#lns:
#    ros2 run diffbot_control diff_drive_node --ros-args -p use_sim:=false -p esp_port:=/dev/ttyUSB0

#lys:
#    ros2 run diffbot_control diff_drive_node --ros-args -p use_sim:=true 

sd:
    docker run -it \
    --net=host \
    -v $(pwd):/home/ros/ros2_ws \
    --name my_ros_container \
    --user ros \
    --env="DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    -v /dev:/dev  \
    --privileged \
    --ulimit rtprio=99 \
    --ulimit memlock=-1 \
    --cap-add=SYS_NICE \
    ros2_container

nd:
    docker exec -it my_ros_container /bin/bash \

bd:
    docker build -t ros2_container .

bdm:
  docker buildx build --platform linux/arm64 \
  -t ros2_container:latest \
  --output type=docker,dest=image_robot.tar .

rosdep:
    sudo rosdep update \
    rosdep install --from-paths src --ignore-src -y

rmd:
    docker rm my_ros_container

screen:
    xhost +local:root

lgazebo:
    ros2 launch gazebo_ros gazebo.launch.py 

lspawn:
    ros2 run gazebo_ros spawn_entity.py  -topic robot_description -entity my_bot

ldiffbotm:
    ros2 launch diffdrive_arduino diffbot.launch.py use_mock:=true

ldiffbotr:
    ros2 launch diffdrive_arduino diffbot.launch.py use_mock:=false

lk:
    ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diffbot_base_controller/cmd_vel_unstamped -p use_sim_time:=true

lura:
    ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -v6