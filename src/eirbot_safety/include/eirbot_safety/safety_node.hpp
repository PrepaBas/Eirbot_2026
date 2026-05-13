#ifndef EIRBOT_SAFETY__SAFETY_NODE_HPP_
#define EIRBOT_SAFETY__SAFETY_NODE_HPP_

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include <chrono>

namespace eirbot_safety {

class SafetyNode : public rclcpp::Node {
public:
    explicit SafetyNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());

private:
    void scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg);
    void check_watchdog();

    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr sub_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr watchdog_timer_; // <--- Le compilateur le veut ici !

    double stop_dist_;
    rclcpp::Time last_scan_time_;
};

}  // namespace eirbot_safety

#endif  // EIRBOT_SAFETY__SAFETY_NODE_HPP_