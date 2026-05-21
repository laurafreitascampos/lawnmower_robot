"""
Random Coverage Node - V2 (corrigida)

Estratégia:
  1. FORWARD: anda pra frente, observando cone frontal estreito (40°)
  2. Detecta obstáculo perto -> entra em TURNING
  3. TURNING: gira UMA direção fixa enquanto vê obstáculo
  4. Continua FORWARD assim que liberar
  5. Tem timeout de segurança: se girar demais (>5s), tenta outra direção

Diferença pra V1:
  - Cone de detecção mais estreito (40°) - só obstáculos mais "na cara"
  - Durante TURNING, monitora LiDAR em tempo real, não por tempo
  - Para de girar assim que abre caminho, não espera tempo aleatório
  - Anti-loop: se girar mais de 5 segundos, inverte direção
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
        self.declare_parameter('linear_speed', 0.3)
        self.declare_parameter('angular_speed', 0.8)
        self.declare_parameter('safety_distance', 0.5)     # 0.5m de distância
        self.declare_parameter('front_angle_deg', 40.0)    # cone mais ESTREITO (40°)
        self.declare_parameter('clear_distance', 0.8)      # distância pra considerar "livre"
        self.declare_parameter('max_turn_time', 5.0)       # se girar mais que isso, inverte

        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.safety_distance = self.get_parameter('safety_distance').value
        self.front_angle_rad = math.radians(self.get_parameter('front_angle_deg').value)
        self.clear_distance = self.get_parameter('clear_distance').value
        self.max_turn_time = self.get_parameter('max_turn_time').value

        # ====== Estado da máquina ======
        self.state = 'FORWARD'
        self.turn_direction = 1.0
        self.turn_start_time = None

        # ====== Pub/Sub ======
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        lidar_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, lidar_qos
        )

        self.timer = self.create_timer(0.1, self.control_loop)
        self.latest_scan = None

        self.get_logger().info('=== Random Coverage V2 iniciado ===')
        self.get_logger().info(f'Vel linear: {self.linear_speed} m/s')
        self.get_logger().info(f'Distância de segurança: {self.safety_distance} m')
        self.get_logger().info(f'Distância de livre: {self.clear_distance} m')
        self.get_logger().info(f'Cone frontal: {self.get_parameter("front_angle_deg").value}°')

    def scan_callback(self, msg: LaserScan):
        self.latest_scan = msg

    def get_min_distance_in_front(self):
            """Retorna (distancia_minima, lado_mais_proximo) dentro do cone frontal."""
            if self.latest_scan is None:
                return float('inf'), 'left'

            ranges = self.latest_scan.ranges
            angle_min = self.latest_scan.angle_min
            angle_increment = self.latest_scan.angle_increment

            # IMPORTANTE: ignora leituras dentro do próprio chassi do robô
            # Chassi tem 40cm de comprimento, então qualquer leitura < 25cm
            # provavelmente é o próprio robô (o LiDAR está no centro do chassi)
            MIN_VALID_RANGE = 0.25

            min_dist = float('inf')
            min_dist_angle = 0.0

            for i, r in enumerate(ranges):
                angle = angle_min + i * angle_increment

                # Só considera feixes no cone frontal
                if abs(angle) > self.front_angle_rad / 2.0:
                    continue

                # Filtra valores inválidos
                if not math.isfinite(r):
                    continue
                if r < self.latest_scan.range_min or r > self.latest_scan.range_max:
                    continue

                # NOVO: ignora leituras dentro do raio do próprio robô
                if r < MIN_VALID_RANGE:
                    continue

                if r < min_dist:
                    min_dist = r
                    min_dist_angle = angle

            side = 'left' if min_dist_angle > 0 else 'right'
            return min_dist, side

    def control_loop(self):
        if self.latest_scan is None:
            return

        cmd = Twist()
        min_dist, closest_side = self.get_min_distance_in_front()
        now = self.get_clock().now().nanoseconds * 1e-9

        if self.state == 'FORWARD':
            if min_dist < self.safety_distance:
                # Detectou obstáculo, começa a girar
                self.turn_direction = -1.0 if closest_side == 'left' else 1.0
                self.turn_start_time = now
                self.state = 'TURNING'
                self.get_logger().info(
                    f'Obstáculo a {min_dist:.2f}m ({closest_side}), '
                    f'girando pra {"direita" if self.turn_direction < 0 else "esquerda"}...'
                )
                # Não anda nesse ciclo
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
            else:
                # Tudo livre, segue em frente
                cmd.linear.x = self.linear_speed
                cmd.angular.z = 0.0

        elif self.state == 'TURNING':
            # Verifica caminho em TEMPO REAL (não espera tempo passar)
            if min_dist >= self.clear_distance:
                # Caminho livre! Volta a andar
                self.state = 'FORWARD'
                self.get_logger().info(f'Caminho livre ({min_dist:.2f}m), seguindo...')
                cmd.linear.x = self.linear_speed
                cmd.angular.z = 0.0
            else:
                # Ainda bloqueado, continua girando
                elapsed = now - self.turn_start_time

                # Anti-loop: se girou tempo demais, inverte direção
                if elapsed > self.max_turn_time:
                    self.turn_direction *= -1.0
                    self.turn_start_time = now
                    self.get_logger().warn(
                        f'Girou {self.max_turn_time}s sem desobstruir, invertendo direção'
                    )

                cmd.linear.x = 0.0
                cmd.angular.z = self.turn_direction * self.angular_speed

        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = RandomCoverageNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cmd = Twist()
        node.cmd_pub.publish(cmd)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
