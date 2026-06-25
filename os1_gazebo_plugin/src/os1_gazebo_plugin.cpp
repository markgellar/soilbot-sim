// OS1 Gazebo Plugin — Option C
// A Gazebo Classic MODEL plugin that connects to a <sensor type="ray"> already
// defined on a URDF link, converts the ray data to sensor_msgs/PointCloud2,
// and publishes it via a standalone rclcpp::Node.
//
// WHY THIS EXISTS:
// The standard libgazebo_ros_ray_sensor.so requires a <remapping> tag whose
// `:=` syntax breaks gazebo_ros2_control's internal YAML parser, preventing
// the controller manager from starting. This plugin avoids that entirely —
// the topic name is set via a plain <topic_name> parameter.

#include <functional>
#include <string>
#include <cmath>
#include <mutex>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/sensors/sensors.hh>
#include <gazebo/common/common.hh>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/point_cloud2_iterator.hpp>

namespace os1_gazebo
{

class OS1GazeboPlugin : public gazebo::ModelPlugin
{
public:
  OS1GazeboPlugin() = default;
  ~OS1GazeboPlugin() override
  {
    if (update_conn_)
      update_conn_.reset();
    if (sensor_conn_)
      sensor_conn_.reset();
  }

  void Load(gazebo::physics::ModelPtr model, sdf::ElementPtr sdf) override
  {
    model_ = model;

    // ---- Read SDF parameters (set in the URDF <plugin> block) ----
    if (sdf->HasElement("sensor_name"))
      sensor_name_ = sdf->Get<std::string>("sensor_name");
    else
      sensor_name_ = "os1_sensor";

    if (sdf->HasElement("topic_name"))
      topic_name_ = sdf->Get<std::string>("topic_name");
    else
      topic_name_ = "/ouster/points";

    if (sdf->HasElement("frame_name"))
      frame_name_ = sdf->Get<std::string>("frame_name");
    else
      frame_name_ = "os1_lidar_link";

    if (sdf->HasElement("min_intensity"))
      min_intensity_ = sdf->Get<double>("min_intensity");

    // ---- Create a standalone rclcpp node (NOT gazebo_ros::Node) ----
    if (!rclcpp::ok())
      rclcpp::init(0, nullptr);

    node_ = std::make_shared<rclcpp::Node>("os1_gazebo_plugin_node");
    pub_ = node_->create_publisher<sensor_msgs::msg::PointCloud2>(
      topic_name_, rclcpp::SensorDataQoS());

    RCLCPP_INFO(node_->get_logger(),
      "OS1 plugin loaded — looking for sensor '%s', will publish on '%s'",
      sensor_name_.c_str(), topic_name_.c_str());

    // ---- Deferred sensor lookup on every world update tick ----
    // The sensor may not be registered yet when Load() runs.
    update_conn_ = gazebo::event::Events::ConnectWorldUpdateBegin(
      std::bind(&OS1GazeboPlugin::OnUpdate, this));
  }

private:
  // ------------------------------------------------------------------
  // Called every simulation step. Used for:
  //   1. Deferred sensor discovery (first few ticks)
  //   2. Spinning rclcpp so publishers/subscribers work
  // ------------------------------------------------------------------
  void OnUpdate()
  {
    // --- Sensor discovery (runs until sensor is found) ---
    if (!ray_sensor_)
    {
      auto *mgr = gazebo::sensors::SensorManager::Instance();

      for (auto &link : model_->GetLinks())
      {
        for (unsigned int i = 0; i < link->GetSensorCount(); ++i)
        {
          std::string scoped = link->GetSensorName(i);
          if (scoped.find(sensor_name_) != std::string::npos)
          {
            auto sensor = mgr->GetSensor(scoped);
            ray_sensor_ = std::dynamic_pointer_cast<gazebo::sensors::RaySensor>(sensor);

            if (!ray_sensor_)
            {
              // Try GpuRaySensor
              gpu_ray_sensor_ = std::dynamic_pointer_cast<gazebo::sensors::GpuRaySensor>(sensor);
              if (gpu_ray_sensor_)
              {
                gpu_ray_sensor_->SetActive(true);
                sensor_conn_ = gpu_ray_sensor_->ConnectUpdated(
                  std::bind(&OS1GazeboPlugin::OnScanGpu, this));
                RCLCPP_INFO(node_->get_logger(),
                  "Attached to GPU ray sensor: %s", scoped.c_str());
              }
            }
            else
            {
              ray_sensor_->SetActive(true);
              sensor_conn_ = ray_sensor_->ConnectUpdated(
                std::bind(&OS1GazeboPlugin::OnScan, this));
              RCLCPP_INFO(node_->get_logger(),
                "Attached to CPU ray sensor: %s", scoped.c_str());
            }
            break;
          }
        }
        if (ray_sensor_ || gpu_ray_sensor_)
          break;
      }
    }

    // Keep rclcpp alive
    if (rclcpp::ok())
      rclcpp::spin_some(node_);
  }

  // ------------------------------------------------------------------
  // Callback for CPU RaySensor
  // ------------------------------------------------------------------
  void OnScan()
  {
    if (!ray_sensor_)
      return;

    const int h_samples = ray_sensor_->RangeCount();
    const int v_samples = ray_sensor_->VerticalRangeCount();
    const double h_min  = ray_sensor_->AngleMin().Radian();
    const double h_max  = ray_sensor_->AngleMax().Radian();
    const double v_min  = ray_sensor_->VerticalAngleMin().Radian();
    const double v_max  = ray_sensor_->VerticalAngleMax().Radian();
    const double r_min  = ray_sensor_->RangeMin();
    const double r_max  = ray_sensor_->RangeMax();

    const int v_count = (v_samples > 0) ? v_samples : 1;
    const int h_count = (h_samples > 0) ? h_samples : 1;

    // Pre-count valid points so we allocate once
    int valid = 0;
    for (int i = 0; i < v_count * h_count; ++i)
    {
      double r = ray_sensor_->Range(i);
      if (r >= r_min && r <= r_max && std::isfinite(r))
        ++valid;
    }

    PublishCloud(h_count, v_count, h_min, h_max, v_min, v_max, r_min, r_max,
                 valid, [this](int idx) { return ray_sensor_->Range(idx); });
  }

  // ------------------------------------------------------------------
  // Callback for GpuRaySensor
  // ------------------------------------------------------------------
  void OnScanGpu()
  {
    if (!gpu_ray_sensor_)
      return;

    const int h_samples = gpu_ray_sensor_->RangeCount();
    const int v_samples = gpu_ray_sensor_->VerticalRangeCount();
    const double h_min  = gpu_ray_sensor_->AngleMin().Radian();
    const double h_max  = gpu_ray_sensor_->AngleMax().Radian();
    const double v_min  = gpu_ray_sensor_->VerticalAngleMin().Radian();
    const double v_max  = gpu_ray_sensor_->VerticalAngleMax().Radian();
    const double r_min  = gpu_ray_sensor_->RangeMin();
    const double r_max  = gpu_ray_sensor_->RangeMax();

    const int v_count = (v_samples > 0) ? v_samples : 1;
    const int h_count = (h_samples > 0) ? h_samples : 1;

    int valid = 0;
    for (int i = 0; i < v_count * h_count; ++i)
    {
      double r = gpu_ray_sensor_->Range(i);
      if (r >= r_min && r <= r_max && std::isfinite(r))
        ++valid;
    }

    PublishCloud(h_count, v_count, h_min, h_max, v_min, v_max, r_min, r_max,
                 valid, [this](int idx) { return gpu_ray_sensor_->Range(idx); });
  }

  // ------------------------------------------------------------------
  // Build and publish PointCloud2 from spherical ray data
  // ------------------------------------------------------------------
  template <typename RangeFunc>
  void PublishCloud(int h_count, int v_count,
                    double h_min, double h_max,
                    double v_min, double v_max,
                    double r_min, double r_max,
                    int valid_count, RangeFunc get_range)
  {
    auto msg = std::make_unique<sensor_msgs::msg::PointCloud2>();
    msg->header.stamp = node_->now();
    msg->header.frame_id = frame_name_;
    msg->height = 1;
    msg->width = valid_count;
    msg->is_dense = true;
    msg->is_bigendian = false;

    // Fields: x, y, z, intensity, ring
    sensor_msgs::PointCloud2Modifier modifier(*msg);
    modifier.setPointCloud2Fields(5,
      "x",         1, sensor_msgs::msg::PointField::FLOAT32,
      "y",         1, sensor_msgs::msg::PointField::FLOAT32,
      "z",         1, sensor_msgs::msg::PointField::FLOAT32,
      "intensity", 1, sensor_msgs::msg::PointField::FLOAT32,
      "ring",      1, sensor_msgs::msg::PointField::UINT16);
    modifier.resize(valid_count);

    sensor_msgs::PointCloud2Iterator<float>    xi(*msg, "x");
    sensor_msgs::PointCloud2Iterator<float>    yi(*msg, "y");
    sensor_msgs::PointCloud2Iterator<float>    zi(*msg, "z");
    sensor_msgs::PointCloud2Iterator<float>    ii(*msg, "intensity");
    sensor_msgs::PointCloud2Iterator<uint16_t> ri(*msg, "ring");

    const double h_step = (h_count > 1) ? (h_max - h_min) / (h_count - 1) : 0.0;
    const double v_step = (v_count > 1) ? (v_max - v_min) / (v_count - 1) : 0.0;

    for (int v = 0; v < v_count; ++v)
    {
      double v_angle = v_min + v * v_step;
      double cos_v = std::cos(v_angle);
      double sin_v = std::sin(v_angle);

      for (int h = 0; h < h_count; ++h)
      {
        int idx = v * h_count + h;
        double r = get_range(idx);

        if (r < r_min || r > r_max || !std::isfinite(r))
          continue;

        double h_angle = h_min + h * h_step;

        *xi = static_cast<float>(r * cos_v * std::cos(h_angle));
        *yi = static_cast<float>(r * cos_v * std::sin(h_angle));
        *zi = static_cast<float>(r * sin_v);
        *ii = static_cast<float>(min_intensity_);  // Gazebo Classic doesn't give per-point intensity
        *ri = static_cast<uint16_t>(v);             // ring = vertical channel index

        ++xi; ++yi; ++zi; ++ii; ++ri;
      }
    }

    pub_->publish(std::move(msg));
  }

  // ---- Members ----
  gazebo::physics::ModelPtr model_;
  gazebo::sensors::RaySensorPtr ray_sensor_;
  gazebo::sensors::GpuRaySensorPtr gpu_ray_sensor_;

  gazebo::event::ConnectionPtr update_conn_;
  gazebo::event::ConnectionPtr sensor_conn_;

  rclcpp::Node::SharedPtr node_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_;

  std::string sensor_name_;
  std::string topic_name_;
  std::string frame_name_;
  double min_intensity_{0.0};
};

GZ_REGISTER_MODEL_PLUGIN(OS1GazeboPlugin)

}  // namespace os1_gazebo
