#!/bin/bash
# Setup do ambiente de desenvolvimento para o projeto lawnmower_robot
# Testado em Ubuntu 24.04 LTS

set -e  # para na primeira falha

echo "=== Lawnmower Robot - Setup do ambiente de desenvolvimento ==="
echo ""

# Verifica se está no Ubuntu 24.04
if ! grep -q "24.04" /etc/os-release; then
    echo "AVISO: este script foi testado no Ubuntu 24.04. Você está em:"
    cat /etc/os-release | grep PRETTY_NAME
    read -p "Continuar mesmo assim? (s/N) " resp
    [[ "$resp" != "s" ]] && exit 1
fi

# 1. ROS2 Jazzy
if ! command -v ros2 &> /dev/null; then
    echo ">>> Instalando ROS2 Jazzy..."
    sudo apt update && sudo apt install -y software-properties-common curl
    sudo add-apt-repository universe -y
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
        http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
        | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    sudo apt update
    sudo apt install -y ros-jazzy-desktop ros-dev-tools
else
    echo ">>> ROS2 já instalado, pulando."
fi

# 2. Gazebo Harmonic (vem junto com ros-jazzy-desktop mas garantimos)
echo ">>> Instalando integração ROS2 <-> Gazebo..."
sudo apt install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-xacro \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-rviz2 \
    ros-jazzy-teleop-twist-keyboard

# 3. SLAM e Navegação (vamos usar depois)
echo ">>> Instalando SLAM Toolbox e Nav2..."
sudo apt install -y \
    ros-jazzy-slam-toolbox \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup

# 4. Adiciona source no .bashrc se ainda não estiver
if ! grep -q "source /opt/ros/jazzy/setup.bash" ~/.bashrc; then
    echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
fi

echo ""
echo "=== Setup concluído! ==="
echo "Abra um novo terminal (ou rode 'source ~/.bashrc') e execute:"
echo "  ros2 --help"
echo "Pra confirmar que funcionou."
