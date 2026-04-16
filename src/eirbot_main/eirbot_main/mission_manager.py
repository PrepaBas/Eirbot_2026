#!/usr/bin/env python3
import os
import rclpy
import math
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from rclpy.action import ActionClient

# Messages Standards
from std_msgs.msg import Int8MultiArray
from nav2_msgs.action import NavigateToPose
from robot_localization.srv import SetPose
from ament_index_python.packages import get_package_share_directory

# Message spécifique pour le Virtual Layer
from nav2_virtual_layer.srv import RemoveShape
from std_srvs.srv import Trigger
from nav2_msgs.srv import ClearEntireCostmap

class MissionManager(Node):
    def __init__(self):
        super().__init__('mission_manager')
        
        self.current_goal_handle = None

        # 1. Configuration UI
        qos = QoSProfile(depth=10, durability=DurabilityPolicy.VOLATILE)
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, qos)
        
        # 2. Clients
        self.ekf_client = self.create_client(SetPose, '/set_pose')
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.remove_shape_client = self.create_client(RemoveShape, '/global_costmap/virtual_layer/remove_shape')
        self.reload_shapes_client = self.create_client(Trigger, '/global_costmap/virtual_layer/reload_shapes')

        # 3. STRATÉGIE LOGIQUE (Coordonnées pour le côté BLEU / X positif)
        self.waypoints = [
            {'pos': (1.25, 1.45, -1.57), 'zone_name': 'loading_v_top'},
            {'pos': (0.7, 0.8, 3.14),  'zone_name': 'loading_h_mid'},
            {'pos': (0.8, 0.25, 3.14),  'zone_name': 'loading_h_bot'},

            {'pos': (-0.7, 0.8, 3.14),  'zone_name': 'loading_h_mid_mirror'},
            {'pos': (-0.8, 0.25, 3.14),  'zone_name': 'loading_h_bot_mirror'},
        ]

        # Mapping des IDs (Bleu, Orange)
        self.zone_map = {
            'loading_v_top': ('16', '18'),
            'loading_h_mid': ('12', '14'),
            'loading_h_bot': ('11', '13'),
            'loading_h_mid_mirror': ('14', '12'),
            'loading_h_bot_mirror': ('13', '11'),

            'start_cleanup': (['2', '4', '7', '8'], ['7', '8', '2', '4']),
        }
        
        self.current_step = 0
        self.match_started = False
        self.prev_tirette = 1
        self.color = 0 # 0: Bleu, 1: Orange
        self.is_resetting = False

    def get_target_id(self, zone_name):
        if zone_name in self.zone_map:
            ids = self.zone_map[zone_name]
            return ids[0] if self.color == 0 else ids[1]
        return None

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        self.color, reset_btn, tirette = msg.data[0], msg.data[1], msg.data[2]

        if reset_btn == 1:
            self.handle_reset()

        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.get_logger().info('!!! MATCH START !!!')
            self.match_started = True
            self.current_step = 0
            self.send_next_goal()

        self.prev_tirette = tirette

    def handle_reset(self):
        if self.is_resetting: return
        self.is_resetting = True    
        self.get_logger().info('Reset en cours...')

        # Annulation navigation en cours
        if self.current_goal_handle is not None:
            self.current_goal_handle.cancel_goal_async()

        # Calcul Pose Home Symétrique
        x_home = 1.2 if self.color == 0 else -1.2
        y_home = 1.7
        yaw_home = -1.57

        req = SetPose.Request()
        req.pose.header.frame_id = 'map'
        req.pose.header.stamp = self.get_clock().now().to_msg()
        req.pose.pose.pose.position.x = x_home
        req.pose.pose.pose.position.y = y_home
        req.pose.pose.pose.orientation.z = math.sin(yaw_home / 2.0)
        req.pose.pose.pose.orientation.w = math.cos(yaw_home / 2.0)
        
        self.ekf_client.call_async(req)
        
        if self.reload_shapes_client.service_is_ready():
            self.reload_shapes_client.call_async(Trigger.Request())
    
        cleanup_ids = self.zone_map['start_cleanup'][0] if self.color == 0 else self.zone_map['start_cleanup'][1]
        for zone_id in cleanup_ids:
            if self.remove_shape_client.service_is_ready():
                req = RemoveShape.Request()
                req.identifier = zone_id
                self.remove_shape_client.call_async(req)
                self.get_logger().info(f'Zone de départ {zone_id} supprimée.')

        self.match_started = False
        self.current_step = 0
        self.create_timer(1.0, self.finish_reset_callback)
        
    def finish_reset_callback(self, *args):
        # On cherche le timer dans les arguments variables
        for arg in args:
            if hasattr(arg, 'destroy'):
                arg.destroy()
        self.is_resetting = False
        self.get_logger().info('Reset terminé, robot prêt.')

    def send_next_goal(self):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        
        if self.current_step < len(self.waypoints):
            step = self.waypoints[self.current_step]
            raw_x, y, raw_yaw = step['pos']
            
            # --- SYMÉTRIE ---
            x = raw_x if self.color == 0 else -raw_x
            yaw = raw_yaw if self.color == 0 else math.atan2(math.sin(raw_yaw), -math.cos(raw_yaw))
            
            nav_share = get_package_share_directory('eirbot_navigation')
            goal.behavior_tree = os.path.join(nav_share, 'config', 'navigate_to_pose.xml')
            self.get_logger().info(f'Étape {self.current_step} : Vers {step["zone_name"]}')

        elif self.current_step == len(self.waypoints):
            x = 1.2 if self.color == 0 else -1.2
            y = 1.7
            yaw = -1.57
            self.get_logger().info('Retour à la base...')
        else:
            return

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.nav_client.wait_for_server()
        self.nav_client.send_goal_async(goal).add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.current_goal_handle = future.result()
        if not self.current_goal_handle.accepted: return
        self.current_goal_handle.get_result_async().add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        if future.result().status == 4: # SUCCEEDED
            if self.current_step < len(self.waypoints):
                z_name = self.waypoints[self.current_step]['zone_name']
                t_id = self.get_target_id(z_name)
                if t_id:
                    req = RemoveShape.Request()
                    req.identifier = t_id
                    self.remove_shape_client.call_async(req)

            self.current_step += 1
            self.send_next_goal()

def main():
    rclpy.init()
    node = MissionManager()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()