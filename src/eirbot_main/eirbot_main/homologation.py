#!/usr/bin/env python3
import os
import rclpy
import math
import time
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Int8MultiArray
from ament_index_python.packages import get_package_share_directory

class Homologation(Node):
    def __init__(self):
        super().__init__('homologation')
        
        # 1. Configuration des chemins
        try:
            self.nav_share = get_package_share_directory('eirbot_navigation')
            # Remplace 'main_tree.xml' par le nom réel de ton fichier dans eirbot_navigation/config/
            self.bt_path = os.path.join(self.nav_share, 'config', 'navigate_to_pose.xml')
        except Exception as e:
            self.get_logger().error(f'Impossible de trouver le package eirbot_navigation: {e}')

        # 2. UI Subscriber
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, 10)
        
        # 3. Nav2 Action Client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Variables d'état
        self.color = 0 
        self.match_started = False
        self.prev_tirette = 1
        self.current_step = 0 

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        self.color = msg.data[0]
        tirette = msg.data[2]

        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.get_logger().info('--- DÉMARRAGE HOMOLOGATION ---')
            self.match_started = True
            self.execute_sequence()

        self.prev_tirette = tirette

    def execute_sequence(self):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        
        # On spécifie le Behavior Tree à utiliser (celui avec le noeud PUSH)
        goal.behavior_tree = self.bt_path

        side = 1.0 if self.color == 0 else -1.0
        
        # Points de passage pour l'homologation
        if self.current_step == 0: 
            # Aller vers l'avant (Nav2 s'arrêtera, puis fera le PUSH et le BACKUP du BT)
            x, y, yaw = (1.2 * side), 1.0, -1.57
            self.get_logger().info('Etape 1: Navigation + PUSH')
        
        elif self.current_step == 1:
            # Retour à la base
            x, y, yaw = (1.2 * side), 1.7, -1.57
            self.get_logger().info('Etape 2: RETOUR MAISON')
        else:
            self.get_logger().info('--- HOMOLOGATION RÉUSSIE ---')
            return

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.get_logger().info(f'Envoi objectif: x={x}, y={y}')
        self.nav_client.wait_for_server()
        self.nav_client.send_goal_async(goal).add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Objectif refusé par Nav2')
            return
        goal_handle.get_result_async().add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        if future.result().status == 4: # SUCCESS
            self.current_step += 1
            time.sleep(1.0) 
            self.execute_sequence()
        else:
            self.get_logger().warn('Échec de l’étape, nouvelle tentative dans 2s...')
            time.sleep(2.0)
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