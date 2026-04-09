from setuptools import setup
import os
from glob import glob

package_name = 'eirbot_localization'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        # Enregistrement du package dans l'index ROS
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        
        # Inclusion du package.xml
        ('share/' + package_name, ['package.xml']),
        
        # Inclusion de tous les fichiers .launch.py du dossier launch/
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        
        # Inclusion de tous les fichiers .yaml du dossier config/ (pour l'EKF)
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'config'), glob('config/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='bastien',
    maintainer_email='ros@todo.todo',
    description='Localization system for Eirbot 2026 using EKF fusion',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # On garde le point d'entrée au cas où tu réutilises le script
            'pose_broadcaster = eirbot_localization.pose_broadcaster:main',
            'push_action = eirbot_localization.push_action_node:main',
            'set_init_pose = eirbot_localization.set_init_pose:main',
        ],
    },
)