#include <string>
#include <memory>

#include "behaviortree_cpp_v3/bt_factory.h"
#include "nav2_behavior_tree/bt_action_node.hpp"
#include "eirbot_interfaces/action/push.hpp"

namespace eirbot_actions
{
// On hérite de BtActionNode qui gère déjà 90% du travail (connexion au serveur d'action)
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

  // Cette méthode s'exécute juste avant d'envoyer la requête au serveur Python
  void on_tick() override
  {
    // On récupère les valeurs depuis le XML (Blackboard)
    // Si elles ne sont pas fournies, on met des valeurs par défaut
    getInput("distance", goal_.distance);
    getInput("speed", goal_.speed);
    getInput("target_angle", goal_.target_angle);
  }

  // Définition des ports (paramètres acceptés par la balise XML)
  static BT::PortsList providedPorts()
  {
    return providedBasicPorts(
      {
        BT::InputPort<float>("distance", 0.3, "Distance à parcourir"),
        BT::InputPort<float>("speed", 0.15, "Vitesse de poussée"),
        BT::InputPort<float>("target_angle", 0.0, "Angle d'alignement")
      });
  }
};

}  // namespace eirbot_actions

// Enregistrement du plugin pour qu'il soit visible par Nav2
BT_REGISTER_NODES(factory)
{
  BT::NodeBuilder builder =
    [](const std::string & name, const BT::NodeConfiguration & config)
    {
      return std::make_unique<eirbot_actions::PushAction>(name, "push_object", config);
    };

  factory.registerBuilder<eirbot_actions::PushAction>("Push", builder);
}