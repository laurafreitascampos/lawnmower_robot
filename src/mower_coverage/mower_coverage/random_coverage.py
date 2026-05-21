"""
Random Coverage Node - Lógica de cobertura aleatória pro robô cortador de grama.

Estratégia (estilo Roomba antigo):
  1. Anda pra frente em velocidade constante
  2. Lê o tópico /scan (LiDAR LD19) continuamente
  3. Se detectar obstáculo dentro de uma "zona de segurança" frontal:
     a. Para o robô
     b. Gira em direção oposta ao obstáculo
     c. Volta a andar pra frente
  4. Repete indefinidamente

Após algum tempo, o robô cobre estatisticamente toda a área navegável.
É o algoritmo de cobertura mais simples possível, mas funcional.

Tópicos:
  Inscreve em:  /scan       (sensor_msgs/LaserScan)
  Publica em:   /cmd_vel    (geometry_msgs/Twist)
"""

import math
import random
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class RandomCoverageNode(Node):

    def __init__(self):
        super().__init__('random_coverage')

        # ====== Parâmetros configuráveis ======
        self.declare_parameter('linear_speed', 0.3)       # m/s ao andar pra frente
        self.declare_parameter('angular_speed', 1.0)      # rad/s ao girar
        self.declare_parameter('safety_distance', 0.6)    # metros, distância de "alarme"
        self.declare_parameter('front_angle_deg', 60.0)   # ângulo do "cone frontal" a observar

        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.safety_distance = self.get_parameter('safety_distance').value
        self.front_angle_rad = math.radians(self.get_parameter('front_angle_deg').value)

        # ====== Estado da máquina ======
        # FORWARD: andando reto
        # TURNING: girando até abrir caminho
        self.state = 'FORWARD'
        self.turn_direction = 1.0    # 1.0 = esquerda, -1.0 = direita
        self.turn_end_time = None

        # ====== Publisher pro tópico de comando ======
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # ====== Subscriber pro LiDAR ======
        # QoS BEST_EFFORT é importante pra LiDAR no Gazebo
        # (o plugin publica em best_effort por padrão)
        lidar_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, lidar_qos
        )

        # ====== Timer pra publicar comandos a 10Hz ======
        self.timer = self.create_timer(0.1, self.control_loop)

        # Última leitura do LiDAR (None até receber a primeira)
        self.latest_scan = None

        self.get_logger().info('=== Random Coverage iniciado ===')
        self.get_logger().info(f'Vel linear: {self.linear_speed} m/s')
        self.get_logger().info(f'Vel angular: {self.angular_speed} rad/s')
        self.get_logger().info(f'Distância de segurança: {self.safety_distance} m')

    def scan_callback(self, msg: LaserScan):
        """Armazena a última leitura do LiDAR."""
        self.latest_scan = msg

    def get_min_distance_in_front(self):
        """
        Olha o LiDAR e retorna a menor distância dentro do cone frontal.

        O LiDAR do nosso robô (LD19) faz scan 360 graus, começando atrás (-pi)
        e indo até atrás de novo (+pi). O ponto 0 rad é "frente do robô".

        Retorna (distancia_mínima, lado_mais_próximo)
          lado_mais_próximo: 'left' ou 'right' (pra decidir pra onde girar)
        """
        if self.latest_scan is None:
            return float('inf'), 'left'

        ranges = self.latest_scan.ranges
        angle_min = self.latest_scan.angle_min
        angle_increment = self.latest_scan.angle_increment

        min_dist = float('inf')
        min_dist_angle = 0.0

        # Itera por todos os feixes do scan
        for i, r in enumerate(ranges):
            # Calcula o ângulo deste feixe
            angle = angle_min + i * angle_increment

            # Só considera feixes dentro do cone frontal
            if abs(angle) > self.front_angle_rad / 2.0:
                continue

            # Ignora leituras inválidas (inf, NaN, ou fora do range do sensor)
            if not math.isfinite(r):
                continue
            if r < self.latest_scan.range_min or r > self.latest_scan.range_max:
                continue

            if r < min_dist:
                min_dist = r
                min_dist_angle = angle

        # Determina lado: ângulo positivo é esquerda, negativo é direita
        # (convenção ROS: x pra frente, y pra esquerda)
        side = 'left' if min_dist_angle > 0 else 'right'

        return min_dist, side

    def control_loop(self):
        """Chamado 10x por segundo - decide o que o robô deve fazer."""
        if self.latest_scan is None:
            # Ainda não chegou nenhum scan, espera
            return

        cmd = Twist()

        # ====== Lógica da máquina de estados ======
        if self.state == 'FORWARD':
            min_dist, closest_side = self.get_min_distance_in_front()

            if min_dist < self.safety_distance:
                # Obstáculo detectado, transiciona pra TURNING
                self.get_logger().info(
                    f'Obstáculo a {min_dist:.2f}m no lado {closest_side}, girando...'
                )

                # Gira na direção OPOSTA ao obstáculo
                # (se obstáculo está na esquerda, gira pra direita, e vice-versa)
                self.turn_direction = -1.0 if closest_side == 'left' else 1.0

                # Duração aleatória do giro entre 0.8 e 2.0 segundos
                # Isso faz com que o robô explore aleatoriamente
                turn_duration = random.uniform(0.8, 2.0)
                self.turn_end_time = self.get_clock().now().nanoseconds * 1e-9 + turn_duration

                self.state = 'TURNING'
                # Não anda nesse ciclo (já vai começar a girar no próximo)
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
            else:
                # Caminho livre, anda pra frente
                cmd.linear.x = self.linear_speed
                cmd.angular.z = 0.0

        elif self.state == 'TURNING':
            now = self.get_clock().now().nanoseconds * 1e-9

            if now >= self.turn_end_time:
                # Tempo de giro acabou, verifica se desbloqueou
                min_dist, _ = self.get_min_distance_in_front()

                if min_dist >= self.safety_distance:
                    # Caminho livre, volta a andar
                    self.get_logger().info(f'Caminho livre ({min_dist:.2f}m), seguindo...')
                    self.state = 'FORWARD'
                    cmd.linear.x = self.linear_speed
                    cmd.angular.z = 0.0
                else:
                    # Ainda bloqueado, gira mais um pouco
                    self.turn_end_time = now + random.uniform(0.5, 1.5)
                    cmd.linear.x = 0.0
                    cmd.angular.z = self.turn_direction * self.angular_speed
            else:
                # Ainda girando
                cmd.linear.x = 0.0
                cmd.angular.z = self.turn_direction * self.angular_speed

        # Publica o comando
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = RandomCoverageNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Antes de fechar, manda velocidade zero pro robô parar
        cmd = Twist()
        node.cmd_pub.publish(cmd)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
