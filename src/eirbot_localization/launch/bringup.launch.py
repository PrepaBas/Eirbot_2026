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
    use_mock = LaunchConfiguration('use_mock', default='true')

    return LaunchDescription([
        DeclareLaunchArgument('use_mock', default_value='true', description='Use mock hardware'),

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

        # 4. RViz2 (Optionnel : ne le lance que si tu veux)
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', os.path.join(pkg_local, 'config', 'eirbot.rviz')], # Si tu as un fichier de config
            output='screen'
        ),

    ])