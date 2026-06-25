import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class LimeRecommender(Node):

    def __init__(self):
        super().__init__('lime_recommender')
        self.subscription = self.create_subscription(
            Float32,
            '/soil/ph',
            self.ph_callback,
            10)
        self.get_logger().info('Lime recommender node started')

    def ph_callback(self, msg):
        ph = msg.data
        recommendation = self.evaluate_ph(ph)
        self.get_logger().info(f'pH: {ph} -> {recommendation}')

    def evaluate_ph(self, ph):
        if ph < 6.0:
            return f'Apply lime: soil is acidic (pH {ph})'
        elif ph > 7.0:
            return f'No lime needed: soil is alkaline (pH {ph})'
        else:
            return f'Optimal range: no action needed (pH {ph})'

def main():
    rclpy.init()
    node = LimeRecommender()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
