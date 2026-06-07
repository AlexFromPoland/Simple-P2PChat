import socket
import threading
import json
import time

class P2PChat:
    def __init__(self, nick, discovery_port=5000, chat_port=4000):
        self.nick = nick
        self.discovery_port = discovery_port
        self.chat_port = chat_port

        self.peers = {}
        self.running = True
        self.lock = threading.Lock()

        # discovery
        self.udp_socket = None
        # TCP chat 
        self.tcp_server = None
        
    def _get_my_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
        
    def start(self):
        # UDP do discovery
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(('', self.discovery_port))
        
        # TCP server do odbierania połączeń
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server.bind(('', self.chat_port))
        self.tcp_server.listen(5)

        # Uruchom wątki
        threading.Thread(target=self.broadcast, daemon=True).start()
        threading.Thread(target=self.listen_for_peers, daemon=True).start()
        threading.Thread(target=self.accept_connections, daemon=True).start()  # DODANE
        threading.Thread(target=self.connect_to_peers, daemon=True).start()
        threading.Thread(target=self.receive_messages, daemon=True).start()
        threading.Thread(target=self.console_input, daemon=True).start()  # ZMIENIONE

        print(f"\n[{self.nick}] Czat uruchomiony!")
        print(f"Twój IP: {self._get_my_ip()}")
        print(f"Port TCP: {self.chat_port}")
        print(f"Możesz wpisywać wiadomości")
        print(f"Aby wyjść, wpisz '/quit'\n")

    def broadcast(self):
        """wysyła wiadomość broadcast do każdego w sieci lokalnej co 3 sekundy"""
        message = json.dumps({
            "type": "HELLO",
            "user": self.nick,
            "chat_port": self.chat_port,
        })

        while self.running:
            try:
                self.udp_socket.sendto(
                    message.encode(),
                    ('255.255.255.255', self.discovery_port)
                )
            except:
                pass
            time.sleep(3)
    
    def listen_for_peers(self):
        """nasłuchuje broadcast by szukać nowych peerów w sieci"""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                msg = json.loads(data.decode())
                sender_ip = addr[0]
                sender_port = addr[1]

                if sender_ip == self._get_my_ip():
                    continue

                with self.lock:
                    if sender_ip not in self.peers:
                        print(f"\n[ODKRYTO] nowy peer: {msg['user']} ({sender_ip})")
                        print("> ", end="", flush=True)

                        self.peers[sender_ip] = {
                            "nick": msg["user"],
                            "chat_port": msg["chat_port"],
                        }
                        
                        self.send_udp_response(sender_ip, sender_port)

            except Exception as e:
                pass
    
    def send_udp_response(self, target_ip, target_port):
        """wysyła odpowiedź UDP do konkretnego peera"""
        message = json.dumps({
            "type": "HELLO",
            "user": self.nick,
            "chat_port": self.chat_port,
        })
        try:
            self.udp_socket.sendto(message.encode(), (target_ip, target_port))
        except Exception as e:
            pass

    def accept_connections(self):
        """akceptuje połączenia TCP od peerów"""
        while self.running:
            try:
                client_socket, client_addr = self.tcp_server.accept()
                
                with self.lock:
                    ip = client_addr[0]
                    if ip in self.peers:
                        self.peers[ip]['tcp_socket'] = client_socket
                        print(f"\n[POŁĄCZONO] {self.peers[ip]['nick']} ({ip}) przez TCP")
                        print("> ", end="", flush=True)
                    else:
                        # Nieznany peer - zamknij połączenie
                        client_socket.close()
                        
            except Exception as e:
                if self.running:
                    pass

    def connect_to_peers(self):
        """nawiązuje połączenia TCP z odkrytymi peerami"""
        while self.running:
            with self.lock:
                for ip, peer_data in self.peers.items():
                    if 'tcp_socket' not in peer_data:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(3)
                            sock.connect((ip, peer_data['chat_port']))
                            peer_data['tcp_socket'] = sock
                            print(f"\n[POŁĄCZONO] z {peer_data['nick']} ({ip}) przez TCP")
                            print("> ", end="", flush=True)
                        except Exception as e:
                            pass  # Nie udało się połączyć
            time.sleep(5)

    def send_to_all(self, message):
        """wysyła wiadomość do wszystkich podłączonych peerów przez TCP"""
        if not message:
            return
            
        with self.lock:
            for ip, peer_data in self.peers.items():
                if 'tcp_socket' in peer_data:
                    try:
                        data = json.dumps({
                            "user": self.nick,
                            "message": message
                        })
                        peer_data['tcp_socket'].send(data.encode())
                    except Exception as e:
                        # Usuń uszkodzone połączenie
                        if 'tcp_socket' in peer_data:
                            del peer_data['tcp_socket']
                        print(f"\n[UTRATA] połączenia z {peer_data['nick']}")
                        print("> ", end="", flush=True)

    def receive_messages(self):
        """odczytuje wiadomości od wszystkich peerów przez TCP"""
        while self.running:
            with self.lock:
                for ip, peer_data in list(self.peers.items()):
                    if 'tcp_socket' in peer_data:
                        try:
                            peer_data['tcp_socket'].setblocking(False)
                            try:
                                data = peer_data['tcp_socket'].recv(4096)
                                if data:
                                    msg = json.loads(data.decode())
                                    print(f"\n[{peer_data['nick']}]: {msg['message']}")
                                    print("> ", end="", flush=True)
                            except BlockingIOError:
                                pass  # Brak danych
                            except:
                                # Połączenie zerwane
                                if 'tcp_socket' in peer_data:
                                    del peer_data['tcp_socket']
                                print(f"\n[ROZŁĄCZONO] {peer_data['nick']}")
                                print("> ", end="", flush=True)
                        except Exception as e:
                            pass
            
            time.sleep(0.1)

    def console_input(self):
        """czyta wejście z konsoli i wysyła wiadomości"""
        while self.running:
            try:
                message = input("> ")
                
                if message.lower() == '/quit':
                    self.running = False
                    break
                
                if message:
                    self.send_to_all(message)
                    
            except EOFError:
                break
            except:
                pass

def main():
    nick = input("Podaj swój nick: ")
    chat = P2PChat(nick)
    chat.start()
    
    try:
        while chat.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZamykanie czatu...")
        chat.running = False

if __name__ == "__main__":
    main()