import rclpy
from rclpy.node import Node
from soil_msgs.msg import SoilMeasurement
import csv
import os
from datetime import datetime


class SoilMonitor(Node):

    def __init__(self):
        super().__init__('soil_monitor')

        self.subscription = self.create_subscription(
            SoilMeasurement,
            '/soil/measurement',
            self.measurement_callback,
            10)

        # Create a timestamped log file in the home directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_path = os.path.expanduser(
            f'~/soil_logs/measurement_{timestamp}.csv')

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        # Open CSV and write header
        self.csv_file = open(self.log_path, 'w', newline='')
        self.writer = csv.DictWriter(self.csv_file, fieldnames=[
            'timestamp',
            'latitude',
            'longitude',
            'altitude',
            'ph',
            'moisture',
            'temperature',
            'ec',
            'gps_status',
            'recommendation'
        ])
        self.writer.writeheader()
        self.csv_file.flush()

        self.measurements = []
        self.get_logger().info(f'Soil monitor started, logging to {self.log_path}')

    def measurement_callback(self, msg):

        if msg.gps_status < 1:
            self.get_logger().warn('No GPS fix - skipping')
            return

        recommendation = self.evaluate_ph(msg.ph)

        # Build row for CSV
        row = {
            'timestamp': f'{msg.header.stamp.sec}.{msg.header.stamp.nanosec}',
            'latitude': msg.latitude,
            'longitude': msg.longitude,
            'altitude': msg.altitude,
            'ph': msg.ph,
            'moisture': msg.moisture,
            'temperature': msg.temperature,
            'ec': msg.ec,
            'gps_status': msg.gps_status,
            'recommendation': recommendation
        }

        # Write to CSV immediately
        self.writer.writerow(row)
        self.csv_file.flush()

        self.measurements.append(row)

        self.get_logger().info(
            f'Measurement {len(self.measurements)}: '
            f'pH={msg.ph:.2f} | '
            f'moisture={msg.moisture:.1f}% | '
            f'EC={msg.ec:.2f} dS/m | '
            f'temp={msg.temperature:.1f}C | '
            f'at ({msg.latitude:.7f}, {msg.longitude:.7f}) | '
            f'{recommendation}'
        )

    def evaluate_ph(self, ph):
        if ph < 6.0:
            return 'Apply lime (acidic)'
        elif ph > 7.0:
            return 'No lime needed (alkaline)'
        else:
            return 'Optimal range'

    def destroy_node(self):
        self.csv_file.close()
        self.get_logger().info(
            f'Logged {len(self.measurements)} measurements to {self.log_path}')
        super().destroy_node()


def main():
    rclpy.init()
    node = SoilMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()