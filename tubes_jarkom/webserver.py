import socket
import threading
import os
import mimetypes
from datetime import datetime

HOST = '127.0.0.1'
TCP_PORT = 8000
UDP_PORT = 9000
BUFFER_SIZE = 4096


def log(message):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] {message}")


# =========================
# HANDLE TCP CLIENT
# =========================
def handle_client(client_socket, addr):
    try:
        request = client_socket.recv(BUFFER_SIZE).decode(errors='ignore')

        if not request:
            return

        request_line = request.split('\r\n')[0]
        parts = request_line.split()

        if len(parts) != 3:
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/html\r\n\r\n"
                "<h1>400 Bad Request</h1>"
            )
            client_socket.sendall(response.encode())
            return

        method, path, version = parts

        if method != 'GET':
            response = (
                "HTTP/1.1 405 Method Not Allowed\r\n"
                "Content-Type: text/html\r\n\r\n"
                "<h1>405 Method Not Allowed</h1>"
            )
            client_socket.sendall(response.encode())
            return

        if path == '/':
            path = '/index.html'

        file_path = '.' + path

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                body = f.read()

            mime_type = mimetypes.guess_type(file_path)[0]
            if mime_type is None:
                mime_type = 'application/octet-stream'

            header = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Type: {mime_type}\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n"
            )

            response = header.encode() + body

            log(f"[TCP] {addr[0]} meminta {path} -> 200 OK")

        else:
            body = b"<h1>404 Not Found</h1>"

            header = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n"
            )

            response = header.encode() + body

            log(f"[TCP] {addr[0]} meminta {path} -> 404")

        client_socket.sendall(response)

    except Exception as e:
        log(f"[ERROR SERVER] {e}")

        try:
            body = b"<h1>500 Internal Server Error</h1>"

            header = (
                "HTTP/1.1 500 Internal Server Error\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n"
            )

            client_socket.sendall(header.encode() + body)

        except:
            pass

    finally:
        client_socket.close()


# =========================
# TCP SERVER
# =========================
def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, TCP_PORT))
    server.listen(20)

    log(f"[WEB SERVER] TCP berjalan di port {TCP_PORT}")

    while True:
        client_socket, addr = server.accept()

        log(f"[NEW CONNECTION] {addr}")

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, addr),
            daemon=True
        )

        thread.start()


# =========================
# UDP ECHO SERVER
# =========================
def udp_server():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((HOST, UDP_PORT))

    log(f"[UDP SERVER] berjalan di port {UDP_PORT}")

    while True:
        data, addr = udp.recvfrom(1024)

        log(f"[UDP] Paket dari {addr[0]}:{addr[1]}")

        udp.sendto(data, addr)


# =========================
# MAIN
# =========================
if __name__ == '__main__':
    tcp_thread = threading.Thread(target=tcp_server, daemon=True)
    udp_thread = threading.Thread(target=udp_server, daemon=True)

    tcp_thread.start()
    udp_thread.start()

    tcp_thread.join()
    udp_thread.join()