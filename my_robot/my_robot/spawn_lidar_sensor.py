import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SpawnEntity
from geometry_msgs.msg import Pose
import subprocess
import time


class LidarSensorSpawner(Node):

    def __init__(self):
        super().__init__('lidar_sensor_spawner')

        self.client = self.create_client(SpawnEntity, '/spawn_entity')
        while not self.client.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Waiting for spawn service...')

        # Wait for the robot to fully spawn
        time.sleep(3.0)

        # Get the current pose of sensor_box_link from tf
        self.spawn_sensor()

    def spawn_sensor(self):
        sdf = """<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="os1_sensor_model">
    <link name="sensor_link">
      <sensor type="ray" name="os1_lidar">
        <pose>0 0 0 0 0 0</pose>
        <visualize>true</visualize>
        <update_rate>10</update_rate>
        <ray>
          <scan>
            <horizontal>
              <samples>512</samples>
              <resolution>1</resolution>
              <min_angle>-3.14159</min_angle>
              <max_angle>3.14159</max_angle>
            </horizontal>
            <vertical>
              <samples>64</samples>
              <resolution>1</resolution>
              <min_angle>-0.3927</min_angle>
              <max_angle>0.3927</max_angle>
            </vertical>
          </scan>
          <range>
            <min>0.3</min>
            <max>120.0</max>
            <resolution>0.003</resolution>
          </range>
        </ray>
        <plugin name="os1_plugin" filename="libgazebo_ros_ray_sensor.so">
          <ros>
            <remapping>~/out:=/ouster/points</remapping>
          </ros>
          <output_type>sensor_msgs/PointCloud2</output_type>
          <frame_name>sensor_box_link</frame_name>
        </plugin>
      </sensor>
    </link>
  </model>
</sdf>"""

        request = SpawnEntity.Request()
        request.name = 'os1_sensor'
        request.xml = sdf
        request.robot_namespace = ''
        request.reference_frame = ''

        # Spawn at approximate world position of the LiDAR
        request.initial_pose.position.x = 0.0
        request.initial_pose.position.y = 0.0
        request.initial_pose.position.z = 0.5

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        result = future.result()
        if result is not None and result.success:
            self.get_logger().info('LiDAR sensor spawned successfully')
        else:
            msg = result.status_message if result else 'No response'
            self.get_logger().error(f'Failed: {msg}')


def main():
    rclpy.init()
    node = LidarSensorSpawner()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
