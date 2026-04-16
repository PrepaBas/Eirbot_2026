import os
from launch_ros.actions import Node, SetRemap
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from nav2_common.launch import RewrittenYaml 

def generate_launch_description():
    # 1. Chemins des dossiers
    pkg_navigation = get_package_share_directory('eirbot_navigation')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    
    map_yaml_file = os.path.join(pkg_navigation, 'maps', 'eurobot_table.yaml')
    default_params_file = os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')

    # 2. Arguments de lancement
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    autostart = LaunchConfiguration('autostart', default='true')
    params_file = LaunchConfiguration('params_file', default=default_params_file)

    # 3. Réécriture des paramètres (Pour injecter use_sim_time proprement)
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'global_frame': 'map' # On s'assure que Nav2 travaille toujours dans le repère map
    }

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key='',
        param_rewrites=param_substitutions,
        convert_types=True)

    # 4. Groupe Nav2 : On lance uniquement le nécessaire
    nav2_stack = GroupAction(
        actions=[
            # Remap du topic de commande vers ton contrôleur hardware
            SetRemap(src='/cmd_vel', dst='/eirbot_base_controller/cmd_vel_unstamped'),
            
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
                ),
                launch_arguments={
                    'map': map_yaml_file,
                    'use_sim_time': use_sim_time,
                    'autostart': autostart,
                    'params_file': configured_params,
                    'use_amcl': 'False',      # AMCL est désactivé ici
                    'use_localization': 'False',
                    'use_composition': 'True', # Recommandé pour réduire la charge CPU sur Pi
                }.items()
            ),
        ]
    )
    
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('params_file', default_value=default_params_file),
        nav2_stack
    ])