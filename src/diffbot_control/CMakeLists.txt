cmake_minimum_required(VERSION 3.8)
project(diffbot_control)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(
  PROGRAMS
    diffbot_control/diff_drive_node.py
    diffbot_control/esp_driver.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
