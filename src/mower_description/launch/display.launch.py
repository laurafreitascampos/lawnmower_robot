"""
Launch file pra visualizar o URDF do robô no RViz2, SEM Gazebo.
Útil pra conferir se as juntas, rodas e LiDAR estão nas posições certas.

Uso:
    ros2 launch mower_description display.launch.py
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Caminho pro arquivo xacro
    urdf_path = PathJoinSubstitution([
        FindPackageShare("mower_description"),
        "urdf",
        "mower.urdf.xacro"
    ])

    # Argumento: usar joint_state_publisher_gui (com sliders) ou não
    gui_arg = DeclareLaunchArgument(
        "gui", default_value="true",
        description="Abrir joint_state_publisher_gui pra movimentar juntas manualmente"
    )

    # Processa o xacro -> URDF em tempo de execução
    robot_description = {
        "robot_description": Command(["xacro ", urdf_path])
    }

    # Node que publica o TF do robô a partir do URDF
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description],
        output="screen"
    )

    # Node que publica os estados das juntas (com GUI)
    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        condition=None,  # sempre abre nesse launch de display
    )

    # RViz
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen"
    )

    return LaunchDescription([
        gui_arg,
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz,
    ])
