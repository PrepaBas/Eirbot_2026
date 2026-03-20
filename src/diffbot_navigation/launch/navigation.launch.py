import os
from launch_ros.actions import Node, SetRemap
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_navigation = get_package_share_directory('diffbot_navigation')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    # Configuration Nav2
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    map_yaml_file = os.path.join(pkg_navigation, 'maps', 'eurobot_table.yaml')
    params_file = os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')

    # 1. Déclaration des arguments de position (INDISPENSABLE dans le return final)
    declare_x_arg = DeclareLaunchArgument('x', default_value='1.5', description='Start X')
    declare_y_arg = DeclareLaunchArgument('y', default_value='0.5', description='Start Y')
    declare_yaw_arg = DeclareLaunchArgument('yaw', default_value='1.57', description='Start Yaw (rad)')
    declare_use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false')
    declare_autostart_arg = DeclareLaunchArgument('autostart', default_value='true')

    # 2. Static TF Publisher (Map -> Odom)
    # L'ordre est : x y z yaw pitch roll frame_id child_frame_id
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_node',
        arguments=[
            LaunchConfiguration('x'), 
            LaunchConfiguration('y'), 
            '0', # Z
            LaunchConfiguration('yaw'), 
            '0', '0', # Pitch / Roll
            'map', 'odom'
        ]
    )

    # 3. Groupe Nav2 avec Remappings
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
                    'use_amcl': 'False', # On n'utilise pas de Lidar
                    'use_composition': 'True', # Recommandé pour Raspberry Pi
                    'use_namespace': 'False'
                }.items()
            ),
        ]
    )

    # 4. Retour de la description (Tous les DeclareLaunchArgument DOIVENT être ici)
    return LaunchDescription([
        declare_x_arg,
        declare_y_arg,
        declare_yaw_arg,
        declare_use_sim_time_arg,
        declare_autostart_arg,
        static_tf_node,
        nav2_with_remappings
    ])