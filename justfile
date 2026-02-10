build:
    pixi run build

lns:
    ros2 run diffbot_control diff_drive_node --ros-args -p use_sim:=false -p esp_port:=/dev/ttyUSB0

lys:
    ros2 run diffbot_control diff_drive_node --ros-args -p use_sim:=true 