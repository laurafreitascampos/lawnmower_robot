# Lawnmower Robot

Robô cortador de grama autônomo baseado em ROS2 + LiDAR LD19, controlado por Raspberry Pi 5.

## Stack

- **ROS2 Jazzy** (Ubuntu 24.04)
- **Gazebo Harmonic** (simulação)
- **Nav2** (navegação autônoma)
- **SLAM Toolbox** (mapeamento)
- **LiDAR LDRobot LD19** (sensor principal)

## Hardware

Ver esquemático em [`docs/esquema_eletrico.pdf`](docs/esquema_eletrico.pdf).

### Componentes principais

| Componente            | Função                                  | Tensão     |
|-----------------------|-----------------------------------------|------------|
| 2x Bateria Lipo 2S    | Alimentação (em paralelo, 7.4V / 13Ah) | 7.4V       |
| Raspberry Pi 5        | Computador principal (ROS2, Nav2, SLAM) | 5V         |
| ESP8266 (ou ESP32)    | Controle de baixo nível (PWM, encoders) | 3.3V       |
| LiDAR LD19            | Sensoriamento 360°                      | 5V         |
| Ponte H1              | Driver dos motores das rodas            | 7.4V       |
| Ponte H2              | Driver do motor da lâmina               | 7.4V       |
| 2x XL4015             | Step-down (5V pro Pi e LiDAR)           | -          |
| 1x AMS1117            | Step-down (3.3V pro ESP)                | -          |

### Pendências de hardware (a resolver)

- [ ] Confirmar: 2 motores tração (2WD) ou 4 motores skid-steer?
- [ ] Adicionar encoders aos motores das rodas (essencial pra odometria)
- [ ] Avaliar troca ESP8266 → ESP32 (mais RAM, suporta micro-ROS)
- [ ] Confirmar tensão de saída dos XL4015 (5V pro Pi, 5V pro LiDAR)

## Estrutura do repositório

```
lawnmower_robot/
├── docs/                       # Documentação, datasheets, esquemáticos
├── scripts/                    # Scripts de setup do ambiente
└── src/                        # Pacotes ROS2
    ├── mower_description/      # URDF do robô (modelo 3D + sensores)
    ├── mower_bringup/          # Launch files de alto nível
    └── mower_simulation/       # Mundos Gazebo, configs de simulação
```

## Setup rápido (PC de desenvolvimento)

```bash
# 1. Clone o repositório dentro do workspace ROS2
mkdir -p ~/mower_ws/src
cd ~/mower_ws/src
git clone <URL_DO_SEU_REPO> lawnmower_robot

# 2. Rode o setup (instala ROS2 + Gazebo + deps)
cd lawnmower_robot
./scripts/setup_dev.sh

# 3. Build o workspace (em terminal NOVO, após setup)
cd ~/mower_ws
colcon build --symlink-install
source install/setup.bash

# 4. Visualize o URDF no RViz
ros2 launch mower_description display.launch.py

# 5. (Etapa 2) Suba a simulação completa
ros2 launch mower_bringup sim.launch.py
```

## Status do projeto

- [x] Estrutura inicial do repositório
- [x] URDF do robô (4 rodas skid-steer + LiDAR)
- [x] Esquemático elétrico documentado
- [ ] Mundo Gazebo
- [ ] Launch de simulação
- [ ] Teleop por teclado
- [ ] SLAM
- [ ] Navegação autônoma
- [ ] Lógica de cobertura
- [ ] Driver real do LD19 (no Pi)
- [ ] Driver de motores via ESP (micro-ROS)
- [ ] Migração pro hardware real

## Arquitetura de software

```
                  ┌─────────────────────────────┐
                  │   Camada de aplicação        │
                  │  (mesma em sim e real)       │
                  │  • SLAM Toolbox              │
                  │  • Nav2                      │
                  │  • Lógica de cobertura       │
                  └────────────┬─────────────────┘
                               │ tópicos padrão:
                               │ /scan /cmd_vel /odom /tf
                  ┌────────────┴─────────────────┐
                  │                              │
        ┌─────────▼──────────┐      ┌────────────▼─────────┐
        │  SIMULAÇÃO         │      │  HARDWARE REAL        │
        │  (no PC)           │      │  (no Pi 5)            │
        │  • Gazebo plugin   │      │  • ldlidar_stl_ros2   │
        │    LiDAR + skid    │      │  • micro-ROS no ESP   │
        │                    │      │    (motores+encoders) │
        └────────────────────┘      └───────────────────────┘
```
