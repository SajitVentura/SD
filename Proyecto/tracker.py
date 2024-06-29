import socket
import threading
import time
import hashlib
import os

# Configuración del rastreador
HOST = '0.0.0.0'
PORT = 12345
BUFFER_SIZE = 16777216  # 16 MB
peers = {}
lock = threading.Lock()
running = True

def handle_peer(conn, addr):
    try:
        data = conn.recv(BUFFER_SIZE).decode()
        request = data.split()

        if request[0] == 'ANNOUNCE':
            if len(request) != 5:
                raise ValueError("Formato de mensaje ANNOUNCE incorrecto")

            file_name = request[1]
            peer_id = request[2]
            peer_port = int(request[3])
            file_hash = request[4]

            with lock:
                if file_name not in peers:
                    peers[file_name] = {}
                peers[file_name][peer_id] = (addr[0], peer_port, file_hash)

                peer_list = [
                    f"{p_id}|{ip}:{port}|{file_hash}"
                    for p_id, (ip, port, file_hash) in peers[file_name].items()
                    if p_id != peer_id  # Comparar con p_id
                ]

                response = ",".join(peer_list).encode() if peer_list else b"NO_PEERS"
                conn.sendall(response)

        elif request[0] == 'LIST_FILES':
            with lock:
                file_list = "\n".join([f"{file} (Nodo {peer_id})" for file, peers_list in peers.items() for peer_id in peers_list])
            conn.sendall(file_list.encode() if file_list else b"NO_FILES")

    except ValueError as ve:
        print(f"Error de valor al procesar la solicitud del peer {addr}: {ve}")
        conn.sendall(b"ERROR")
    except Exception as e:
        print(f"Error al procesar la solicitud del peer {addr}: {e}")
        conn.sendall(b"ERROR")
    finally:
        time.sleep(0.1)
        conn.sendall(b"OK")
        conn.close()

def show_network_status():
    global running
    while running:
        with lock:
            print("\nEstado de la red:")
            for file_name, peer_list in peers.items():
                print(f"  Archivo: {file_name}")
                for peer_id, (ip, port, file_hash) in peer_list.items():  # Desempaquetar los 3 elementos
                    print(f"    Peer {peer_id}: {ip}:{port} (Hash: {file_hash})")  # Mostrar el hash
        user_input = input("Presione Enter para actualizar (o escriba 'exit' para detener el tracker): ")
        if user_input.lower() == "exit":
            with lock:
                running = False
                break

if __name__ == '__main__':
    status_thread = threading.Thread(target=show_network_status, daemon=True)
    status_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Rastreador escuchando en {HOST}:{PORT}")
        s.settimeout(1)
        while running:
            try:
                conn, addr = s.accept()
                threading.Thread(target=handle_peer, args=(conn, addr)).start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error en el bucle principal del tracker: {e}")
                break

    status_thread.join()
    print("Tracker detenido.")