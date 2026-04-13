#include "eirbot_base.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

namespace eirbot_base
{

CallbackReturn EirBotMicroRos::on_init(const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // Initialize buffers
  hw_commands_.assign(2, 0.0);
  hw_positions_.assign(2, 0.0);
  hw_velocities_.assign(2, 0.0);

  // Setup Bridge Node
  node_ = rclcpp::Node::make_shared("micro_ros_hw_interface");

  // Publish to ESP32: [left_vel, right_vel]
  cmd_pub_ = node_->create_publisher<std_msgs::msg::Float64MultiArray>("/esp32/wheel_cmds", 10);

  // Subscribe from ESP32: Standard JointState (pos/vel)
  state_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
    "/esp32/joint_states", 10,
    [this](const sensor_msgs::msg::JointState::SharedPtr msg) {
      if (msg->name.size() >= 2) {
        this->hw_positions_[0] = msg->position[0];
        this->hw_positions_[1] = msg->position[1];
        this->hw_velocities_[0] = msg->velocity[0];
        this->hw_velocities_[1] = msg->velocity[1];
      }
    });

  return CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> EirBotMicroRos::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;
  for (size_t i = 0; i < info_.joints.size(); i++) {
    state_interfaces.emplace_back(info_.joints[i].name, hardware_interface::HW_IF_POSITION, &hw_positions_[i]);
    state_interfaces.emplace_back(info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_velocities_[i]);
  }
  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> EirBotMicroRos::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  for (size_t i = 0; i < info_.joints.size(); i++) {
    command_interfaces.emplace_back(info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_commands_[i]);
  }
  return command_interfaces;
}

return_type EirBotMicroRos::read(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Process incoming subscriber messages
  rclcpp::spin_some(node_);
  return return_type::OK;
}

return_type EirBotMicroRos::write(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Take the pointers from the controller and publish them to micro-ROS
  auto msg = std_msgs::msg::Float64MultiArray();
  msg.data = {hw_commands_[0], hw_commands_[1]};
  cmd_pub_->publish(msg);
  
  return return_type::OK;
}

} // namespace eirbot_micro_ros

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(eirbot_base::EirBotMicroRos, hardware_interface::SystemInterface)