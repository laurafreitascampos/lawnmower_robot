"""
Launch que sobe TUDO + node autônomo de cobertura.

Inclui:
  - O launch de simulação completo (Gazebo + RViz + ponte)
  - O node random_coverage que controla o robô autonomamente

Uso:
    ros2 launch mower_coverage coverage.launch.py

Espera uns 15 segundos pra Gazebo carregar, e o robô começa a se mover
sozinho, andando pra frente e desviando de obstáculos detectados pelo LiDAR.
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Inclui o launch de simulação completo
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("mower_bringup"),
                "launch",
                "sim.launch.py",
            ])
        ])
    )

    # Node de cobertura - inicia com 10 segundos de delay
    # pra dar tempo do Gazebo carregar e o robô spawnar
    coverage_node = TimerAction(
        period=10.0,
        actions=[
            Node(
                package="mower_coverage",
                executable="random_coverage",
                name="random_coverage",
                output="screen",
                parameters=[{
                    "linear_speed": 0.4,
                    "angular_speed": 1.2,
                    "safety_distance": 0.05,
                    "front_angle_deg": 30.0,
		    "clear_distance": 0.3,
		    "max_turn_time": 3.0,
                }],
            )
        ]
    )

    return LaunchDescription([
        sim_launch,
        coverage_node,
    ])
