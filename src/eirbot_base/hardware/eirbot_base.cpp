#include "eirbot_base.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

namespace eirbot_micro_ros
{

CallbackReturn EirBotMicroRos::on_init(const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // Initialize buffers (expecting 2 joints: left and right)
  hw_commands_.assign(info_.joints.size(), 0.0);
  hw_positions_.assign(info_.joints.size(), 0.0);
  hw_velocities_.assign(info_.joints.size(), 0.0);

  // Initialize the bridge node
  node_ = rclcpp::Node::make_shared("micro_ros_hw_interface");

  // Publisher: Sends robot-level Twist to ESP32
  cmd_pub_ = node_->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);

  // Subscriber: Receives joint states (encoder feedback) from ESP32
  state_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
    "/esp32/joint_states", 10,
    [this](const sensor_msgs::msg::JointState::SharedPtr msg) {
      // Ensure the received message has at least 2 joints
      if (msg->position.size() >= 2) {
        this->hw_positions_[0] = msg->position[0]; // Left
        this->hw_positions_[1] = msg->position[1]; // Right
        this->hw_velocities_[0] = msg->velocity[0];
        this->hw_velocities_[1] = msg->velocity[1];
      }
    });

  RCLCPP_INFO(node_->get_logger(), "Hardware Interface Initialized");
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
  // 1. Get commands from the diff_drive_controller (in rad/s per wheel)
  double v_left = hw_commands_[0];
  double v_right = hw_commands_[1];

  // 2. Convert Wheel Velocities -> Robot Twist (V and W)
  // This is the forward kinematics step
  auto msg = geometry_msgs::msg::Twist();
  msg.linear.x = (v_right + v_left) / 2.0;
  msg.angular.z = (v_right - v_left) / wheel_base_;

  // 3. Publish to ESP32
  cmd_pub_->publish(msg);
  
  return return_type::OK;
}

} // namespace eirbot_micro_ros

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(eirbot_micro_ros::EirBotMicroRos, hardware_interface::SystemInterface)