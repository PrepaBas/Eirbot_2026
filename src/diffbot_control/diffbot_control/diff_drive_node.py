import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from diffbot_control.esc_driver import ESCDriver


class DiffDriveNode(Node):

    def __init__(self):
        super().__init__('diff_drive_node')

        # Parameters
        self.declare_parameter('wheel_base', 0.30)  # distance entre roues (m)
        self.declare_parameter('use_sim', True)
        self.declare_parameter('left_esc_port', '/dev/ttyUSB0')
        self.declare_parameter('right_esc_port', '/dev/ttyUSB1')

        self.L = self.get_parameter('wheel_base').value
        self.use_sim = self.get_parameter('use_sim').value

        # ESC drivers (mode réel)
        if not self.use_sim:
            self.left_esc = ESCDriver(
                self.get_parameter('left_esc_port').value
            )
            self.right_esc = ESCDriver(
                self.get_parameter('right_esc_port').value
            )

        # Subscriber
        self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info(
            f"DiffDriveNode started (use_sim={self.use_sim})"
        )

    def cmd_vel_callback(self, msg: Twist):
        v = msg.linear.x
        w = msg.angular.z

        v_left = v - (w * self.L / 2.0)
        v_right = v + (w * self.L / 2.0)

        if self.use_sim:
            self.simulate(v_left, v_right)
        else:
            self.send_to_esc(v_left, v_right)

    def simulate(self, v_left, v_right):
        self.get_logger().info(
            f"[SIM] left={v_left:.2f} m/s | right={v_right:.2f} m/s"
        )

    def send_to_esc(self, v_left, v_right):
        self.left_esc.set_speed(v_left)
        self.right_esc.set_speed(v_right)


def main():
    rclpy.init()
    node = DiffDriveNode()
    rclpy.spin(node)
    rclpy.shutdown()
