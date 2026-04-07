import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from tf2_ros import TransformBroadcaster
import math

class PoseBroadcaster(Node):
    def __init__(self):
        super().__init__('pose_broadcaster')
        self.br = TransformBroadcaster(self)
        
        # Paramètres par défaut Eurobot
        self.declare_parameter('initial_x', -1.2)
        self.declare_parameter('initial_y', 1.75)
        self.declare_parameter('initial_yaw', -1.75)

        self.x = self.get_parameter('initial_x').value
        self.y = self.get_parameter('initial_y').value
        self.yaw = self.get_parameter('initial_yaw').value

        self.subscription = self.create_subscription(
            PoseWithCovarianceStamped, '/initialpose', self.handle_initial_pose, 10)

        self.timer = self.create_timer(0.05, self.broadcast_tf)
        self.get_logger().info("Pose Broadcaster prêt. Cliquez sur '2D Pose Estimate' dans RViz.")

    def handle_initial_pose(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        # Conversion manuelle Quaternion -> Yaw (2D)
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)
        
        self.get_logger().info(f"Position mise à jour : x={self.x:.2f}, y={self.y:.2f}, yaw={self.yaw:.2f}")

    def broadcast_tf(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'map'
        t.child_frame_id = 'odom'
        
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0

        # Conversion manuelle Yaw (2D) -> Quaternion
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(self.yaw / 2.0)
        t.transform.rotation.w = math.cos(self.yaw / 2.0)

        self.br.sendTransform(t)

def main():
    rclpy.init()
    node = PoseBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()