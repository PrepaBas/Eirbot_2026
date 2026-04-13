import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Chemins vers les autres packages
    pkg_base = get_package_share_directory('eirbot_base')
    pkg_local = get_package_share_directory('eirbot_localization')
    pkg_nav = get_package_share_directory('eirbot_navigation')

    # Arguments (pour garder la main sur le mode simulation/mock)
    use_mock = LaunchConfiguration('use_mock', default='false')

    return LaunchDescription([
        DeclareLaunchArgument('use_mock', default_value='false', description='Use mock hardware'),

        # 1. Hardware / Base
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_base, 'launch', 'eirbot_base.launch.py')),
            launch_arguments={'use_mock': use_mock}.items()
        ),

        # 2. Localization (EKF)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_local, 'launch', 'localization.launch.py'))
        ),

        # 3. Navigation (Nav2)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_nav, 'launch', 'navigation.launch.py'))
        ),

        Node(
            package='eirbot_actions',
            executable='push_server', # Assure-toi que c'est le nom défini dans ton setup.py ou CMakeLists
            name='push_server',
            output='screen',
        ),

        Node(
            package='micro_ros_agent',
            executable='micro_ros_agent',
            name='micro_ros_agent',
            output='screen',
            arguments=['serial', '--dev', '/dev/ttyUSB0', '-v1']
        )

        # 5. Eirbot Mission Manager (Le cerveau)
        Node(package='eirbot_main', executable='mission_manager', output='screen'),
    ])