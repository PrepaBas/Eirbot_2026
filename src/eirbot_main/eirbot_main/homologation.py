#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int8MultiArray
import time

class SimplePushTest(Node):
    def __init__(self):
        super().__init__('simple_push_test')
        
        # Publisher vers le multiplexeur (on utilise le channel nav)
        self.publisher = self.create_publisher(Twist, '/cmd_vel_nav', 10)
        
        # UI Subscriber pour la tirette
        self.sub_ui = self.create_subscription(Int8MultiArray, '/hardware/switches', self.ui_callback, 10)
        
        self.prev_tirette = 1
        self.match_started = False

    def ui_callback(self, msg):
        if len(msg.data) < 3: return
        tirette = msg.data[2]

        if tirette == 0 and self.prev_tirette == 1 and not self.match_started:
            self.match_started = True
            self.run_test()

        self.prev_tirette = tirette

    def send_twist(self, linear_x, duration):
        """Envoie une commande de vitesse pendant X secondes"""
        msg = Twist()
        msg.linear.x = linear_x
        
        end_time = time.time() + duration
        while time.time() < end_time:
            self.publisher.publish(msg)
            time.sleep(0.1) # Fréquence de 10Hz
            
        # Arrêt
        msg.linear.x = 0.0
        self.publisher.publish(msg)

    def run_test(self):
        self.get_logger().info('DÉBUT DU TEST : AVANT')
        self.send_twist(0.2, 2.0)  # Avance à 0.2 m/s pendant 2s (~40cm)
        
        self.get_logger().info('PAUSE')
        time.sleep(1.0)
        
        self.get_logger().info('RETOUR : ARRIÈRE')
        self.send_twist(-0.2, 2.0) # Recule pendant 2s
        
        self.get_logger().info('TEST TERMINÉ')
        self.match_started = False

def main():
    rclpy.init()
    node = SimplePushTest()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()