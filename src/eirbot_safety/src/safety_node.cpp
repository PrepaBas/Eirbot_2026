#include "eirbot_safety/safety_node.hpp"
#include <algorithm>

using namespace std::chrono_literals; // <--- Règle l'erreur sur "500ms"

namespace eirbot_safety {

SafetyNode::SafetyNode(const rclcpp::NodeOptions & options)
: Node("safety_node", options) {
    this->declare_parameter("stop_distance", 0.4);
    stop_dist_ = this->get_parameter("stop_distance").as_double();

    // Initialisation du temps pour éviter un arrêt d'urgence au premier cycle
    last_scan_time_ = this->now();

    sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
        "/scan", 10, std::bind(&SafetyNode::scan_callback, this, std::placeholders::_1));

    pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel_safety", 10);

    // Le timer est maintenant déclaré dans le .hpp, donc pas d'erreur de scope
    watchdog_timer_ = this->create_wall_timer(
        500ms, std::bind(&SafetyNode::check_watchdog, this));
}

void SafetyNode::scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg) {
    this->get_parameter("stop_distance", stop_dist_);
    last_scan_time_ = this->now();

    bool obstacle = std::any_of(msg->ranges.begin(), msg->ranges.end(),
        [this, msg](float r) {
            return (r > msg->range_min && r < (float)stop_dist_);
        });

    if (obstacle) {
        auto stop_msg = geometry_msgs::msg::Twist();
        pub_->publish(stop_msg);
        RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 500, "Obstacle détecté !");
    }
}

// Correction : On reste dans le namespace et on précise bien "SafetyNode::"
void SafetyNode::check_watchdog() {
    auto age = this->now() - last_scan_time_;
    if (age.seconds() > 0.5) {
        RCLCPP_ERROR(this->get_logger(), "LIDAR DISCONNECTED! Emergency stop.");
        auto stop_msg = geometry_msgs::msg::Twist();
        pub_->publish(stop_msg);
    }
}

}  // namespace eirbot_safety

// Le main est TOUJOURS en dehors du namespace
int main(int argc, char ** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<eirbot_safety::SafetyNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}