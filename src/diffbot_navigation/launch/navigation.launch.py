import os

from launch_ros.actions import Node, PushRosNamespace, SetRemap # Add SetRemap
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction # Add GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_navigation = get_package_share_directory('diffbot_navigation')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    autostart = LaunchConfiguration('autostart', default='true')
    
    map_yaml_file = os.path.join(pkg_navigation, 'maps', 'eurobot_table.yaml')
    params_file = os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')

    # 1. Wrap the bringup in a GroupAction to apply remappings
    nav2_with_remappings = GroupAction(
        actions=[
            SetRemap(src='/cmd_vel', dst='/diffbot_base_controller/cmd_vel_unstamped'),
            
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
                ),
                launch_arguments={
                    'map': map_yaml_file,
                    'use_sim_time': use_sim_time,
                    'params_file': params_file,
                    'autostart': autostart,
                    'use_amcl': 'False',
                    'use_slam': 'False'
                }.items()
            ),
        ]
    )

    # 2. Keep your static transform to stay out of the corner
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        arguments=['0.5', '0.5', '0', '0', '0', '0', 'map', 'odom']
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        nav2_with_remappings, # Use the group here
        static_tf_node 
    ])