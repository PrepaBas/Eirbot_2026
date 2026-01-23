cmake_minimum_required(VERSION 3.8)
project(diffbot_description)

# Bonnes pratiques warnings si un jour tu ajoutes du C++
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Dependencies (pour launch/urdf on installe surtout des fichiers,
# mais on déclare quand même les dépendances runtime dans package.xml)
find_package(ament_cmake REQUIRED)

# --- Installer les ressources du package ---
# URDF / xacro
install(
  DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

# Launch files
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# Config (yaml), meshes, rviz configs, etc.
install(
  DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

install(
  DIRECTORY meshes
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

install(
  DIRECTORY rviz
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
