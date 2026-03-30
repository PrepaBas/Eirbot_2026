#ifndef DIFFBOT_MICRO_ROS_HPP
#define DIFFBOT_MICRO_ROS_HPP

#include "hardware_interface/system_interface.hpp"
#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "sensor_msgs/msg/joint_state.hpp"

namespace diffbot_micro_ros
{
using hardware_interface::CallbackReturn;
using hardware_interface::return_type;

class DiffBotMicroRos : public hardware_interface::SystemInterface
{
public:
  CallbackReturn on_init(const hardware_interface::HardwareInfo & info) override;
  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;
  return_type read(const rclcpp::Time & time, const rclcpp::Duration & period) override;
  return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  // micro-ROS Communication
  rclcpp::Node::SharedPtr node_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr cmd_pub_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr state_sub_;

  // Memory buffers for the Controller Manager (Pointers)
  // Indices: 0 = Left, 1 = Right
  std::vector<double> hw_commands_;
  std::vector<double> hw_positions_;
  std::vector<double> hw_velocities_;
};
} 
#endif