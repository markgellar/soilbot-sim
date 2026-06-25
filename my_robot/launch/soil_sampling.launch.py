from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        Node(
            package='my_robot',
            executable='talker',
            name='ph_sensor',
            output='screen',
        ),

        Node(
            package='my_robot',
            executable='soil_monitor',
            name='soil_monitor',
            output='screen',
        ),

    ])