cmake_minimum_required(VERSION 3.8)
project(eirbot_actions)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. Dépendances
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(eirbot_interfaces REQUIRED)
find_package(behaviortree_cpp_v3 REQUIRED)
find_package(nav2_behavior_tree REQUIRED)

# 2. Compilation du Wrapper C++ (Le Plugin BT)
add_library(push_action_bt_node_lib SHARED
  src/push_action_bt_node.cpp
)

# On ajoute explicitement les répertoires d'inclusion pour éviter les erreurs de headers
target_include_directories(push_action_bt_node_lib PRIVATE
  include
  ${nav2_behavior_tree_INCLUDE_DIRS}
  ${behaviortree_cpp_v3_INCLUDE_DIRS}
)

# Liens vers les dépendances C++
# Utilisation des variables ${..._LIBRARIES} au lieu des targets :: pour assurer la compatibilité
target_link_libraries(push_action_bt_node_lib
  ${nav2_behavior_tree_LIBRARIES}
  ${behaviortree_cpp_v3_LIBRARIES}
  eirbot_interfaces::eirbot_interfaces__rosidl_typesupport_cpp
)

# On s'assure que le plugin exporte bien ses symboles pour être chargé par Nav2
target_compile_definitions(push_action_bt_node_lib PRIVATE BT_PLUGIN_EXPORT)

# 3. Installation des exécutables Python (Serveur d'action)
install(PROGRAMS
  eirbot_actions/push_server.py
  DESTINATION lib/${PROJECT_NAME}
)

# 4. Installation de la bibliothèque C++ (Plugin BT)
install(TARGETS push_action_bt_node_lib
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Indispensable pour que le plugin soit trouvé par le bt_navigator
ament_export_libraries(push_action_bt_node_lib)
ament_export_dependencies(nav2_behavior_tree behaviortree_cpp_v3 eirbot_interfaces)

ament_package()