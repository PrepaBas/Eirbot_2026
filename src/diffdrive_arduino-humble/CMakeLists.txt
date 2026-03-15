cmake_minimum_required(VERSION 3.16)
project(diffbot_micro_ros LANGUAGES CXX) # Updated project name

if(CMAKE_CXX_COMPILER_ID MATCHES "(GNU|Clang)")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. Dependencies - Notice 'serial' is gone
set(THIS_PACKAGE_INCLUDE_DEPENDS
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
  std_msgs
  sensor_msgs
)

find_package(ament_cmake REQUIRED)
foreach(Dependency IN ITEMS ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

## 2. COMPILE
add_library(
  diffbot_micro_ros SHARED
  src/diffbot_micro_ros.cpp  # Path to your new .cpp file
)

target_compile_features(diffbot_micro_ros PUBLIC cxx_std_17)

# Ensure the compiler can find your .hpp in the include/ directory
target_include_directories(diffbot_micro_ros PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(
  diffbot_micro_ros PUBLIC
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

# 3. Plugin Registration
# Ensure the .xml filename matches your actual file in the root
pluginlib_export_plugin_description_file(hardware_interface diffbot_micro_ros.xml)

## 4. INSTALL 
install(
  DIRECTORY include/
  DESTINATION include
)

# Install your launch/config/urdf folders so they are available in the 'share' folder
install(
  DIRECTORY launch config description
  DESTINATION share/${PROJECT_NAME}
)

install(TARGETS diffbot_micro_ros
  EXPORT export_diffbot_micro_ros
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

## 5. EXPORTS
ament_export_targets(export_diffbot_micro_ros HAS_LIBRARY_TARGET)
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()