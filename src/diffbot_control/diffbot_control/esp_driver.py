import serial
import time


class ESPDriver:

    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)

    def set_speeds(self, speed_left, speed_right):
        """
        Convertit une vitesse (m/s) en commande ESC
        Exemple simple : -100 à 100
        """
        esp_left_value = int(speed_left * 50)
        esp_left_value = max(-100, min(100, esp_left_value))

        esp_right_value = int(speed_right * 50)
        esp_right_value = max(-100, min(100, esp_right_value))

        cmd = f"L{esp_left_value}:R{esp_right_value}\n"
        self.ser.write(cmd.encode())
