from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import UnlessCondition, IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # 1. Setup Substitutions & Arguments
    use_gazebo = LaunchConfiguration('use_gazebo')
    
    use_gazebo_arg = DeclareLaunchArgument(
        'use_gazebo', 
        default_value='false',
        description='Start Gazebo simulation'
    )

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]), " ",
        PathJoinSubstitution([FindPackageShare("diffdrive_arduino"), "urdf", "diffbot.urdf.xacro"]),
        " use_gazebo:=", use_gazebo
    ])

    config_path = lambda pkg, folder, file: PathJoinSubstitution([FindPackageShare(pkg), folder, file])

    # 2. Gazebo Specific Actions (Conditional)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py'])
        ]),
        condition=IfCondition(use_gazebo) # Only start Gazebo if use_gazebo is true
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'diffbot'],
        output='screen',
        condition=IfCondition(use_gazebo) # Only spawn if use_gazebo is true
    )

    # 3. Standard Nodes
    nodes = [
        use_gazebo_arg,
        gazebo,
        spawn_entity,
        
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

        Node(package="controller_manager", executable="spawner", arguments=["joint_state_broadcaster"]),
        Node(package="controller_manager", executable="spawner", arguments=["diffbot_base_controller"]),

        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", config_path("diffdrive_arduino", "rviz", "diffbot.rviz")],
        ),
    ]

    return LaunchDescription(nodes)