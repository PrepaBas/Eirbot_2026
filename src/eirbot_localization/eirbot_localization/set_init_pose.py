import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
import time

def main():
    rclpy.init()
    node = rclpy.create_node('initial_pose_setter')
    
    # Utilisation de la QoS "transient_local" comme dans RViz pour plus de fiabilité
    from rclpy.qos import QoSProfile, QoSDurabilityPolicy
    qos = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
    
    pub = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', qos)
    
    msg = PoseWithCovarianceStamped()
    msg.header.frame_id = 'map'
    msg.header.stamp = node.get_clock().now().to_msg()
    
    # Position
    msg.pose.pose.position.x = 1.2
    msg.pose.pose.position.y = 1.7
    
    # Orientation : Sois explicite pour éviter les surprises
    msg.pose.pose.orientation.x = 0.0
    msg.pose.pose.orientation.y = 0.0
    msg.pose.pose.orientation.z = 0.0
    msg.pose.pose.orientation.w = 1.0 # 0 radian (tout droit)

    # Covariance ultra-faible pour forcer le saut (On utilise la notation scientifique)
    cov = [0.0] * 36
    cov[0]  = 0.0 # X
    cov[7]  = 0.0 # Y
    
    cov[35] = 0.0# Yaw (Theta)
    msg.pose.covariance = cov
    
    # Petite attente pour laisser le temps au publisher de se connecter
    time.sleep(1.0)
    
    node.get_logger().info("Publishing Initial Pose...")
    pub.publish(msg)
    
    time.sleep(0.3)
    
    node.get_logger().info("Publishing Initial Pose...")
    pub.publish(msg)
    
    time.sleep(0.3)
    node.get_logger().info("Publishing Initial Pose...")
    pub.publish(msg)
    
    time.sleep(0.3)
    node.get_logger().info("Publishing Initial Pose...")
    pub.publish(msg)
    
    time.sleep(0.3)
    node.get_logger().info("Publishing Initial Pose...")
    pub.publish(msg)
    
    time.sleep(0.3)

    # On laisse un peu de temps pour que le message parte avant de tuer le node
    time.sleep(0.5)
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()