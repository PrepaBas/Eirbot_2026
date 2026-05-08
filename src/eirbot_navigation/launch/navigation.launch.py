import os
from launch_ros.actions import Node, SetRemap
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from nav2_common.launch import RewrittenYaml 

def generate_launch_description():
    pkg_navigation = get_package_share_directory('eirbot_navigation')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    
    map_yaml_file = os.path.join(pkg_navigation, 'maps', 'eurobot_table.yaml')
    default_params_file = os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    autostart = LaunchConfiguration('autostart', default='true')
    params_file = LaunchConfiguration('params_file', default=default_params_file)

    param_substitutions = {
        'use_sim_time': use_sim_time,
        'global_frame': 'map'
    }

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key='',
        param_rewrites=param_substitutions,
        convert_types=True)

    nav2_stack = GroupAction(
        actions=[
            # Redirect the final output of the entire Nav2 stack
            SetRemap(src='/cmd_vel', dst='/cmd_vel_nav'),
            
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
                ),
                launch_arguments={
                    'map': map_yaml_file,
                    'use_sim_time': use_sim_time,
                    'autostart': autostart,
                    'params_file': configured_params,
                    'use_amcl': 'False',      
                    'use_localization': 'False',
                    'use_composition': 'True', # Critical for Pi 5 CPU
                }.items()
            ),
        ]
    )

    # Collision Monitor: The final safety gate
    collision_monitor_node = Node(
        package='nav2_collision_monitor',
        executable='collision_monitor',
        name='collision_monitor',
        output='screen',
        parameters=[configured_params]

    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('params_file', default_value=default_params_file),
        nav2_stack, # Added missing comma here
        collision_monitor_node
    ])