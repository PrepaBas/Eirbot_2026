#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import Int8MultiArray
from eirbot_interfaces.action import Push
import time

class Homologation(Node):
    def __init__(self):
        super().__init__('homologation')
        
        # 1. Client pour ton Action Server de push
        self._action_client = ActionClient(self, Push, 'push_object')
        
        # 2. UI Subscriber (Color, Reset, Tirette)
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, 10)
        
        self.match_started = False
        self.prev_tirette = 1
        self.current_step = 0 # 0: Forward, 1: Backward

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        tirette = msg.data[2]

        # Déclenchement sur relâchement de tirette
        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.get_logger().info('--- DÉBUT HOMOLOGATION ---')
            self.match_started = True
            self.execute_step()

        self.prev_tirette = tirette

    def execute_step(self):
        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Push Server non disponible !')
            return

        goal_msg = Push.Goal()
        
        if self.current_step == 0:
            self.get_logger().info('Action : Avance de 0.5m à 0°')
            goal_msg.distance = 0.5
            goal_msg.speed = 0.2
            goal_msg.target_angle = 0.0 # On suppose que 0 est l'avant
        
        elif self.current_step == 1:
            self.get_logger().info('Action : Retour de 0.5m à 180°')
            goal_msg.distance = 0.5
            goal_msg.speed = 0.2
            goal_msg.target_angle = 180.0 # Demi-tour et revient
        else:
            self.get_logger().info('--- HOMOLOGATION TERMINEE ---')
            return

        send_goal_future = self._action_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal refusé par le serveur')
            return

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        if result.success:
            self.get_logger().info(f'Étape {self.current_step} réussie.')
            self.current_step += 1
            time.sleep(1.0) # Petite pause de sécurité
            self.execute_step()

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