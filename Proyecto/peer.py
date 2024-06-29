import socket
import threading
import os
import json
import time

class Peer:
    def __init__(self, peer_id, tracker_host, tracker_port, files_dir, peer_port):
        self.peer_id = peer_id
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.files_dir = files_dir
        self.peer_port = peer_port
        self.BUFFER_SIZE = 16777216  # 16 MB
        self.checkpoint_dir = f"checkpoints_node_{peer_id.lower()}"
        os.makedirs(self.checkpoint_dir, exist_ok=True)

        self.files = self.get_files_from_directory()
        self.load_state()
        self.announce_files()
        self.start_server()

    def get_files_from_directory(self):
        return [f for f in os.listdir(self.files_dir) if os.path.isfile(os.path.join(self.files_dir, f))]

    def load_state(self):
        state_file = f"peer_{self.peer_id}_state.json"
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
                self.files = state.get('files', [])

    def save_state(self):
        state = {
            'files': self.files,
        }
        state_file = f"peer_{self.peer_id}_state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f)

    def announce_files(self):
        for file in self.files:
            self.send_to_tracker(f"ANNOUNCE {file} {self.peer_id} {self.peer_port}")

    def send_to_tracker(self, message):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with socket.socket() as s:
                    s.settimeout(5)
                    s.connect((self.tracker_host, self.tracker_port))
                    s.sendall(message.encode())
                    response = s.recv(self.BUFFER_SIZE).decode()
                    if response not in ["OK", "NO_PEERS", "NO_FILES"]:
                        print(f"Respuesta inesperada del tracker: {response}")
                    return response
            except (socket.timeout, ConnectionResetError) as e:
                print(f"Error al comunicarse con el tracker (intento {attempt + 1}): {e}")
                time.sleep(1)
        print("No se pudo conectar al tracker después de varios intentos")
        return None

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.peer_port))
        self.server_socket.listen()
        print(f"Nodo {self.peer_id} escuchando en {self.server_socket.getsockname()}")
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        while True:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_request, args=(conn, addr)).start()
            except Exception as e:
                print(f"Error al aceptar conexión: {e}")

    def handle_request(self, conn, addr):
        try:
            data = conn.recv(self.BUFFER_SIZE).decode()
            request = data.split()
            if request[0] == 'GET':
                file_name, piece_index = request[1], int(request[2])
                file_path = os.path.join(self.files_dir, file_name)
                if file_name in self.files and os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        f.seek(piece_index * self.BUFFER_SIZE)
                        chunk = f.read(self.BUFFER_SIZE)
                        conn.sendall(chunk)
                else:
                    conn.sendall(b"FILE_NOT_FOUND")
        except ConnectionAbortedError:
            print(f"Conexión abortada por el cliente {addr}")
        except Exception as e:
            print(f"Error al manejar la solicitud de {addr}: {e}")
        finally:
            conn.close()

    def download_file(self, file_name, peer_id, peer_address):
        os.makedirs(self.files_dir, exist_ok=True)
        file_path = os.path.join(self.files_dir, file_name)
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{file_name}.checkpoint")

        # Verificar si existe un checkpoint
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r') as f:
                checkpoint_data = json.load(f)
                received_bytes = checkpoint_data['received_bytes']
                file_size = checkpoint_data['file_size']
        else:
            received_bytes = 0
            file_size = 0

        try:
            with socket.socket() as s:
                s.settimeout(10)
                s.connect(peer_address)
                with open(file_path, 'ab') as f:
                    piece_index = received_bytes // self.BUFFER_SIZE
                    while True:
                        s.sendall(f"GET {file_name} {piece_index}".encode())
                        chunk = s.recv(self.BUFFER_SIZE)
                        if not chunk or chunk == b"FILE_NOT_FOUND":
                            break
                        f.write(chunk)
                        received_bytes += len(chunk)
                        piece_index += 1

                        # Guardar checkpoint
                        with open(checkpoint_path, 'w') as checkpoint_file:
                            json.dump({
                                'received_bytes': received_bytes,
                                'file_size': max(file_size, received_bytes)
                            }, checkpoint_file)

                        # Calcula y muestra la barra de progreso
                        if file_size == 0:
                            file_size = os.path.getsize(file_path)
                        progress = min(received_bytes, file_size)
                        percent = (progress / file_size) * 100 if file_size > 0 else 0
                        print(f"Descargando {file_name} desde Nodo {peer_id}: [{'#' * int(percent / 10)}{'.' * (10 - int(percent / 10))}] {percent:.2f}%", end='\r')

                        if len(chunk) < self.BUFFER_SIZE:
                            break

            print(f"\nDescarga de {file_name} desde Nodo {peer_id} completada.")
            self.files.append(file_name)
            self.save_state()
            os.remove(checkpoint_path)  # Eliminar el checkpoint después de la descarga completa
        except Exception as e:
            print(f"\nError al descargar {file_name} desde Nodo {peer_id}: {e}")
            print("La descarga se reanudará desde el último punto guardado en el próximo intento.")

    def get_peers_from_tracker(self, file_name):
        response = self.send_to_tracker(f"ANNOUNCE {file_name} {self.peer_id} {self.peer_port}")
        if response and response != "NO_PEERS":
            return [tuple(peer_info.split('|')) for peer_info in response.split(',') if peer_info]
        return []

    def show_available_files(self):
        response = self.send_to_tracker("LIST_FILES")
        if response and response != "NO_FILES":
            print("\nLista de Archivos:")
            for file_info in response.split('\n'):
                if file_info:
                    print(file_info)
        else:
            print("No hay archivos disponibles en la red.")

    def run(self):
        while True:
            self.show_available_files()
            file_to_download = input("Ingresa el nombre del archivo que deseas descargar (o 'q' para salir): ")
            if file_to_download.lower() == 'q':
                break

            peers = self.get_peers_from_tracker(file_to_download)
            if peers:
                num_nodes_to_download_from = min(len(peers), 3)
                threads = []
                for i in range(num_nodes_to_download_from):
                    peer_id, peer_addr_str = peers[i]
                    peer_ip, peer_port_str = peer_addr_str.split(':')
                    peer_addr = (peer_ip, int(peer_port_str))
                    t = threading.Thread(target=self.download_file, args=(file_to_download, peer_id, peer_addr))
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join()

                self.save_state()
            else:
                print(f"No se encontraron peers que compartan '{file_to_download}'")

if __name__ == '__main__':
    peer_id = input("Ingresa el ID del nodo (A, B o C): ").upper()
    files_dir = f"archivos_nodo_{peer_id.lower()}"

    peer_ports = {'A': 50001, 'B': 50002, 'C': 50003}
    peer_port = peer_ports.get(peer_id)

    peer = Peer(peer_id, 'localhost', 12345, files_dir, peer_port)
    peer.run()