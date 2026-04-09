import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math
import time

class PushActionNode(Node):
    def __init__(self):
        super().__init__('push_action_node')
        self.cmd_pub = self.create_publisher(Twist, '/eirbot_base_controller/cmd_vel_unstamped', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry/filtered', self.odom_callback, 10)
        
        self.current_yaw = 0.0
        self.current_x = 0.0
        self.current_y = 0.0

    def odom_callback(self, msg):
        # On récupère la position
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        # On convertit le quaternion en angle Yaw (radians)
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def align_to_angle(self, target_yaw_deg, tolerance_deg=1.5):
        """ Aligne le robot sur un angle précis avant de pousser """
        target_yaw = math.radians(target_yaw_deg)
        self.get_logger().info(f"Alignement vers {target_yaw_deg}°...")

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            error = target_yaw - self.current_yaw
            
            # Normalisation de l'erreur entre -pi et pi
            error = (error + math.pi) % (2 * math.pi) - math.pi

            if abs(math.degrees(error)) < tolerance_deg:
                break
            
            msg = Twist()
            # Vitesse proportionnelle à l'erreur (P-Controller simple)
            msg.angular.z = 0.5 * error 
            # On sature la vitesse pour ne pas brusquer les moteurs
            msg.angular.z = max(min(msg.angular.z, 0.6), -0.6)
            
            self.cmd_pub.publish(msg)

        self.cmd_pub.publish(Twist()) # Stop
        self.get_logger().info("Alignement terminé !")

    def start_push(self, distance, speed, target_angle):
        # 1. On s'aligne parfaitement d'abord
        self.align_to_angle(target_angle)
        
        # 2. On attend que l'EKF se stabilise
        time.sleep(0.2)
        
        # 3. On pousse (en utilisant l'angle actuel pour rester droit)
        self.get_logger().info("Poussée en cours...")
        start_x = self.current_x
        start_y = self.current_y
        
        msg = Twist()
        msg.linear.x = speed
        
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            # Calcul de la distance parcourue via Pythagore
            dist_moved = math.sqrt((self.current_x - start_x)**2 + (self.current_y - start_y)**2)
            
            if dist_moved >= distance:
                break
                
            self.cmd_pub.publish(msg)
            
        self.cmd_pub.publish(Twist())
        self.get_logger().info("Action terminée !")

def main():
    rclpy.init()
    node = PushActionNode()
    
    # Simulation d'un signal : dans la vraie vie, ce serait 
    # appelé par un Behavior Tree ou un timer de match
    time.sleep(2) 
    node.start_push(distance=0.3, speed=0.15, target_angle=90.0)
    
    node.destroy_node()
    rclpy.shutdown()