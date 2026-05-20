import socket
import sys
import time
import threading
import statistics

PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8080

UDP_SERVER_HOST = '127.0.0.1'
UDP_SERVER_PORT = 9000

BUFFER_SIZE = 4096


# ==========================================
# HTTP CLIENT (TCP)
# ==========================================
def http_client(path='/index.html'):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        start_time = time.time()

        client.connect((PROXY_HOST, PROXY_PORT))

        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {PROXY_HOST}\r\n"
            "Connection: close\r\n\r\n"
        )

        client.sendall(request.encode())

        response = b""

        while True:
            data = client.recv(BUFFER_SIZE)

            if not data:
                break

            response += data

        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        print("\n===================================")
        print("HTTP RESPONSE")
        print("===================================\n")

        print(response.decode(errors='ignore'))

        print(f"\n[INFO] Response Time: {response_time:.2f} ms")

    except Exception as e:
        print(f"[ERROR TCP CLIENT] {e}")

    finally:
        client.close()


# ==========================================
# UDP QoS TEST
# ==========================================
def udp_qos():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    client.settimeout(1)

    rtts = []
    packet_lost = 0
    total_bytes = 0

    print("\n===================================")
    print("UDP QoS TEST")
    print("===================================\n")

    overall_start = time.time()

    for seq in range(10):

        send_time = time.time()

        message = f"Ping {seq} {send_time}"

        total_bytes += len(message.encode())

        try:
            client.sendto(
                message.encode(),
                (UDP_SERVER_HOST, UDP_SERVER_PORT)
            )

            data, server = client.recvfrom(1024)

            receive_time = time.time()

            rtt = (receive_time - send_time) * 1000

            rtts.append(rtt)

            print(
                f"Ping {seq} | RTT = {rtt:.2f} ms"
            )

        except socket.timeout:
            print(
                f"Ping {seq} | Request Timed Out"
            )

            packet_lost += 1

        time.sleep(1)

    overall_end = time.time()

    total_duration = overall_end - overall_start

    print("\n===================================")
    print("HASIL QoS")
    print("===================================\n")

    if len(rtts) > 0:

        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)

        print(f"Min RTT       : {min_rtt:.2f} ms")
        print(f"Avg RTT       : {avg_rtt:.2f} ms")
        print(f"Max RTT       : {max_rtt:.2f} ms")

        # ==========================================
        # JITTER
        # ==========================================
        jitters = []

        for i in range(1, len(rtts)):
            jitter_value = abs(rtts[i] - rtts[i - 1])
            jitters.append(jitter_value)

        if len(jitters) > 0:
            avg_jitter = sum(jitters) / len(jitters)
        else:
            avg_jitter = 0

        print(f"Jitter        : {avg_jitter:.2f} ms")

        # ==========================================
        # THROUGHPUT
        # ==========================================
        throughput = (
            (total_bytes * 8)
            / total_duration
        ) / 1000

        print(f"Throughput    : {throughput:.2f} kbps")

    # ==========================================
    # PACKET LOSS
    # ==========================================
    packet_loss_percentage = (
        packet_lost / 10
    ) * 100

    print(
        f"Packet Loss   : {packet_loss_percentage:.2f}%"
    )

    client.close()


# ==========================================
# MULTI CLIENT TEST
# ==========================================
def multi_client_test():

    print("\n===================================")
    print("MULTI CLIENT TEST")
    print("===================================\n")

    threads = []

    for i in range(5):

        print(f"[CLIENT {i+1}] Starting...")

        thread = threading.Thread(
            target=http_client,
            args=('/index.html',)
        )

        threads.append(thread)

        thread.start()

    for thread in threads:
        thread.join()

    print("\n===================================")
    print("SEMUA CLIENT SELESAI")
    print("===================================\n")


# ==========================================
# MAIN PROGRAM
# ==========================================
if __name__ == "__main__":

    if len(sys.argv) < 3:

        print("\nGunakan:")
        print("python client.py --mode tcp")
        print("python client.py --mode udp")
        print("python client.py --mode multi")

    elif sys.argv[1] == "--mode":

        mode = sys.argv[2]

        if mode == "tcp":
            http_client()

        elif mode == "udp":
            udp_qos()

        elif mode == "multi":
            multi_client_test()

        else:
            print("[ERROR] Mode tidak dikenali")