#include <string>
#include <memory>
#include <cmath>

#include "behaviortree_cpp_v3/bt_factory.h"
#include "nav2_behavior_tree/bt_action_node.hpp"
#include "eirbot_interfaces/action/push.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"

// Nécessaire pour la conversion Quaternion -> Euler
#include "tf2/LinearMath/Quaternion.h"
#include "tf2/LinearMath/Matrix3x3.h"

namespace eirbot_actions
{
class PushAction : public nav2_behavior_tree::BtActionNode<eirbot_interfaces::action::Push>
{
public:
  PushAction(
    const std::string & xml_tag_name,
    const std::string & action_name,
    const BT::NodeConfiguration & conf)
  : BtActionNode<eirbot_interfaces::action::Push>(xml_tag_name, action_name, conf)
  {
  }

  void on_tick() override
  {
    // 1. Récupération des paramètres simples
    getInput("distance", goal_.distance);
    getInput("speed", goal_.speed);

    // 2. Extraction de l'angle depuis la pose "goal"
    geometry_msgs::msg::PoseStamped goal_pose;
    if (getInput("goal", goal_pose)) {
        
        // Conversion du quaternion en Euler
        tf2::Quaternion q(
            goal_pose.pose.orientation.x,
            goal_pose.pose.orientation.y,
            goal_pose.pose.orientation.z,
            goal_pose.pose.orientation.w);
        
        tf2::Matrix3x3 m(q);
        double roll, pitch, yaw;
        m.getRPY(roll, pitch, yaw);

        // On convertit en degrés si ton serveur Python attend des degrés
        // Eurobot utilise souvent les degrés pour la lisibilité, Nav2 les radians.
        float yaw_deg = static_cast<float>(yaw * 180.0 / M_PI);
        
        goal_.target_angle = yaw_deg;
        
        RCLCPP_INFO(node_->get_logger(), "Push target angle extracted from goal: %.2f deg", yaw_deg);
    } else {
        RCLCPP_WARN(node_->get_logger(), "Push: goal pose not provided, using default angle 0.0");
        goal_.target_angle = 0.0;
    }
  }

  static BT::PortsList providedPorts()
  {
    return providedBasicPorts(
      {
        // On définit "goal" comme un port d'entrée obligatoire pour l'angle
        BT::InputPort<geometry_msgs::msg::PoseStamped>("goal", "Pose d'objectif pour extraire l'angle"),
        BT::InputPort<float>("distance", 0.3, "Distance à parcourir"),
        BT::InputPort<float>("speed", 0.15, "Vitesse de poussée"),
      });
  }
};

}  // namespace eirbot_actions

BT_REGISTER_NODES(factory)
{
  BT::NodeBuilder builder =
    [](const std::string & name, const BT::NodeConfiguration & config)
    {
      // "push_object" est le nom du serveur d'action ROS 2 (le nom dans ton push_server.py)
      return std::make_unique<eirbot_actions::PushAction>(name, "push_object", config);
    };

  factory.registerBuilder<eirbot_actions::PushAction>("Push", builder);
}