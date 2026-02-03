build:
    pixi run -e hw build

launch_control_nosim:
    ros2 run diffbot_control diff_drive_node --ros-args -p left_esc_port:=/dev/ttyACM0 -p right_esc_port:=/dev/ttyACM1 -p use_sim:=falsepi