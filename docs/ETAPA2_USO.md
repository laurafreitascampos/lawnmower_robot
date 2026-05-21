# Etapa 2 - Simulação Gazebo + LiDAR + Teleop

Este documento explica como rodar a simulação completa do robô cortador de grama.

## Pré-requisitos

- ROS2 Jazzy instalado e configurado
- Gazebo Harmonic instalado (vem com `ros-jazzy-ros-gz`)
- Workspace ROS2 buildado (ver instruções abaixo)

## Build do workspace

```bash
# Entra no container (se usando Distrobox)
distrobox enter ubuntu-ros2

# Vai pro workspace e builda
cd ~/mower_ws
colcon build --symlink-install

# Source pro terminal atual reconhecer os pacotes
source install/setup.bash
```

## Como rodar

### Terminal 1: Sobe a simulação

```bash
ros2 launch mower_bringup sim.launch.py
```

Vai abrir 2 janelas:
- **Gazebo**: mostra o robô no "quintal" simulado (com cercas e obstáculos)
- **RViz2**: mostra o modelo 3D do robô + pontos do LiDAR em vermelho

Espera uns 10-15 segundos pra tudo carregar.

### Terminal 2: Controla o robô pelo teclado

Em outro terminal (dentro do mesmo container):

```bash
distrobox enter ubuntu-ros2
source ~/mower_ws/install/setup.bash

ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Comandos do teleop:
- `i` = pra frente
- `,` = pra trás
- `j` = girar pra esquerda
- `l` = girar pra direita
- `u` `o` = curva pra frente
- `m` `.` = curva pra trás
- `k` ou espaço = parar
- `q` `z` = aumentar/diminuir velocidade

## O que observar

1. **Gazebo**: o robô se move quando você dirige pelo teclado
2. **RViz2**:
   - Pontos vermelhos representam o LiDAR detectando os obstáculos
   - Quando o robô gira ou se move, os pontos vermelhos acompanham
   - As cercas e obstáculos do mundo Gazebo aparecem como pontos
   - O modelo 3D do robô (verde com rodas pretas) se move no RViz junto com o Gazebo

## Verificações úteis

### Listar tópicos ativos

```bash
ros2 topic list
```

Deve aparecer: `/scan`, `/cmd_vel`, `/odom`, `/tf`, `/joint_states`, `/clock`, etc.

### Ver dados do LiDAR em tempo real

```bash
ros2 topic echo /scan
```

Vai mostrar os arrays de distâncias detectadas (em metros). Aperta Ctrl+C pra parar.

### Ver odometria

```bash
ros2 topic echo /odom
```

Mostra posição e velocidade do robô.

### Ver TF tree (árvore de transformações)

```bash
ros2 run tf2_tools view_frames
```

Gera um PDF com o diagrama de frames (base_link, lidar_link, odom, etc).

## Troubleshooting

### Gazebo não abre / abre e fecha

Conferir variáveis de ambiente:

```bash
echo $GZ_IP        # deve ser 127.0.0.1
echo $QT_QPA_PLATFORM   # deve ser xcb
```

Se vazio, adicionar no `~/.bashrc`:

```bash
export GZ_IP=127.0.0.1
export GZ_PARTITION=mower_sim
export QT_QPA_PLATFORM=xcb
```

### RViz não mostra os pontos do LiDAR

Conferir se a ponte está rodando:

```bash
ros2 topic hz /scan
```

Deve mostrar ~10 Hz. Se mostrar 0 ou "no new messages", a ponte falhou.

### Robô não anda

Confere se está mandando comandos pro tópico certo:

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

Se isso não funcionar, o plugin diff_drive não está ativo no Gazebo.

## Próximos passos

- [ ] Etapa 3: SLAM Toolbox mapeando o ambiente
- [ ] Etapa 4: Nav2 navegando autonomamente
- [ ] Etapa 5: Lógica de cobertura zigue-zague
