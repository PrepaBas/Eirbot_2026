import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from eirbot_interfaces.action import Push
import math

class PushActionServer(Node):
    def __init__(self):
        super().__init__('push_server')
        self._action_server = ActionServer(
            self, Push, 'push_object', self.execute_callback)
        
        self.cmd_pub = self.create_publisher(Twist, '/eirbot_base_controller/cmd_vel_unstamped', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry/filtered', self.odom_callback, 10)
        
        self.x, self.y, self.yaw = 0.0, 0.0, 0.0

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

    def align(self, target_deg):
        target_rad = math.radians(target_deg)
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.05)
            error = math.atan2(math.sin(target_rad - self.yaw), math.cos(target_rad - self.yaw))
            if abs(math.degrees(error)) < 1.5: break
            
            msg = Twist()
            msg.angular.z = max(min(0.5 * error, 0.6), -0.6)
            self.cmd_pub.publish(msg)
        self.cmd_pub.publish(Twist())

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Requête Push reçue')
        
        # Extraction des paramètres du goal
        dist_target = goal_handle.request.distance
        speed = goal_handle.request.speed
        angle = goal_handle.request.target_angle

        # 1. Alignement
        self.align(angle)

        # 2. Poussée
        start_x, start_y = self.x, self.y
        feedback_msg = Push.Feedback()
        
        move_msg = Twist()
        move_msg.linear.x = speed

        while rclpy.ok():
            dist_moved = math.sqrt((self.x - start_x)**2 + (self.y - start_y)**2)
            
            # Envoi du feedback au BT
            feedback_msg.partial_distance = dist_moved
            goal_handle.publish_feedback(feedback_msg)

            if dist_moved >= dist_target: break
            
            self.cmd_pub.publish(move_msg)
            rclpy.spin_once(self, timeout_sec=0.05)

        self.cmd_pub.publish(Twist())
        goal_handle.succeed()
        
        result = Push.Result()
        result.success = True
        return result

def main():
    rclpy.init()
    node = PushActionServer()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()