cmake_minimum_required(VERSION 3.16)
project(eirbot_base LANGUAGES CXX)

if(CMAKE_CXX_COMPILER_ID MATCHES "(GNU|Clang)")
  add_compile_options(-Wall -Wextra)
endif()

# find dependencies
set(THIS_PACKAGE_INCLUDE_DEPENDS
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
  std_msgs
  sensor_msgs
  geometry_msgs
)

# find dependencies
find_package(ament_cmake REQUIRED)
foreach(Dependency IN ITEMS ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()


## COMPILE
add_library(
  eirbot_base SHARED
  hardware/eirbot_base.cpp
)

target_compile_features(eirbot_base PUBLIC cxx_std_17)
target_include_directories(eirbot_base PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/hardware/include/eirbot_base>
  $<INSTALL_INTERFACE:include/eirbot_base>
)

ament_target_dependencies(
  eirbot_base PUBLIC
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

target_link_libraries(eirbot_base PUBLIC )

# Causes the visibility macros to use dllexport rather than dllimport,
# which is appropriate when building the dll but not consuming it.
# target_compile_definitions(${PROJECT_NAME} PRIVATE "DIFFDRIVE_ARDUINO_BUILDING_DLL")

# Export hardware plugins
pluginlib_export_plugin_description_file(hardware_interface eirbot_base.xml)

# INSTALL
install(
  DIRECTORY hardware/include/
  DESTINATION include/eirbot_base
)
install(
  DIRECTORY description/ros2_control description/urdf description/rviz
  DESTINATION share/eirbot_base
)
install(
  DIRECTORY launch config
  DESTINATION share/eirbot_base
)
install(TARGETS eirbot_base
  EXPORT export_eirbot_base
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
endif()

## EXPORTS
ament_export_targets(export_eirbot_base HAS_LIBRARY_TARGET)
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()
