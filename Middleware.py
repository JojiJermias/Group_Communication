import logging
import json
import socket

class Middleware:
    def __init__(self, peer_id, group_config_file):
        self.peer_id = peer_id
        self.group_config_file = group_config_file
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("localhost", self.get_port_from_peer_id(peer_id)))
        self.socket.settimeout(1)  # Timeout for receiving ACKs in Stop and Wait ARQ
        self.peer_list = self.load_group_config()

    def load_group_config(self):
        try:
            with open(self.group_config_file, 'r') as file:
                config = json.load(file)
                return config['group']
        except FileNotFoundError:
            logging.error(f'Group config file {self.group_config_file} not found.')
            print(f'Group config file {self.group_config_file} not found.')
            return []

    def start(self):
        logging.basicConfig(filename='middleware_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
        logging.info('Middleware started.')
        print('Middleware started.')
        if self.peer_id in [peer['peer_id'] for peer in self.peer_list]:
            if self.peer_id == 1:  # If the current peer is the sender
                self.sender_mode()
            else:
                self.receiver_mode()
        else:
            print(f"Peer ID {self.peer_id} not found in the group configuration.")

    def get_port_from_peer_id(self, peer_id):
        for peer in self.peer_list:
            if peer['peer_id'] == peer_id:
                return peer['port']

    def sender_mode(self):
        print("You are in sender mode.")
        while True:
            message = input("Enter message to send (or type 'exit' to quit): ")
            if message.lower() == 'exit':
                break
            self.send_message(message)

    def receiver_mode(self):
        print("You are in receiver mode. Waiting for messages...")
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                message, checksum = data.decode().split(',', 1)
                if self.verify_checksum(message, int(checksum)):
                    print(f'Message received: {message}')
                    self.send_ack(addr)
                else:
                    print("Checksum verification failed. Message may be corrupted.")
            except socket.timeout:
                print("Timeout occurred while waiting for message.")
            except Exception as e:
                print(f"Error receiving message: {e}")

    def send_message(self, message):
        for peer in self.peer_list:
            if peer['peer_id'] != self.peer_id:
                checksum = self.calculate_checksum(message.encode())
                data = f"{message},{checksum}"
                self.socket.sendto(data.encode(), ("localhost", peer['port']))
                print(f'Message sent to Peer {peer["peer_id"]}: {message}')
                logging.info(f'Message sent to Peer {peer["peer_id"]}: {message}')
                ack_received = False
                retries = 0
                while not ack_received and retries < 3:
                    try:
                        ack, addr = self.socket.recvfrom(1024)
                        if ack.decode() == "ACK":
                            ack_received = True
                            print("ACK received.")
                    except socket.timeout:
                        retries += 1
                        print("Timeout occurred while waiting for ACK. Retrying...")
                        self.socket.sendto(data.encode(), ("localhost", peer['port']))
                if not ack_received:
                    print("Max retries reached. Message may not have been delivered.")

    def send_ack(self, addr):
        self.socket.sendto("ACK".encode(), addr)

    def calculate_checksum(self, data):
        checksum = 0
        for i in range(0, len(data), 2):
            chunk = (data[i] << 8) + (data[i+1] if i+1 < len(data) else 0)
            checksum += chunk
            if checksum & 0xFFFF0000:
                checksum = (checksum & 0xFFFF) + 1
        checksum = checksum & 0xFFFF
        checksum = ~checksum & 0xFFFF
        return checksum

    def verify_checksum(self, message, received_checksum):
        calculated_checksum = self.calculate_checksum(message.encode())
        return calculated_checksum == received_checksum
    
    def toggle_bit(self, payload, bit_index):
        byte_index = bit_index // 8
        bit_offset = bit_index % 8
        payload_int = int.from_bytes(payload.encode(), byteorder='big')
        # toggle bit at specified index
        mask = 1 << (7 - bit_offset)
        modified_payload_int = payload_int ^ (mask << (byte_index * 8))
        modified_payload_bytes = modified_payload_int.to_bytes((modified_payload_int.bit_length() + 7) // 8, byteorder='big')
        modified_payload = modified_payload_bytes.decode()
        return modified_payload

'''
import logging
import json

class Middleware:
    def __init__(self, peer_id, group_config_file):
        self.peer_id = peer_id
        self.group_config_file = group_config_file

    def start(self):
        logging.basicConfig(filename='middleware_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
        logging.info('Middleware started.')
        print('Middleware started.')

    

        # Implement middleware logic here

# Example usage:
middleware = Middleware(peer_id=1, group_config_file='group_config.txt')
middleware.start()#
'''
