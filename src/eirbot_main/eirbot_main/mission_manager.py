#!/usr/bin/env python3
import os
import rclpy
import math
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from rclpy.action import ActionClient

# Messages Standards
from std_msgs.msg import Bool, Int8MultiArray
from nav2_msgs.action import NavigateToPose
from robot_localization.srv import SetPose
from ament_index_python.packages import get_package_share_directory

class MissionManager(Node):
    def __init__(self):
        super().__init__('mission_manager')
        
        self.current_goal_handle = None
        self.reset_timer = None

        # 1. Configuration UI (Tirette, Couleur, Reset)
        qos = QoSProfile(depth=10, durability=DurabilityPolicy.VOLATILE)
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, qos)
        
        # 2. Clients Services & Actions
        self.ekf_client = self.create_client(SetPose, '/set_pose')
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # 3. STRATÉGIE LOGIQUE (Coordonnées de base pour le côté BLEU / X positif)
        self.waypoints = [
            {'pos': (1.25, 1.45, -1.57), 'zone_name': 'loading_v_top'},
            {'pos': (0.7, 0.8, 3.14),  'zone_name': 'loading_h_mid'},
            # {'pos': (0.8, 0.25, 3.14),  'zone_name': 'loading_h_bot'},

            #{'pos': (-0.7, 0.8, 0.0),  'zone_name': 'loading_h_mid_mirror'},
            #{'pos': (-0.8, 0.25, 0.0),  'zone_name': 'loading_h_bot_mirror'},
        
        ]

        # Mapping des IDs de zones pour traitement futur (Ex: Virtual Layer)
        self.zone_map = {
            'loading_v_top': ('16', '18'),
        }
        
        self.current_step = 0
        self.match_started = False
        self.prev_tirette = 1
        self.color = 0 # 0: Bleu, 1: Orange
        self.is_resetting = False

        
        self.pub_ready = self.create_publisher(Bool, '/wait_for_start', 10)

    def ui_callback(self, msg):
        if len(msg.data) < 3: 
            return
        self.color, reset_btn, tirette = msg.data[0], msg.data[1], msg.data[2]

        # Gestion du bouton Reset
        if reset_btn == 1:
            self.handle_reset()

        # Déclenchement du match sur front descendant de la tirette
        if tirette == 0 and self.prev_tirette == 1 and not self.match_started and not self.is_resetting:

            ready_msg = Bool()
            ready_msg.data = False
            self.pub_ready.publish(ready_msg)

            self.get_logger().info('!!! MATCH START !!!')
            self.match_started = True
            self.current_step = 0
            self.send_next_goal()

        self.prev_tirette = tirette

    def handle_reset(self):
        if self.is_resetting: 
            return
        self.is_resetting = True    
        self.get_logger().info('Démarrage de la procédure de Reset...')


        ready_msg = Bool()
        ready_msg.data = False
        self.pub_ready.publish(ready_msg)
        
        # 1. Annulation propre et immédiate de la navigation en cours
        if self.current_goal_handle is not None:
            self.get_logger().info('Annulation du but Nav2 en cours...')
            self.current_goal_handle.cancel_goal_async()
            self.current_goal_handle = None

        # 2. Calcul de la Pose Home Symétrique
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
        
        # Validation de la disponibilité de l'EKF pour éviter de bloquer le thread
        if self.ekf_client.service_is_ready():
            self.ekf_client.call_async(req)
        else:
            self.get_logger().warn("Le service /set_pose de l'EKF n'est pas prêt. Position non réinitialisée.")
    
        self.match_started = False
        self.current_step = 0
        
        # 3. Fixation du Timer One-Shot de manière robuste
        if self.reset_timer is not None:
            self.reset_timer.destroy()
        self.reset_timer = self.create_timer(1.0, self.finish_reset_callback)
        
    def finish_reset_callback(self):
        # Destruction immédiate du timer pour garantir l'effet "One-Shot"
        if self.reset_timer is not None:
            self.reset_timer.destroy()
            self.reset_timer = None

        if self.is_resetting:
            self.get_logger().info('Reset terminé avec succès. Robot prêt à partir.')
        self.is_resetting = False

        ready_msg = Bool()
        ready_msg.data = True
        self.pub_ready.publish(ready_msg)

    def send_next_goal(self):
        # Sécurité : Ne pas envoyer de cible si on est en cours de reset
        if self.is_resetting:
            return

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        
        if self.current_step < len(self.waypoints):
            step = self.waypoints[self.current_step]
            raw_x, y, raw_yaw = step['pos']
            
            # --- SYMÉTRIE DE CONFIGURATION ---
            x = raw_x if self.color == 0 else -raw_x
            # Formule de miroir stable pour l'axe X (Côté Orange)
            yaw = raw_yaw if self.color == 0 else math.atan2(math.sin(raw_yaw), -math.cos(raw_yaw))
            
            try:
                nav_share = get_package_share_directory('eirbot_navigation')
                goal.behavior_tree = os.path.join(nav_share, 'config', 'navigate_to_pose.xml')
            except Exception as e:
                self.get_logger().error(f"Impossible de trouver le package eirbot_navigation : {e}")
                return

            self.get_logger().info(f'Étape {self.current_step} : En route vers {step["zone_name"]} (X: {x:.2f}, Y: {y:.2f})')

        elif self.current_step == len(self.waypoints):
            # Étape finale : Retour à la base
            x = 1.2 if self.color == 0 else -1.2
            y = 1.7
            yaw = -1.57
            self.get_logger().info('Toutes les étapes validées. Retour à la base de départ...')
        else:
            self.get_logger().info('!!! FIN DU MATCH !!! Le robot est à l\'arrêt permanent.')
            return

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        # Attente asynchrone non-bloquante du serveur d'action Nav2
        if not self.nav_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error("Le serveur d'action 'navigate_to_pose' de Nav2 ne répond pas !")
            return

        self.nav_client.send_goal_async(goal).add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        try:
            self.current_goal_handle = future.result()
            if not self.current_goal_handle.accepted:
                self.get_logger().warn(f"Le but pour l'étape {self.current_step} a été REFUSÉ par Nav2.")
                return
            
            self.current_goal_handle.get_result_async().add_done_callback(self.get_result_callback)
        except Exception as e:
            self.get_logger().error(f"Erreur lors de la réponse du serveur d'action : {e}")

    def get_result_callback(self, future):
        try:
            status = future.result().status
            if status == 4:  # STATUS_SUCCEEDED
                self.get_logger().info(f"Étape {self.current_step} ATTEINTE.")
                self.current_step += 1
                self.send_next_goal()
            elif status == 5:  # STATUS_CANCELED
                self.get_logger().warn(f"Étape {self.current_step} ANNULÉE (Reset demandé ?).")
            else:
                self.get_logger().error(f"Échec ou Abandon de l'étape {self.current_step} (Code : {status}). Passage à l'étape suivante...")
                self.current_step += 1
                self.send_next_goal()
        except Exception as e:
            self.get_logger().error(f"Erreur lors de la récupération du résultat de navigation : {e}")

def main():
    rclpy.init()
    node = MissionManager()
    try: 
        rclpy.spin(node)
    except KeyboardInterrupt: 
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()