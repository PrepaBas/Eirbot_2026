import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from diffbot_control.diffbot_control.esp_driver import ESPDriver


class DiffDriveNode(Node):

    def __init__(self):
        super().__init__('diff_drive_node')

        # Parameters
        self.declare_parameter('wheel_base', 0.30)  # distance entre roues (m)
        self.declare_parameter('use_sim', True)
        self.declare_parameter('esp_port', '/dev/ttyUSB0')

        self.L = self.get_parameter('wheel_base').value
        self.use_sim = self.get_parameter('use_sim').value

        # ESC drivers (mode réel)
        if not self.use_sim:
            self.ucontroller = ESPDriver(
                port=self.get_parameter('esp_port').value
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
            self.send_to_esp(v_left, v_right)

    def simulate(self, v_left, v_right):
        self.get_logger().info(
            f"[SIM] left={v_left:.2f} m/s | right={v_right:.2f} m/s"
        )

    def send_to_esp(self, v_left, v_right):     
        self.ucontroller.set_speeds(v_left, v_right)


def main():
    rclpy.init()
    node = DiffDriveNode()
    rclpy.spin(node)
    rclpy.shutdown()
