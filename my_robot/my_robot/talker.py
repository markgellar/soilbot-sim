import rclpy
from rclpy.node import Node
from soil_msgs.msg import SoilMeasurement
import random


class pHSensor(Node):

    def __init__(self):
        super().__init__('ph_sensor')
        self.publisher = self.create_publisher(
            SoilMeasurement,
            '/soil/measurement',
            10)
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.step = 0
        self.get_logger().info('pH sensor node started')

    def timer_callback(self):
        msg = SoilMeasurement()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        msg.ph = round(random.uniform(5.5, 7.5), 2)
        msg.moisture = round(random.uniform(10.0, 40.0), 2)
        msg.temperature = round(random.uniform(15.0, 25.0), 2)
        msg.ec = round(random.uniform(0.1, 2.0), 2)

        msg.latitude = 39.9526 + (self.step * 0.000009)
        msg.longitude = -75.1652
        msg.altitude = 50.0
        msg.gps_status = 3

        self.publisher.publish(msg)
        self.get_logger().info(
            f'Published: pH={msg.ph}, '
            f'moisture={msg.moisture}%, '
            f'EC={msg.ec} dS/m, '
            f'temp={msg.temperature}C'
        )

        self.step += 1


def main():
    rclpy.init()
    node = pHSensor()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
