import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from std_msgs.msg import Int8MultiArray
from std_srvs.srv import Empty
from robot_localization.srv import SetPose
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
import math

class MissionManager(Node):
    def __init__(self):
        super().__init__('mission_manager')
        
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.sub = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, qos)
        
        self.ekf_client = self.create_client(SetPose, '/set_pose')
        self.clear_global = self.create_client(Empty, '/global_costmap/clear_entirely_global_costmap')
        self.clear_local = self.create_client(Empty, '/local_costmap/clear_entirely_local_costmap')
        
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        self.goal_handle = None
        self.prev_reset_btn = 0
        self.prev_tirette = 1
        self.match_started = False

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        
        color, reset_btn, tirette = msg.data[0], msg.data[1], msg.data[2]

        if reset_btn == 1 and self.prev_reset_btn == 0:
            self.get_logger().info('Action: RESET')
            self.handle_reset(color)
        
        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.get_logger().info('Action: MATCH START')
            self.match_started = True
            self.start_strategy()

        self.prev_reset_btn = reset_btn
        self.prev_tirette = tirette

    def handle_reset(self, color):
        # Annulation propre de l'objectif Nav2 si existant
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
            self.goal_handle = None
        
        # Set Pose EKF
        req = SetPose.Request()
        req.pose.header.frame_id = 'map'
        req.pose.header.stamp = self.get_clock().now().to_msg()
        if color == 0: # Bleu
            req.pose.pose.pose.position.x, req.pose.pose.pose.position.y = -1.20, 1.70
            req.pose.pose.pose.orientation.w = 1.0
        else: # Orange
            req.pose.pose.pose.position.x, req.pose.pose.pose.position.y = 1.20, 1.70
            req.pose.pose.pose.orientation.z, req.pose.pose.pose.orientation.w = 1.0, 0.0
        
        req.pose.pose.covariance = [1e-9 if i%7==0 else 0.0 for i in range(36)]
        self.ekf_client.call_async(req)
        
        self.clear_global.call_async(Empty.Request())
        self.clear_local.call_async(Empty.Request())
        self.match_started = False

    def start_strategy(self):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.pose.position.x = 0.0
        goal.pose.pose.position.y = 1.0
        goal.pose.pose.orientation.w = 1.0
        
        self.get_logger().info('Sending goal to Nav2...')
        send_goal_future = self.nav_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        self.get_logger().info('Goal accepted')

def main():
    rclpy.init()
    rclpy.spin(MissionManager())
    rclpy.shutdown()