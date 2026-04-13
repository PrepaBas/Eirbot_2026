#!/usr/bin/env python3
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
        # Conversion Quaternion vers Yaw
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)

    def get_angle_error(self, target_rad):
        return math.atan2(math.sin(target_rad - self.yaw), math.cos(target_rad - self.yaw))

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Push Action Started')
        
        dist_target = goal_handle.request.distance
        speed_target = goal_handle.request.speed
        target_rad = math.radians(goal_handle.request.target_angle)

        rate = self.create_rate(20) # 20Hz pour un contrôle fluide

        # --- 1. ALIGNEMENT PRÉCIS ---
        while rclpy.ok():
            error = self.get_angle_error(target_rad)
            if abs(math.degrees(error)) < 0.5: # Tolérance plus fine
                break
            
            msg = Twist()
            # On utilise un gain P (0.4) et on sature la vitesse minimale pour vaincre les frottements
            p_term = 0.5 * error
            min_rot = 0.15 if error > 0 else -0.15
            msg.angular.z = max(min(p_term, 0.5), -0.5) + min_rot
            
            self.cmd_pub.publish(msg)
            rate.sleep()

        self.cmd_pub.publish(Twist()) # Stop rotation
        self.get_logger().info('Aligned. Starting Translation...')

        # --- 2. POUSSÉE AVEC MAINTIEN DE CAP ---
        start_x, start_y = self.x, self.y
        feedback_msg = Push.Feedback()

        while rclpy.ok():
            dist_moved = math.sqrt((self.x - start_x)**2 + (self.y - start_y)**2)
            
            # Feedback
            feedback_msg.partial_distance = dist_moved
            goal_handle.publish_feedback(feedback_msg)

            if dist_moved >= dist_target:
                break

            # Correction de cap (Heading Lock)
            angle_error = self.get_angle_error(target_rad)
            
            msg = Twist()
            msg.linear.x = speed_target
            msg.angular.z = 1.0 * angle_error # Gain correctif pour rester droit malgré les obstacles
            
            self.cmd_pub.publish(msg)
            rate.sleep()

        # Stop final
        self.cmd_pub.publish(Twist())
        goal_handle.succeed()
        
        result = Push.Result()
        result.success = True
        return result

def main():
    rclpy.init()
    node = PushActionServer()
    # Le MultiThreadedExecutor permet de recevoir l'Odom pendant que l'Action tourne
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()