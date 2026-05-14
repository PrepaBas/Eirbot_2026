#include "eirbot_safety/safety_node.hpp"
#include <algorithm>

using namespace std::chrono_literals;

namespace eirbot_safety {

SafetyNode::SafetyNode(const rclcpp::NodeOptions & options)
: Node("safety_node", options), obstacle_detected_(false) {
    
    this->declare_parameter("stop_distance", 0.4); // en mètres
    stop_dist_ = this->get_parameter("stop_distance").as_double();

    last_range_time_ = this->now(); // Devient last_range_time_ dans le hpp

    // --- CONFIGURATION DES TOPICS DE CAPTEURS ---
    // Tu peux ajouter ici tous les topics de tes ToF ou Ultrasons
    std::vector<std::string> range_topics = {
        "/hardware/ultrasons", 
        // "/hardware/tof_gauche", 
        // "/hardware/tof_droit"
    };

    // Création dynamique des abonnements avec passage du nom du topic au callback
    for (const auto & topic : range_topics) {
        auto sub = this->create_subscription<sensor_msgs::msg::Range>(
            topic, 10, 
            [this, topic](const sensor_msgs::msg::Range::SharedPtr msg) {
                this->range_callback(msg, topic);
            });
        subs_.push_back(sub);
    }

    pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel_safety", 10);

    watchdog_timer_ = this->create_wall_timer(
        500ms, std::bind(&SafetyNode::check_watchdog, this));
}

void SafetyNode::range_callback(const sensor_msgs::msg::Range::SharedPtr msg, const std::string & topic_name) {
    last_range_time_ = this->now();
    float current_range = msg->range;

    // 1. Filtrage des valeurs aberrantes (Out-of-range)
    if (current_range < msg->min_range || current_range > msg->max_range) {
        return; // On ignore la mesure
    }

    // 2. Logique de confirmation (Exemple simple)
    // On n'arrête le robot que si on a au moins 2 mesures de suite sous le seuil
    static int low_range_count = 0;

    if (current_range < (float)stop_dist_) {
        low_range_count++;
    } else {
        low_range_count = 0;
        obstacle_detected_ = false;
    }

    if (low_range_count >= 2) { // Confirmation après 2 mesures (soit ~40ms)
        obstacle_detected_ = true;
        auto stop_msg = geometry_msgs::msg::Twist();
        pub_->publish(stop_msg);
        
        RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 500, 
            "OBSTACLE CONFIRMÉ par %s : %.2f m", topic_name.c_str(), current_range);
    }
}

void SafetyNode::check_watchdog() {
    auto age = this->now() - last_range_time_;
    
    // Si aucun capteur n'a publié depuis plus de 0.5 seconde -> Arrêt d'urgence
    if (age.seconds() > 0.5) {
        RCLCPP_ERROR(this->get_logger(), "RANGE SENSORS TIMEOUT! Emergency stop.");
        auto stop_msg = geometry_msgs::msg::Twist();
        pub_->publish(stop_msg);
    }
}

}  // namespace eirbot_safety

int main(int argc, char ** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<eirbot_safety::SafetyNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}