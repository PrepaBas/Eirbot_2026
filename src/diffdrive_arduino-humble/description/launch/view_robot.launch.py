from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # 1. Setup Substitutions
    use_gazebo = LaunchConfiguration('use_gazebo')

    config_path = lambda pkg, folder, file: PathJoinSubstitution([FindPackageShare(pkg), folder, file])

    # 2. Define Nodes
    nodes = [
        DeclareLaunchArgument('use_gazebo', default_value='false'),

        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description_content}],
        ),

        # Only runs for REAL hardware
        Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[{"robot_description": robot_description_content}, 
                        config_path("diffdrive_arduino", "config", "diffbot_controllers.yaml")],
            condition=UnlessCondition(use_gazebo)
        ),

        # Spawners - No EventHandlers needed; they wait for /controller_manager automatically
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster"],
        ),

        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["diffbot_base_controller"],
        ),

        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", config_path("diffdrive_arduino", "rviz", "diffbot.rviz")],
        ),
    ]

    return LaunchDescription(nodes)