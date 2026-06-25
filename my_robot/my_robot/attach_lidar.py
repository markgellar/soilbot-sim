import rclpy
from rclpy.node import Node
from gazebo_msgs.msg import ModelState, ModelStates
from tf2_ros import Buffer, TransformListener


class LidarAttacher(Node):

    def __init__(self):
        super().__init__('lidar_attacher')

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.publisher = self.create_publisher(
            ModelState, '/gazebo/set_model_state', 10)

        self.timer = self.create_timer(0.05, self.update_pose)
        self.get_logger().info('LiDAR attacher started')

    def update_pose(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                'odom', 'os1_lidar_link', rclpy.time.Time())

            msg = ModelState()
            msg.model_name = 'os1_sensor_model'
            msg.pose.position.x = transform.transform.translation.x
            msg.pose.position.y = transform.transform.translation.y
            msg.pose.position.z = transform.transform.translation.z
            msg.pose.orientation = transform.transform.rotation
            msg.reference_frame = 'world'

            self.publisher.publish(msg)

        except Exception:
            pass


def main():
    rclpy.init()
    node = LidarAttacher()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
