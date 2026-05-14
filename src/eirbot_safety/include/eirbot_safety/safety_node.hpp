#ifndef EIRBOT_SAFETY__SAFETY_NODE_HPP_
#define EIRBOT_SAFETY__SAFETY_NODE_HPP_

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/range.hpp"  // <--- Nouveau type de message
#include "geometry_msgs/msg/twist.hpp"
#include <chrono>
#include <vector>

namespace eirbot_safety {

class SafetyNode : public rclcpp::Node {
public:
    explicit SafetyNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());

private:
    // Callback mis à jour pour le message Range
    void range_callback(const sensor_msgs::msg::Range::SharedPtr msg, const std::string & topic_name);
    void check_watchdog();

    // Vecteur de souscriptions pour accepter plusieurs capteurs
    std::vector<rclcpp::Subscription<sensor_msgs::msg::Range>::SharedPtr> subs_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr watchdog_timer_;

    double stop_dist_;
    rclcpp::Time last_range_time_;
    
    // Flag global pour savoir si l'un des capteurs détecte un problème
    bool obstacle_detected_; 
};

}  // namespace eirbot_safety

#endif  // EIRBOT_SAFETY__SAFETY_NODE_HPP_