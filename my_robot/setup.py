import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'my_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='markwilliam',
    maintainer_email='markwilliam@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
		'talker = my_robot.talker:main',
		'listener = my_robot.listener:main',
		'gps_sensor = my_robot.gps_sensor:main',
		'soil_monitor = my_robot.soil_monitor:main',
        'spawn_lidar = my_robot.spawn_lidar_sensor:main',
        'attach_lidar = my_robot.attach_lidar:main',
        'fake_scan = my_robot.fake_scan:main',
        ],
    },
)
