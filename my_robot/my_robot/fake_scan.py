import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math


class FakeScanPublisher(Node):

    def __init__(self):
        super().__init__('fake_scan_publisher')
        self.declare_parameter('use_sim_time', True)
        self.publisher = self.create_publisher(LaserScan, '/scan', 10)
        self.timer = self.create_timer(0.1, self.publish_scan)
        self.get_logger().info('Fake scan publisher started')

    def publish_scan(self):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'os1_lidar_link'

        msg.angle_min = -math.pi
        msg.angle_max = math.pi
        msg.angle_increment = 2.0 * math.pi / 360
        msg.time_increment = 0.0
        msg.scan_time = 0.1
        msg.range_min = 0.3
        msg.range_max = 30.0

        msg.ranges = [30.0] * 360

        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = FakeScanPublisher()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
