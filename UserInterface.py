import logging
import json
import socket

class UserInterface:
    def __init__(self):
        self.role = self.select_role()
        self.peer_id = int(input("Enter Peer ID: "))
        self.port_number = int(input("Enter Port Number: "))
        self.group_config_file = input("Enter Group Config File: ")
        self.log_file = input("Enter Log File: ")
        self.error_injection = input("Enter Error Injection Parameter: ")
        self.peer_list = self.open_group_config(self.group_config_file)
        
    def open_group_config(self, path):
        # Use config file to create a peer list
        peer_list = []
        try:
            with open(path) as f:
                config = json.load(f)
                for c in config['group']:
                    peer = (c['peer_id'], c['port'])
                    peer_list.append(peer)
                return peer_list
        except FileNotFoundError:
            print("Please specify a valid group config file!")
            exit()

    def select_role(self):
        role = input("Choose your role (1 for sender, 2 for receiver): ")
        if role not in ['1', '2']:
            print("Invalid choice. Please enter '1' for sender or '2' for receiver.")
            exit()
        return 'sender' if role == '1' else 'receiver'

    def start(self):
        logging.basicConfig(filename=self.log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
        logging.info('User Interface started.')
        print('User Interface started.')

        if self.role == 'sender':
            self.sender()
        elif self.role == 'receiver':
            self.receiver()

    def sender(self):
        print("You are in sender mode.")
        recipient_peer_id = self.peer_id
        while True:
            message = input("Enter message to send (or type 'exit' to quit): ")
            if message.lower() == 'exit':
                break
            self.send_message(recipient_peer_id, message)

    def receiver(self):
        print("You are in receiver mode. Waiting for messages...")
        recipient_peer_id = self.peer_id
        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # Bind the socket to the receiver's port
            sock.bind(("localhost", self.port_number))

            while True:
                try:
                    # Receive messages
                    data, addr = sock.recvfrom(1024)
                    sender_peer_id, recipient_peer_id, message = data.decode().split(',', 2)
                    if int(recipient_peer_id) == self.peer_id:
                        logging.info(f'Message received from Peer {sender_peer_id}: {message}')
                        print(f'Message received from Peer {sender_peer_id}: {message}')
                except Exception as e:
                    print(f"Error receiving message: {e}")

    def send_message(self, recipient_peer_id, message):
        # Find recipient's port number
        recipient_port = None
        for peer in self.peer_list:
            if peer[0] == recipient_peer_id:
                recipient_port = peer[1]
                break
        
        if recipient_port is None:
            print("Recipient not found in the group.")
            return

        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            try:
                # Send the message to the recipient
                sock.sendto(f"{self.peer_id},{recipient_peer_id},{message}".encode(), ("localhost", recipient_port))
                logging.info(f'Message sent to Peer {recipient_peer_id}: {message}')
                print(f'Message sent to Peer {recipient_peer_id}: {message}')
            except Exception as e:
                print(f"Error sending message: {e}")

# Example usage:
ui = UserInterface()
ui.start()
