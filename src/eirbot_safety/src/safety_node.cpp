#include "eirbot_safety/safety_node.hpp"
#include <algorithm>

namespace eirbot_safety {

SafetyNode::SafetyNode(const rclcpp::NodeOptions & options)
: Node("safety_node", options) {
    this->declare_parameter("stop_distance", 0.4);
    stop_dist_ = this->get_parameter("stop_distance").as_double();

    sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
        "/scan", 10, std::bind(&SafetyNode::scan_callback, this, std::placeholders::_1));

    pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel_safety", 10);

    auto age = this->now() - last_scan_time_;
    watchdog_timer_ = this->create_wall_timer(
        500ms, std::bind(&SafetyNode::check_watchdog, this));
}

void SafetyNode::scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg) {
    // On rafraîchit le paramètre au cas où il ait été changé dynamiquement
    this->get_parameter("stop_distance", stop_dist_);
    last_scan_time_ = this->now(); // On enregistre l'heure du dernier scan

    bool obstacle = std::any_of(msg->ranges.begin(), msg->ranges.end(),
        [this, msg](float r) {
            return (r > msg->range_min && r < stop_dist_);
        });

    if (obstacle) {
        auto stop_msg = geometry_msgs::msg::Twist(); // Tout à 0.0
        pub_->publish(stop_msg);
        RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 500, "Obstacle !");
    }
}

}  // namespace eirbot_safety

void SafetyNode::check_watchdog() {
    auto age = this->now() - last_scan_time_;
    if (age.seconds() > 0.5) {
        RCLCPP_ERROR(this->get_logger(), "LIDAR DISCONNECTED! Emergency stop.");
        auto stop_msg = geometry_msgs::msg::Twist();
        pub_->publish(stop_msg);
    }
}

// Main pour l'exécutable
int main(int argc, char ** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<eirbot_safety::SafetyNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}