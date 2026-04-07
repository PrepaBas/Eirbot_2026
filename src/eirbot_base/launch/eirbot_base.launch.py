from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # 1. Setup Substitutions & Arguments
    use_mock = LaunchConfiguration('use_mock')
    
    # Declare the argument (Default to true so you can see it work immediately)
    declare_use_mock = DeclareLaunchArgument(
        'use_mock', 
        default_value='true',
        description='Use mock hardware (GenericSystem) instead of real hardware'
    )

    # Pass the use_mock argument into the xacro command
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]), " ",
        PathJoinSubstitution([FindPackageShare("eirbot_base"), "urdf", "eirbot_base.urdf.xacro"]),
        " use_mock:=", use_mock,
    ])

    config_path = lambda pkg, folder, file: PathJoinSubstitution([FindPackageShare(pkg), folder, file])
    
    controller_param_file = PathJoinSubstitution(
        [FindPackageShare("eirbot_base"), "config", "eirbot_base_controllers.yaml"]
    )

    nodes = [        
        declare_use_mock,

        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description_content}],
        ),

        Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[{"robot_description": robot_description_content}, 
                        controller_param_file],
            output="both",
        ),

        Node(package="controller_manager", executable="spawner", arguments=["joint_state_broadcaster"]),
        Node(package="controller_manager", executable="spawner", arguments=["eirbot_base_controller"]),

        #Node(
        #    package="rviz2",
        #    executable="rviz2",
        #    arguments=["-d", config_path("diffdrive_arduino", "rviz", "diffbot.rviz")],
        #),
    ]

    return LaunchDescription(nodes)