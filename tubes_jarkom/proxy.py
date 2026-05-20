import socket
import threading
import os
import time
from datetime import datetime

PROXY_HOST = '0.0.0.0'
PROXY_PORT = 8080

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8000

BUFFER_SIZE = 4096
CACHE_DIR = 'cache'

os.makedirs(CACHE_DIR, exist_ok=True)

cache_lock = threading.Lock()


def log(message):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] {message}")


# =========================
# HANDLE CLIENT
# =========================
def handle_client(client_socket, addr):
    start_time = time.time()

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

        if path == '/':
            path = '/index.html'

        cache_name = path.replace('/', '_').replace('?', '_')
        cache_file = os.path.join(CACHE_DIR, cache_name)

        # =========================
        # CACHE HIT
        # =========================
        if os.path.exists(cache_file):
            with cache_lock:
                with open(cache_file, 'rb') as f:
                    cached_data = f.read()

            client_socket.sendall(cached_data)

            elapsed = (time.time() - start_time) * 1000

            log(f"[CACHE HIT] {addr[0]} -> {path} ({elapsed:.2f} ms)")
            return

        # =========================
        # CACHE MISS
        # =========================
        log(f"[CACHE MISS] {addr[0]} -> {path}")

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(5)

        try:
            server_socket.connect((SERVER_HOST, SERVER_PORT))

            forward_request = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {SERVER_HOST}\r\n"
                "Connection: close\r\n\r\n"
            )

            server_socket.sendall(forward_request.encode())

            response = b''

            while True:
                data = server_socket.recv(BUFFER_SIZE)

                if not data:
                    break

                response += data

            client_socket.sendall(response)

            with cache_lock:
                with open(cache_file, 'wb') as f:
                    f.write(response)

            elapsed = (time.time() - start_time) * 1000

            log(f"[FORWARD] {path} selesai ({elapsed:.2f} ms)")

        except socket.timeout:
            response = (
                "HTTP/1.1 504 Gateway Timeout\r\n"
                "Content-Type: text/html\r\n\r\n"
                "<h1>504 Gateway Timeout</h1>"
            )

            client_socket.sendall(response.encode())

            log(f"[TIMEOUT] {path}")

        except Exception as e:
            response = (
                "HTTP/1.1 502 Bad Gateway\r\n"
                "Content-Type: text/html\r\n\r\n"
                "<h1>502 Bad Gateway</h1>"
            )

            client_socket.sendall(response.encode())

            log(f"[BAD GATEWAY] {e}")

        finally:
            server_socket.close()

    except Exception as e:
        log(f"[PROXY ERROR] {e}")

    finally:
        client_socket.close()


# =========================
# START PROXY
# =========================
def start_proxy():
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    proxy.bind((PROXY_HOST, PROXY_PORT))
    proxy.listen(20)

    log(f"[PROXY] berjalan di port {PROXY_PORT}")

    while True:
        client_socket, addr = proxy.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, addr),
            daemon=True
        )

        thread.start()


# =========================
# MAIN
# =========================
if __name__ == '__main__':
    start_proxy()