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
        self.match_timer = None  # Timer pour surveiller les 85s

        # 1. Configuration UI (Tirette, Couleur, Reset)
        qos = QoSProfile(depth=10, durability=DurabilityPolicy.VOLATILE)
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, qos)
        
        # 2. Clients Services & Actions
        self.ekf_client = self.create_client(SetPose, '/set_pose')
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # 3. STRATÉGIE LOGIQUE (Coordonnées pour le côté BLEU / X positif)
        self.waypoints = [
            {'pos': (1.25, 1.45, -1.57), 'zone_name': 'loading_v_top'},
            # {'pos': (0.7, 0.8, 3.14),  'zone_name': 'loading_h_mid'},
        ]

        self.zone_map = {
            'loading_v_top': ('16', '18'),
        }
        
        self.current_step = 0
        self.match_started = False
        self.prev_tirette = 1
        self.color = 0 # 0: Bleu, 1: Orange
        self.is_resetting = False
        
        # --- GESTION DU TEMPS EUROBOT ---
        self.match_start_time = None
        self.forced_return_triggered = False  # Évite d'envoyer l'ordre de retour en boucle
        
        self.pub_ready = self.create_publisher(Bool, '/wait_for_start', 10)

    def ui_callback(self, msg):
        if len(msg.data) < 3: 
            return
        self.color, reset_btn, tirette = msg.data[0], msg.data[1], msg.data[2]

        # Gestion du bouton Reset
        if reset_btn == 1:
            self.handle_reset()

        # Déclenchement du match sur front descendant de la tirette (1 -> 0)
        if tirette == 0 and self.prev_tirette == 1 and not self.match_started and not self.is_resetting:
            ready_msg = Bool()
            ready_msg.data = False
            self.pub_ready.publish(ready_msg)

            self.get_logger().info('!!! MATCH START !!!')
            self.match_started = True
            self.current_step = 0
            
            # Sauvegarde de l'heure exacte du début du match
            self.match_start_time = self.get_clock().now()
            self.forced_return_triggered = False
            
            # Lancement du timer de surveillance (s'exécute toutes les 0.5 secondes)
            self.match_timer = self.create_timer(0.5, self.match_time_check_callback)
            
            self.send_next_goal()

        self.prev_tirette = tirette

    def match_time_check_callback(self):
        """ Vérifie régulièrement si le temps limite des 85 secondes est dépassé """
        if not self.match_started or self.is_resetting or self.forced_return_triggered:
            return
            
        # Calcul du temps écoulé en secondes
        elapsed_time = (self.get_clock().now() - self.match_start_time).nanoseconds / 1e9
        
        # Condition fatidique : 85 secondes écoulées !
        if elapsed_time >= 85.0:
            self.get_logger().warn(f' Attention : {elapsed_time:.1f}s écoulées ! Rappel d\'urgence à la base.')
            self.forced_return_triggered = True
            
            # Interruption propre de l'action en cours
            if self.current_goal_handle is not None:
                self.get_logger().info("Annulation de la tâche Nav2 en cours pour retour d'urgence...")
                self.current_goal_handle.cancel_goal_async()
            
            # On force l'index de l'étape à l'étape finale (Retour Base)
            self.current_step = len(self.waypoints)+2
            self.send_next_goal()

    def handle_reset(self):
        if self.is_resetting: 
            return
        self.is_resetting = True    
        self.get_logger().info('Démarrage de la procédure de Reset...')

        # Destruction propre du timer de match
        if self.match_timer is not None:
            self.match_timer.destroy()
            self.match_timer = None

        ready_msg = Bool()
        ready_msg.data = False
        self.pub_ready.publish(ready_msg)
        
        if self.current_goal_handle is not None:
            self.get_logger().info('Annulation du but Nav2 en cours...')
            self.current_goal_handle.cancel_goal_async()
            self.current_goal_handle = None

        # Calcul de la Pose Home Symétrique
        x_home = 1.2 if self.color == 0 else -1.2
        y_home = 1.72
        yaw_home = -1.57

        req = SetPose.Request()
        req.pose.header.frame_id = 'map'
        req.pose.header.stamp = self.get_clock().now().to_msg()
        req.pose.pose.pose.position.x = x_home
        req.pose.pose.pose.position.y = y_home
        req.pose.pose.pose.orientation.z = math.sin(yaw_home / 2.0)
        req.pose.pose.pose.orientation.w = math.cos(yaw_home / 2.0)
        
        if self.ekf_client.service_is_ready():
            self.ekf_client.call_async(req)
        else:
            self.get_logger().warn("Le service /set_pose de l'EKF n'est pas prêt.")
    
        self.match_started = False
        self.current_step = 0
        self.forced_return_triggered = False
        
        if self.reset_timer is not None:
            self.reset_timer.destroy()
        self.reset_timer = self.create_timer(1.0, self.finish_reset_callback)
        
    def finish_reset_callback(self):
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
        if self.is_resetting:
            return

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        
        if self.current_step < len(self.waypoints):
            step = self.waypoints[self.current_step]
            raw_x, y, raw_yaw = step['pos']
            
            x = raw_x if self.color == 0 else -raw_x
            yaw = raw_yaw if self.color == 0 else math.atan2(math.sin(raw_yaw), -math.cos(raw_yaw))
            
            try:
                nav_share = get_package_share_directory('eirbot_navigation')
                goal.behavior_tree = os.path.join(nav_share, 'config', 'navigate_to_pose.xml')
            except Exception as e:
                self.get_logger().error(f"Impossible de trouver le package eirbot_navigation : {e}")
                return

            self.get_logger().info(f'Étape {self.current_step} : En route vers {step["zone_name"]} (X: {x:.2f}, Y: {y:.2f})')

        elif self.current_step == len(self.waypoints):
            # Étape finale : Retour à la base automatique (déclenché par la fin de liste ou par les 85s)
            x = 1.0 if self.color == 0 else -1.2
            y = 1.2
            yaw = -1.57
            self.get_logger().info('Deplacement vers la zone dattente pami')
            
        elif self.current_step == len(self.waypoints)+1:
            # attendre le retour en base à 85s 
            self.get_logger().info('Attente en base pour la fin du match (85s)...')
            return
            

        elif self.current_step == len(self.waypoints)+2:
            # Étape finale : Retour à la base automatique (déclenché par la fin de liste ou par les 85s)
            x = 1.2 if self.color == 0 else -1.2
            y = 1.7
            yaw = -1.57
            self.get_logger().info('Retour à la base de départ...')
        else:
            self.get_logger().info('!!! FIN DU MATCH !!! Le robot est à l\'arrêt permanent.')
            return

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

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
                self.get_logger().warn(f"Étape {self.current_step} ANNULÉE (Changement d'ordre ou Reset).")
            else:
                self.get_logger().error(f"Échec de l'étape {self.current_step} (Code : {status}). Passage à la suite...")
                self.current_step += 1
                self.send_next_goal()
        except Exception as e:
            self.get_logger().error(f"Erreur lors de la récupération du résultat : {e}")

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