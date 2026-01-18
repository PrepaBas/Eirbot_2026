import serial
import time


class ESCDriver:

    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)

    def set_speed(self, speed_mps):
        """
        Convertit une vitesse (m/s) en commande ESC
        Exemple simple : -100 à 100
        """
        esc_value = int(speed_mps * 50)
        esc_value = max(-100, min(100, esc_value))

        cmd = f"M {esc_value}\n"
        self.ser.write(cmd.encode())
