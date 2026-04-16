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

        # 1. Configuration UI (Tirette et Reset)
        qos = QoSProfile(
            depth=10,
            durability=DurabilityPolicy.VOLATILE # <-- Changement ici
        )
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, qos)
        
        # 2. Clients
        self.ekf_client = self.create_client(SetPose, '/set_pose')
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Client pour supprimer les formes (Local Costmap)
        self.remove_shape_client = self.create_client(RemoveShape, '/global_costmap/virtual_layer/remove_shape')
        self.reload_shapes_client = self.create_client(Trigger, '/global_costmap/virtual_layer/reload_shapes')

        self.clear_global_costmap = self.create_client(ClearEntireCostmap, '/global_costmap/clear_entirely_global_costmap')
        self.clear_local_costmap = self.create_client(ClearEntireCostmap, '/local_costmap/clear_entirely_local_costmap')

        # 3. STRATÉGIE
        # Note : 'zone' doit correspondre à l'ID (identifier) défini dans ton YAML
        self.waypoints = [
            {'pos': (1.25, 1.45, -1.57), 'zone': '16'},
            {'pos': (0.7, 0.8, 3.14),    'zone': '12'},
            {'pos': (0.8, 0.25, 3.14),   'zone': '11'},
        ]
        
        # 4. Variables de contrôle
        self.current_step = 0
        self.match_started = False
        self.prev_tirette = 1
        self.color = 0 # 0: Bleu, 1: Orange
        self.is_resetting = False

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        self.color, reset_btn, tirette = msg.data[0], msg.data[1], msg.data[2]

        if reset_btn == 1:
            self.handle_reset()

        if reset_btn == 0:
            self.reset_block = 0

        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.get_logger().info('MATCH START')
            self.match_started = True
            self.current_step = 0
            self.send_next_goal()

        self.prev_tirette = tirette

    def handle_reset(self):
        if self.is_resetting:
            return  # On ignore si un reset est déjà en cours
        
        self.is_resetting = True    
        self.get_logger().info('Reset démarré...')

        # 3. Nettoyer les Costmaps (pour enlever les fantômes d'obstacles)
        #if self.clear_global_costmap.service_is_ready():
        #    self.clear_global_costmap.call_async(ClearEntireCostmap.Request())
        #if self.clear_local_costmap.service_is_ready():
        #    self.clear_local_costmap.call_async(ClearEntireCostmap.Request())


        if self.current_goal_handle is not None:
            self.current_goal_handle.cancel_goal_async()
            self.current_goal_handle = None
            self.get_logger().info('Objectif Nav2 annulé.')

        req = SetPose.Request()
        req.pose.header.frame_id = 'map'
        req.pose.header.stamp = self.get_clock().now().to_msg()
        
        # Position Home
        x_home = -1.2 if self.color == 0 else 1.2
        y_home = 1.7
        yaw_home = -1.57

        req.pose.pose.pose.position.x = x_home
        req.pose.pose.pose.position.y = y_home
        req.pose.pose.pose.orientation.z = math.sin(yaw_home / 2.0)
        req.pose.pose.pose.orientation.w = math.cos(yaw_home / 2.0)
        req.pose.pose.covariance = [0.01 if i in [0, 7, 35] else 0.0 for i in range(36)]

        self.ekf_client.call_async(req)
        self.get_logger().info('Reset Pose executed')

        # virtual zones
        if self.reload_shapes_client.service_is_ready():
            req = Trigger.Request()
            self.reload_shapes_client.call_async(req)
            self.get_logger().info('Zones virtuelles rechargées depuis le YAML')

        self.match_started = False
        self.current_step = 0

        self.reset_timer = self.create_timer(2.0, self.finish_reset_callback)

    def finish_reset_callback(self):
        # On détruit le timer immédiatement pour qu'il ne tourne qu'une fois
        self.reset_timer.destroy()
        self.is_resetting = False
        self.get_logger().info('Reset terminé, verrou levé.')

    def remove_virtual_zone(self, zone_identifier):
        """ Supprime la zone via le service nav2_virtual_layer """
        if not self.remove_shape_client.service_is_ready():
            self.get_logger().warn(f'Service de suppression non prêt pour {zone_identifier}')
            return

        req = RemoveShape.Request()
        req.identifier = zone_identifier
        
        self.get_logger().info(f'Suppression zone virtuelle : {zone_identifier}')
        self.remove_shape_client.call_async(req)

    def send_next_goal(self):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        
        # ÉTAPES DE LA MISSION
        if self.current_step < len(self.waypoints):
            step = self.waypoints[self.current_step]
            x, y, yaw = step['pos']
            
            nav_share = get_package_share_directory('eirbot_navigation')
            goal.behavior_tree = os.path.join(nav_share, 'config', 'navigate_to_pose.xml')
            self.get_logger().info(f'Objectif {self.current_step} envoyé')

        # RETOUR À LA BASE
        elif self.current_step == len(self.waypoints):
            x = -1.2 if self.color == 0 else 1.2
            y = 1.7
            yaw = -1.57
            # On laisse goal.behavior_tree vide pour la navigation simple
            self.get_logger().info('Retour Home en cours...')

        else:
            self.get_logger().info('Mission terminée.')
            return

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.nav_client.wait_for_server()
        self.nav_client.send_goal_async(goal).add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.current_goal_handle = future.result() # On stocke le handle ici
        if not self.current_goal_handle.accepted:
            self.get_logger().error('Objectif refusé')
            return
        self.current_goal_handle.get_result_async().add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        if future.result().status == 4: # STATUS_SUCCEEDED
            # 1. On supprime la zone de la carte si elle existe pour cette étape
            if self.current_step < len(self.waypoints):
                zone_id = self.waypoints[self.current_step]['zone']
                self.remove_virtual_zone(zone_id)

            # 2. On passe à l'étape suivante
            self.current_step += 1
            self.send_next_goal()

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