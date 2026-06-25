# SoilBot Sim

ROS 2 Humble + Gazebo Classic simulation workspace for a Clearpath Husky A200 equipped with a simulated Ouster OS1-64 3D LiDAR and soil sampling instrumentation.

## What This Is

An autonomous soil sampling robot simulation. The Husky drives to GPS waypoints, collects soil measurements (pH, moisture, temperature, electrical conductivity), and generates lime recommendations. The simulated OS1-64 provides a 3D point cloud for obstacle avoidance and navigation via Nav2.

## The OS1-64 Plugin

The `os1_gazebo_plugin` package is a custom Gazebo Classic **model plugin** that simulates the Ouster OS1-64 without using the standard `libgazebo_ros_ray_sensor.so`. This matters because the standard plugin requires a `<remapping>` tag whose `:=` syntax breaks `gazebo_ros2_control`'s internal YAML parser, preventing the controller manager from starting. Our plugin publishes `PointCloud2` via a standalone `rclcpp::Node` with a plain `<topic_name>` parameter — no remapping involved.

**No official Ouster ROS 2 Gazebo plugin exists.** Ouster confirmed this in December 2024. The only alternative ([Gepetto's ouster-gazebo-simulation](https://github.com/Gepetto/ouster-gazebo-simulation)) is ROS 1 only.

### Sensor Specs (as simulated)

| Parameter | Value |
|-----------|-------|
| Vertical channels | 64 |
| Horizontal FoV | 360° |
| Vertical FoV | ±22.5° (45° total) |
| Range | 0.8m – 120m |
| Horizontal samples | 512 (configurable) |
| Update rate | 6 Hz (WSL2), 10 Hz (native Linux) |
| Noise | Gaussian, σ = 8mm |
| Output topic | `/ouster/points` (`sensor_msgs/PointCloud2`) |
| Fields | x, y, z, intensity, ring |

## Packages

| Package | Description |
|---------|-------------|
| `husky` | Modified Clearpath Husky A200 description, control, and Gazebo launch (includes custom meshes for rail mounts, linear stage, and LiDAR housing) |
| `os1_gazebo_plugin` | Custom Gazebo model plugin for OS1-64 simulation |
| `my_robot` | Launch files, Nav2 config, and ROS 2 nodes for soil sampling, GPS sensing, and navigation |
| `soil_msgs` | Custom message type `SoilMeasurement` (pH, moisture, temperature, EC, GPS, lime recommendation) |

## Prerequisites

- Ubuntu 22.04 (native or WSL2)
- ROS 2 Humble
- Gazebo Classic 11 (`ros-humble-gazebo-ros-pkgs`)
- Nav2 (`ros-humble-navigation2`, `ros-humble-nav2-bringup`)
- Teleop (`ros-humble-teleop-twist-keyboard`)

```bash
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-navigation2 \
  ros-humble-nav2-bringup ros-humble-teleop-twist-keyboard
```

## Setup

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/markgellar/soilbot-sim.git .
cd ~/ros2_ws
colcon build
source install/setup.bash
echo 'export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:~/ros2_ws/install/os1_gazebo_plugin/lib' >> ~/.bashrc
source ~/.bashrc
```

## Launch

### Start the simulation

```bash
cd ~/ros2_ws
source install/setup.bash
export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:$(ros2 pkg prefix os1_gazebo_plugin)/lib
ros2 launch husky_gazebo gazebo.launch.py
```

### Verify the point cloud

```bash
ros2 topic hz /ouster/points    # Should show ~6 Hz on WSL2
```

### Visualize in RViz2

```bash
rviz2
```

1. Set **Fixed Frame** to `base_link`
2. **Add** → By topic → `/ouster/points` → PointCloud2
3. Expand PointCloud2 → Topic → set **Reliability** to **Best Effort**
4. Set **Size (m)** to `0.05`
5. **Add** → By display type → RobotModel → set **Description Source** to `Topic`

### Drive the robot

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Known Limitations

- **WSL2 performance**: GPU ray casting runs at ~6 Hz due to GPU passthrough overhead. Native Linux should reach 10 Hz.
- **No intensity simulation**: Gazebo Classic doesn't simulate surface reflectance. The intensity field is a constant.
- **No odom TF frame**: The diff drive controller publishes odometry messages on `/husky_velocity_controller/odom` but does not broadcast the `odom → base_link` transform by default. Set `enable_odom_tf: true` in `control.yaml` to enable it for Nav2.
- **Gazebo Classic is EOL**: As of January 2025. For long-term use, migrate to Gz Sim (Harmonic) with `gz_ros2_control`.

## Tested On

- Windows 11 + WSL2 (Ubuntu 22.04)
- ROS 2 Humble
- Gazebo Classic 11.10
- NVIDIA GPU with WSL2 GPU passthrough
