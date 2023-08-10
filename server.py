import socket
import ssl
import threading
import queue

import config

from_local_proxy_packet: queue.Queue[bytes] = queue.Queue()
from_remote_vpn_packet: queue.Queue[bytes] = queue.Queue()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config.CERT_FILE, config.KEY_FILE)

def local_proxy_to_remote_proxy():
    with socket.create_server(("0.0.0.0", config.TCP_TUNNEL_PORT)) as sock:
        sock.listen(5)
        with context.wrap_socket(sock, server_side=True) as ssock:
            conn, _ = ssock.accept()
            conn.setblocking(False)
            while True:
                try: data = conn.recv(1024)
                except ssl.SSLWantReadError: data = None
                if data:
                    print(f"[S] Local Proxy -> *Remote Proxy: {len(data)}")
                    from_local_proxy_packet.put(data)
                if not from_remote_vpn_packet.empty():
                    remote_data = from_remote_vpn_packet.get()
                    print(f"[S] *Remote Proxy -> Local Proxy: {len(remote_data)}")
                    conn.sendall(remote_data)

def remote_vpn_and_remote_proxy():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("0.0.0.0", config.REMOTE_PROXY_ADDRESS[1]))

        def recv():
            while True:
                data, _ = sock.recvfrom(2048)
                print(f"[S] Remote VPN -> *Remote Proxy: {len(data)}")
                from_remote_vpn_packet.put(data)

        def send():
            while True:
                try: data = from_local_proxy_packet.get()
                except queue.Empty: return
                print(f"[S] *Remote Proxy -> Remote VPN: {len(data)}")
                sock.sendto(data, config.REMOTE_VPN_ADDRESS)

        threading.Thread(target=recv).start()
        threading.Thread(target=send).start()

        while True:
            ...

if __name__ == "__main__":
    threading.Thread(target=local_proxy_to_remote_proxy).start()
    remote_vpn_and_remote_proxy()