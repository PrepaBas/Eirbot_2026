import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
from std_msgs.msg import Header

class StrategyNode(Node):
    def __init__(self):
        super().__init__('strategy_node')
        
        # 1. Nav2 Action Client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # 2. Obstacle Publisher
        self.obstacle_pub = self.create_publisher(PointCloud2, '/virtual_obstacles', 10)
        
        # --- State Variables ---
        self.sequence = [(1.2, 1.75), (-1.2, 1.75)]  # Example sequence of goals
        self.current_step = 0
        self.is_moving = False
        self.match_finished = False
        
        # Game Data
        self.game_elements = {
            "store_1": (0, 0.1),
            "store_2": (0.8, 0.1),
            "store_3": (0, 0.8),
            "store_4": (0.7, 0.8),
            "store_5": (1.4, 0.8),


            "store_2m": (-0.8, 0.1),
            "store_4m": (-0.7, 0.8),
            "store_5m": (-1.4, 0.8),

            "load_h1": (0.400, 0.175),
            "load_h2": (0.35, 0.8),

            "load_h1m": (-0.400, 0.175),
            "load_h2m": (-0.35, 0.8),

            "load_v1" : (1.35, 0.400),
            "load_v2" : (1.35, 1.2),
            "load_v1m" : (-1.35, 0.400),
            "load_v2m" : (-1.35, 1.2),
        }
        self.active_obstacles_store = ["store_1", "store_2", "store_3", "store_4", "store_5", "store_2m", "store_4m", "store_5m" ]
        self.active_obstacles_vload = ["load_v1", "load_v2", "load_v1m", "load_v2m"]
        self.active_obstacles_hload = ["load_h1", "load_h2", "load_h1m", "load_h2m"]
        
        # --- Timers ---
        self.start_time = self.get_clock().now()
        self.create_timer(0.1, self.publish_virtual_walls)
        self.create_timer(0.5, self.run_strategy) # Check strategy every 0.5s
        self.create_timer(0.1, self.check_match_timer)

    def check_match_timer(self):
        """Emergency stop after 90 seconds."""
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        if elapsed >= 90.0 and not self.match_finished:
            self.get_logger().warn("--- 90 SECONDS UP: STOPPING ROBOT ---")
            self.match_finished = True
            self.nav_client.cancel_all_goals()
            # In a real match, you might also trigger a 'Funny Action' here

    def publish_virtual_walls(self):
        """Publishes coordinates for Nav2 to avoid."""
        points = []
        for name in self.active_obstacles_store:
            x_base, y_base = self.game_elements[name]
            for dx in [-0.1, 0.0, 0.1]:
                for dy in [-0.1, 0.0, 0.1]:
                    points.append([float(x_base + dx), float(y_base + dy), 0.0])
                        
        for name in self.active_obstacles_hload:
            x_base, y_base = self.game_elements[name]
            for dx in [-0.1, 0.0, 0.1]:
                for dy in [-0.075, 0.0, 0.075]:
                    points.append([float(x_base + dx), float(y_base + dy), 0.0])
        
        for name in self.active_obstacles_vload:
            x_base, y_base = self.game_elements[name]
            for dx in [-0.075, 0.0, 0.075]:
                for dy in [-0.1, 0.0, 0.1]:
                    points.append([float(x_base + dx), float(y_base + dy), 0.0])


        # Use 'map' as the frame since your coordinates are absolute table coords
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = "map" 
        
        cloud = pc2.create_cloud_xyz32(header, points)
        self.obstacle_pub.publish(cloud)

    def run_strategy(self):
        """The main brain of the robot."""
        if self.is_moving or self.match_finished:
            return 

        if self.current_step < len(self.sequence):
            target = self.sequence[self.current_step]
            self.go_to_pose(target[0], target[1])
        else:
            self.get_logger().info("All tasks complete. Waiting for match end.")

    def go_to_pose(self, x, y):
        """Sends goal and sets up callbacks to know when it's done."""
        self.is_moving = True
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = "map"
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.w = 1.0
        
        self.get_logger().info(f"Navigating to {x}, {y}...")
        self.nav_client.wait_for_server()
        
        send_goal_future = self.nav_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected!")
            self.is_moving = False
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        """Triggered when the robot physically arrives."""
        self.get_logger().info(f"Step {self.current_step} complete!")
        
        # Example: Remove the obstacle after reaching the first goal
        if self.current_step == 0 and "store_1" in self.active_obstacles_store:
            self.active_obstacles_store.remove("store_1")
            self.get_logger().info("Store 1 cleared from map!")

        self.is_moving = False
        self.current_step += 1

def main():
    rclpy.init()
    node = StrategyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()