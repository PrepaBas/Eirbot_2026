#!/usr/bin/env python3
import os
import rclpy
import math
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from rclpy.action import ActionClient

# Messages
from std_msgs.msg import Int8MultiArray
from nav2_msgs.action import NavigateToPose
from robot_localization.srv import SetPose
from ament_index_python.packages import get_package_share_directory
# IMPORTANT : Remplace 'tu_package_interfaces' par le vrai nom du package de ton service
from eirbot_interfaces.srv import StringID # Exemple, adapte selon ton type de service

class MissionManager(Node):
    def __init__(self):
        super().__init__('mission_manager')

        # 1. Configuration UI (Tirette et Reset)
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, qos)
        
        # 2. Clients Services et Actions
        self.ekf_client = self.create_client(SetPose, '/set_pose')
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        # Client pour supprimer les formes du Virtual Layer
        self.remove_shape_client = self.create_client(StringID, '/local_costmap/virtual_layer/remove_shape')

        # 3. STRATÉGIE (x, y, yaw, zone_id)
        # zone_id est l'ID défini dans ton YAML que l'on veut supprimer APRES l'étape
        self.waypoints = [
            {'pos': (1.25, 1.45, -1.57), 'zone': 'load_v2'},
            {'pos': (0.7, 0.8, 3.14),    'zone': 'load_h2'},
            {'pos': (0.8, 0.25, 3.14),   'zone': 'load_h1'},
        ]
        
        # 4. Variables de contrôle
        self.current_step = 0
        self.match_started = False
        self.prev_tirette = 1
        self.color = 0 # 0: Bleu, 1: Orange

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        self.color, reset_btn, tirette = msg.data[0], msg.data[1], msg.data[2]

        if reset_btn == 1:
            self.handle_reset()

        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.get_logger().info('--- MATCH START ---')
            self.match_started = True
            self.current_step = 0
            self.send_next_goal()

        self.prev_tirette = tirette

    def handle_reset(self):
        self.match_started = False
        self.current_step = 0
        req = SetPose.Request()
        req.pose.header.frame_id = 'map'
        req.pose.header.stamp = self.get_clock().now().to_msg()
        
        # Position Home selon couleur
        x_home = -1.2 if self.color == 0 else 1.2
        y_home = 1.7
        yaw_home = -1.57

        req.pose.pose.pose.position.x = x_home
        req.pose.pose.pose.position.y = y_home
        req.pose.pose.pose.orientation.z = math.sin(yaw_home / 2.0)
        req.pose.pose.pose.orientation.w = math.cos(yaw_home / 2.0)
        req.pose.pose.covariance = [0.01 if i in [0, 7, 35] else 0.0 for i in range(36)]

        self.ekf_client.call_async(req)
        self.get_logger().info(f'Reset EKF (Color: {"Orange" if self.color else "Blue"})')

    def remove_virtual_zone(self, zone_id):
        """ Appelle le service pour supprimer la zone de la costmap """
        if not self.remove_shape_client.service_is_ready():
            self.get_logger().warn('Service remove_shape non disponible')
            return

        req = StringID.Request() # Adapte le type ici
        req.id = zone_id
        self.remove_shape_client.call_async(req)
        self.get_logger().info(f'Zone {zone_id} retirée de la carte.')

    def send_next_goal(self):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        
        # CAS A : Waypoints Tactiques (Navigation + Push)
        if self.current_step < len(self.waypoints):
            step = self.waypoints[self.current_step]
            x, y, yaw = step['pos']
            
            # Utilise ton BT personnalisé qui contient l'Action PUSH
            nav_share = get_package_share_directory('eirbot_navigation')
            goal.behavior_tree = os.path.join(nav_share, 'config', 'navigate_to_pose.xml')
            self.get_logger().info(f'Exécution étape {self.current_step} : {x}, {y}')

        # CAS B : Retour à la Maison (Navigation Simple)
        elif self.current_step == len(self.waypoints):
            x = -1.2 if self.color == 0 else 1.2
            y = 1.7
            yaw = -1.57
            # On ne définit pas goal.behavior_tree -> Nav2 utilise le BT par défaut (simple)
            self.get_logger().info('Toutes étapes finies. Retour au bercail...')

        # CAS C : Mission terminée
        else:
            self.get_logger().info('MATCH TERMINÉ - Robot à la base.')
            return

        # Remplissage orientation
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.nav_client.wait_for_server()
        future = self.nav_client.send_goal_async(goal)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Objectif refusé par Nav2')
            return
        
        self.get_logger().info('Objectif accepté, en attente du résultat...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        if status == 4: # SUCCEEDED
            # Si on vient de finir un waypoint tactique, on supprime sa zone virtuelle
            if self.current_step < len(self.waypoints):
                zone_id = self.waypoints[self.current_step]['zone']
                self.remove_virtual_zone(zone_id)

            self.current_step += 1
            self.send_next_goal()
        else:
            self.get_logger().warn(f'Action échouée (Status: {status}). On sature ici.')

def main():
    rclpy.init()
    node = MissionManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()