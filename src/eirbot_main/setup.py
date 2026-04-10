from setuptools import setup
import os
from glob import glob

package_name = 'eirbot_main'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Installation des fichiers de config (EKF, Nav2)
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        # Installation des cartes (yaml + pgm/png)
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ros',
    maintainer_email='ros@todo.todo',
    description='Eirbot Mission Control and Config',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mission_manager = eirbot_main.mission_manager:main'
        ],
    },
)