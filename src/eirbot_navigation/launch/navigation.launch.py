import os
from launch_ros.actions import Node, SetRemap
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from nav2_common.launch import RewrittenYaml 

def generate_launch_description():
    pkg_navigation = get_package_share_directory('eirbot_navigation')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    map_yaml_file = os.path.join(pkg_navigation, 'maps', 'eurobot_table.yaml')

    # Arguments
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    mode = LaunchConfiguration('mode')
    start_pos = LaunchConfiguration('start_pos')
    
    # 1. Déclaration des arguments
    declare_mode_arg = DeclareLaunchArgument(
        'mode', default_value='static', 
        description='Localization mode: "static" or "amcl"')

    declare_start_pos_arg = DeclareLaunchArgument(
        'start_pos', default_value='pos1',
        description='Starting position: "pos1" or "pos2"')

    # Coordonnées dynamiques pour le Static TF
    x_val = PythonExpression(["'-1.2' if '", start_pos, "' == 'pos1' else '1.2'"])
    y_val = '1.75'
    yaw_val = '-1.75'

    # 2. Logique de modification du YAML (La partie magique)
    # On définit ce qu'on veut écraser dans le fichier original
    param_substitutions = {
        'global_frame': PythonExpression(["'map' if '", mode, "' == 'static' else 'odom'"]),
        'use_sim_time': use_sim_time
    }

    # On crée un nouveau fichier temporaire réécrit
    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key='',
        param_rewrites=param_substitutions,
        convert_types=True)

    # 3. Static TF Publisher (Uniquement en mode static)
    static_tf_node = Node(
        condition=IfCondition(PythonExpression(["'", mode, "' == 'static'"])),
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_node',
        arguments=[x_val, y_val, '0', yaw_val, '0', '0', 'map', 'odom']
    )

    # 4. Groupe Nav2
    nav2_bringup = GroupAction(
        actions=[
            SetRemap(src='/cmd_vel', dst='/diffbot_base_controller/cmd_vel_unstamped'),
            
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
                ),
                launch_arguments={
                    'map': map_yaml_file,
                    'use_sim_time': use_sim_time,
                    'autostart': autostart,
                    'use_amcl': PythonExpression(["'False' if '", mode, "' == 'static' else 'True'"]),
                    'params_file': configured_params, # <--- ON PASSE LE FICHIER RÉÉCRIT
                    'use_composition': 'True',
                }.items()
            ),
        ]
    )
    
    return LaunchDescription([
        declare_mode_arg,
        declare_start_pos_arg,
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('params_file', default_value=os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')),
        static_tf_node,
        nav2_bringup
    ])