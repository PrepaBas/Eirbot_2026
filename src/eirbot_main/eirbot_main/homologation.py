#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import Int8MultiArray

# On importe l'action spécifique de ton push_server
# (Vérifie le nom exact de ton interface d'action, ici supposé 'Push')
from eirbot_interfaces.action import Push 

class HomologationDirectPush(Node):
    def __init__(self):
        super().__init__('homologation_direct_push')
        
        # 1. Client pour ton serveur de push
        self.push_client = ActionClient(self, Push, 'push')
        
        # 2. UI Subscriber pour la tirette
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, 10)
        
        self.prev_tirette = 1
        self.match_started = False

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        tirette = msg.data[2]

        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.get_logger().info('--- START PUSH TEST (Action Server) ---')
            self.match_started = True
            self.send_push_goal(0.4) # Avance de 40cm

        self.prev_tirette = tirette

    def send_push_goal(self, distance):
        self.get_logger().info(f'Envoi de la commande Push : {distance}m')
        
        goal_msg = Push.Goal()
        goal_msg.distance = distance
        # goal_msg.speed = 0.2  # Ajoute si ton interface le supporte

        self.push_client.wait_for_server()
        self.push_client.send_goal_async(goal_msg).add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Commande Push refusée par le serveur')
            return
        goal_handle.get_result_async().add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        if status == 4: # SUCCESS
            self.get_logger().info('Push terminé. Retour en arrière...')
            # Optionnel : Envoyer un push négatif pour reculer si ton serveur le permet
            self.send_push_goal(-0.4) 
        else:
            self.get_logger().error(f'Erreur Action : Status {status}')
            self.match_started = False

def main():
    rclpy.init()
    node = HomologationDirectPush()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()