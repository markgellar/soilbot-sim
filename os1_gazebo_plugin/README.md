# OS1 Gazebo Plugin — Option C

A Gazebo Classic **model plugin** that publishes `sensor_msgs/PointCloud2` from an OS1-64 ray sensor **without using `<remapping>` tags**, so it doesn't break `gazebo_ros2_control`.

## The Problem This Solves

The standard `libgazebo_ros_ray_sensor.so` requires:
```xml
<remapping>~/out:=/ouster/points</remapping>
```
The `:=` in that tag confuses `gazebo_ros2_control`'s internal YAML parser,
preventing the controller manager from starting. This plugin replaces the
standard sensor plugin with a model plugin that uses `<topic_name>` instead.

## Build

```bash
# From your workspace root (e.g. ~/catkin_ws or ~/ros2_ws)
cd src/
# Copy or symlink the os1_gazebo_plugin folder here

cd ..
colcon build --packages-select os1_gazebo_plugin
source install/setup.bash
```

## Integrate with Husky

### Step 1 — Include the xacro in your Husky description

In your Husky's main URDF xacro (or your custom overlay), add:

```xml
<xacro:include filename="$(find os1_gazebo_plugin)/urdf/os1_64.urdf.xacro"/>

<xacro:os1_64_lidar
  name="os1"
  parent_link="top_plate_link"
  xyz="0 0 0.04"
  rpy="0 0 0"
  topic="/ouster/points"
  hz="10"
  h_samples="1024"
  gpu="false"
/>
```

Parameters:
- `name` — prefix for link/joint/sensor names (default: `os1`)
- `parent_link` — which Husky link to mount on (default: `top_plate_link`)
- `xyz` / `rpy` — mount offset
- `topic` — ROS 2 topic for PointCloud2 (default: `/ouster/points`)
- `hz` — scan rate, 10 or 20 (default: `10`)
- `h_samples` — horizontal resolution: 512, 1024, or 2048 (default: `1024`)
- `gpu` — set to `true` to use `gpu_ray` instead of `ray` (default: `false`)

### Step 2 — Install the xacro so `$(find ...)` works

Make sure the `urdf/` folder is installed. Add to `CMakeLists.txt`:

```cmake
install(DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
)
```

### Step 3 — Set `GAZEBO_PLUGIN_PATH`

After `colcon build`, the `.so` lands in `install/os1_gazebo_plugin/lib/`.
Gazebo needs to find it:

```bash
export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:$(ros2 pkg prefix os1_gazebo_plugin)/lib
```

Or add it to your launch file before spawning Gazebo.

### Step 4 — Launch and verify

```bash
# Launch your Husky + Gazebo as usual
ros2 launch your_husky_pkg gazebo.launch.py

# In another terminal:
ros2 topic list | grep ouster
# Should show: /ouster/points

ros2 topic hz /ouster/points
# Should show ~10 Hz

# Visualize in RViz2:
rviz2
# Add → By topic → /ouster/points → PointCloud2
# Set Fixed Frame to "ouster_link" or "os1_lidar_link"
```

## Performance Notes

- **CPU ray** (`gpu="false"`): Safe on WSL2 but slow at 1024×64. Try
  `h_samples="512"` if the sim lags. This gives you 512×64 = 32,768 rays
  at 10 Hz, which is usually fine for Nav2.
- **GPU ray** (`gpu="true"`): Faster but requires working OpenGL on WSL2.
  If Gazebo renders visuals fine, GPU ray should work too.
- The plugin publishes **x, y, z, intensity, ring** fields. Intensity is
  a constant (Gazebo Classic doesn't simulate surface reflectance). Ring
  is the vertical channel index (0–63), matching the real OS1-64 format.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "No sensor found" in console | Check that `sensor_name` in the `<plugin>` block matches the sensor's `name` attribute exactly |
| Controllers don't start | Make sure there are NO `<remapping>` tags anywhere in the URDF. Search: `grep -r "remapping" your_urdf/` |
| PointCloud2 is empty | Sensor is inside a collision mesh. Raise `xyz` in the mount offset |
| PointCloud2 is flat (2D) | The `<vertical>` block is missing from the sensor definition |
| Topic exists but 0 Hz | `GAZEBO_PLUGIN_PATH` doesn't include the plugin's lib directory |
| Gazebo crashes on load | On WSL2 with `gpu="true"` — switch to `gpu="false"` |
