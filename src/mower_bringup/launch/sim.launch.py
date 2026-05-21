"""
Launch de simulação completa do robô cortador de grama.

O que esse launch faz, em ordem:
  1. Processa o URDF (xacro) e disponibiliza no tópico /robot_description
  2. Inicia o Gazebo Harmonic com o mundo backyard_simple.sdf
  3. Spawna o robô no mundo Gazebo (lê o /robot_description)
  4. Inicia o robot_state_publisher (publica TF baseado no URDF)
  5. Inicia a ponte ROS2 <-> Gazebo (parameter_bridge) pros tópicos:
       /clock        Gazebo -> ROS2
       /cmd_vel      ROS2   -> Gazebo (velocidades do robô)
       /odom         Gazebo -> ROS2   (odometria)
       /scan         Gazebo -> ROS2   (LiDAR)
       /tf, /tf_static, /joint_states  Gazebo -> ROS2
  6. Abre RViz2 com a config pré-feita

Uso:
    ros2 launch mower_simulation sim.launch.py

Pra dirigir o robô (em outro terminal):
    ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # ====== Caminhos dos arquivos ======
    pkg_description = FindPackageShare("mower_description")
    pkg_simulation = FindPackageShare("mower_simulation")
    pkg_ros_gz_sim = FindPackageShare("ros_gz_sim")

    urdf_file = PathJoinSubstitution([pkg_description, "urdf", "mower.urdf.xacro"])
    world_file = PathJoinSubstitution([pkg_simulation, "worlds", "backyard_simple.sdf"])
    rviz_config = PathJoinSubstitution([pkg_simulation, "config", "mower.rviz"])

    # ====== Argumentos do launch (configuráveis na linha de comando) ======
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    use_rviz = LaunchConfiguration("use_rviz", default="true")

    # ====== Processa o URDF (xacro -> XML) ======
    # O 'Command' chama o executável xacro e captura sua saída como string,
    # que vai ser o conteúdo do parâmetro robot_description.
    robot_description_content = Command(["xacro ", urdf_file])
    robot_description = {"robot_description": ParameterValue(robot_description_content, value_type=str)}

    # ====== Robot State Publisher ======
    # Publica as transformações TF baseadas no URDF.
    # Toda vez que uma junta se mexe, ele recalcula e publica.
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
        output="screen",
    )

    # ====== Inicia o Gazebo Harmonic ======
    # Usa o launch padrão do ros_gz_sim, passando o arquivo de mundo.
    # A flag '-r' faz a simulação começar rodando (sem precisar clicar play).
    # A flag '--render-engine ogre' usa OGRE1 (que funciona no Distrobox).
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([pkg_ros_gz_sim, "/launch/gz_sim.launch.py"]),
        launch_arguments={
            "gz_args": ["-r -v 4 --render-engine ogre ", world_file],
            "on_exit_shutdown": "true",
        }.items(),
    )

    # ====== Spawna o robô no Gazebo ======
    # Lê o /robot_description (publicado pelo robot_state_publisher) e cria
    # uma instância do robô no mundo, na posição (0, 0, 0.2).
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "mower",
            "-x", "0", "-y", "0", "-z", "0.2",
        ],
        output="screen",
    )

    # ====== Ponte ROS2 <-> Gazebo ======
    # O parameter_bridge converte mensagens entre os dois sistemas.
    # Formato: <topic>@<ros_type>[<direção>]<gz_type>
    #   ] = ROS2 <- Gazebo  (assinante no ROS)
    #   [ = ROS2 -> Gazebo  (publicador no ROS)
    #   @ = bidirecional
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            # Clock: Gazebo publica o tempo simulado pro ROS2
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",

            # Comando de velocidade: ROS2 manda pro Gazebo
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",

            # Odometria: Gazebo manda pro ROS2 (calculada pelo plugin diff_drive)
            "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",

            # LiDAR: Gazebo manda pro ROS2
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",

            # TF: transformações
            "/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",

            # Joint states (estados das juntas das rodas)
            "/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model",
        ],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    # ====== RViz2 ======
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        condition=None,  # vamos controlar pela LaunchConfiguration
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    # ====== Monta o launch description ======
    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time", default_value="true",
            description="Usar tempo simulado (do Gazebo) em vez de tempo real"
        ),
        DeclareLaunchArgument(
            "use_rviz", default_value="true",
            description="Abrir RViz2 automaticamente"
        ),
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge,
        rviz,
    ])
