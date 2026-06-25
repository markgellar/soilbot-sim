import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from builtin_interfaces.msg import Time
import math

class GPSSensor(Node):

    def __init__(self):
        super().__init__('gps_sensor')

        self.publisher = self.create_publisher(
            NavSatFix,
            '/gps/fix',
            10)

        self.timer = self.create_timer(0.5, self.timer_callback)

        # Simulate starting position - center of a farm field
        # Using a real coordinate in Pennsylvania as an example
        self.base_lat = 39.9526
        self.base_lon = -75.1652
        self.altitude = 50.0
        self.step = 0

        self.get_logger().info('GPS sensor node started')

    def timer_callback(self):
        msg = NavSatFix()

        # Header
        now = self.get_clock().now().to_msg()
        msg.header.stamp = now
        msg.header.frame_id = 'gps'

        # Simulate robot moving in a straight line across a field
        # Each step moves ~1 meter north
        msg.latitude = self.base_lat + (self.step * 0.000009)
        msg.longitude = self.base_lon
        msg.altitude = self.altitude

        # Simulate RTK-GPS quality fix
        msg.status.status = NavSatStatus.STATUS_GBAS_FIX
        msg.status.service = NavSatStatus.SERVICE_GPS

        # Position covariance - diagonal represents x,y,z variance in m^2
        # 0.0001 = ~1cm accuracy, typical for RTK
        msg.position_covariance = [
            0.0001, 0.0,    0.0,
            0.0,    0.0001, 0.0,
            0.0,    0.0,    0.0001
        ]
        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN

        self.publisher.publish(msg)
        self.get_logger().info(
            f'GPS fix: lat={msg.latitude:.7f}, '
            f'lon={msg.longitude:.7f}, '
            f'alt={msg.altitude:.1f}m'
        )

        self.step += 1

def main():
    rclpy.init()
    node = GPSSensor()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
