cmake_minimum_required(VERSION 3.8)
project(os1_gazebo_plugin)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(gazebo_dev REQUIRED)

# ----- Shared library (Gazebo plugin) -----
add_library(os1_gazebo_plugin SHARED
  src/os1_gazebo_plugin.cpp
)

target_include_directories(os1_gazebo_plugin PUBLIC
  ${gazebo_dev_INCLUDE_DIRS}
)

ament_target_dependencies(os1_gazebo_plugin
  rclcpp
  sensor_msgs
  gazebo_dev
)

# Gazebo plugins must NOT have the "lib" prefix stripped — Gazebo looks for
# "libos1_gazebo_plugin.so" on disk.
# CMake already prepends "lib" on Linux, so we just need to make sure
# set_target_properties doesn't remove it.

install(TARGETS os1_gazebo_plugin
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
)

ament_environment_hooks(
  "${ament_cmake_package_templates_ENVIRONMENT_HOOK_LIBRARY_PATH}"
)

ament_package()
