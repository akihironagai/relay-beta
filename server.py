import socket
import ssl
import threading
import queue

import config

from_local_proxy_packet: queue.Queue[bytes] = queue.Queue()
from_remote_vpn_packet: queue.Queue[bytes] = queue.Queue()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(f'{config.REMOTE_VPN_ADDRESS[0]}.pem', f'{config.REMOTE_VPN_ADDRESS[0]}-key.pem')

def local_proxy_to_remote_proxy():
    with socket.create_server(config.TCP_TUNNEL) as sock:
        sock.listen(5)
        with context.wrap_socket(sock, server_side=True) as ssock:
            conn, addr = ssock.accept()
            conn.setblocking(False)
            while True:
                try:
                    data = conn.recv(1024)
                except ssl.SSLWantReadError as e:
                    data = None
                if data:
                    print(f"[S] Local Proxy -> *Remote Proxy: {data}")
                    from_local_proxy_packet.put(data)
                if not from_remote_vpn_packet.empty():
                    remote_data = from_remote_vpn_packet.get()
                    print(f"[S] *Remote Proxy -> Local Proxy: {remote_data}")
                    conn.sendall(remote_data)

def remote_proxy_to_remote_vpn():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while True:
            try:
                data = from_local_proxy_packet.get()
            except queue.Empty:
                continue
            print(f"[S] *Remote Proxy -> Remote VPN: {data}")
            sock.sendto(data, config.REMOTE_VPN_ADDRESS)

def remote_vpn_to_remote_proxy():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(config.REMOTE_PROXY_ADDRESS)
        while True:
            data, _ = sock.recvfrom(2048)
            print(f"[S] Remote VPN -> *Remote Proxy: {data}")
            from_remote_vpn_packet.put(data)

if __name__ == "__main__":
    threading.Thread(target=local_proxy_to_remote_proxy).start()
    threading.Thread(target=remote_vpn_to_remote_proxy).start()
    threading.Thread(target=remote_proxy_to_remote_vpn).start()