#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Int8MultiArray
import math
import time

class Homologation(Node):
    def __init__(self):
        super().__init__('homologation')
        
        # UI Subscriber (Color, Reset, Tirette)
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, 10)
        
        # Nav2 Client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # State variables
        self.color = 0 # 0: Bleu, 1: Orange
        self.match_started = False
        self.prev_tirette = 1
        self.current_step = 0 # 0: Push, 1: Turn, 2: Back, 3: Home

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        self.color = msg.data[0]
        tirette = msg.data[2]

        # Trigger on Tirette Release (1 -> 0)
        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.get_logger().info('--- TEST START ---')
            self.match_started = True
            self.execute_sequence()

        self.prev_tirette = tirette

    def execute_sequence(self):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()

        # Simple Logic relative to starting point (assumed 1.2, 1.7 for Blue)
        # We adjust X based on color
        side = 1.0 if self.color == 0 else -1.0
        
        if self.current_step == 0: # PUSH forward
            x, y, yaw = (1.2 * side), 1.0, -1.57
            self.get_logger().info('Action: PUSHING FORWARD')
        
        elif self.current_step == 1: # TURN 180 (Point North)
            x, y, yaw = (1.2 * side), 1.0, 1.57 
            self.get_logger().info('Action: TURNING 180')

        elif self.current_step == 2: # BACK (Moving to Y 1.3 while facing North)
            x, y, yaw = (1.2 * side), 1.3, 1.57
            self.get_logger().info('Action: BACKING UP')

        elif self.current_step == 3: # HOME
            x, y, yaw = (1.2 * side), 1.7, -1.57
            self.get_logger().info('Action: GOING HOME')
        else:
            self.get_logger().info('TEST COMPLETE')
            return

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.get_logger().info(f'Sending Goal: x={x}, y={y}')
        self.nav_client.wait_for_server()
        self.nav_client.send_goal_async(goal).add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal Rejected')
            return
        goal_handle.get_result_async().add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        if future.result().status == 4: # SUCCESS
            self.current_step += 1
            # Small pause between actions for mechanical stability
            time.sleep(0.5) 
            self.execute_sequence()

def main():
    rclpy.init()
    node = Homologation()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()