import socket
import ssl
import os
import threading
import queue

import config

from_remote_proxy_packet: queue.Queue[bytes] = queue.Queue()
from_local_vpn_packet: queue.Queue[bytes] = queue.Queue()

def local_proxy_to_remote_proxy():
    address = config.REMOTE_PROXY_ADDRESS
    context = ssl.create_default_context(
        cafile=os.getenv("SSL_CA_CERT_FILE"),
    )

    with socket.create_connection(address) as sock:
        with context.wrap_socket(sock, server_hostname=address[0]) as ssock:
            ssock.do_handshake(True)
            ssock.setblocking(False)
            while True:
                try:
                    data = ssock.recv(2048)
                except ssl.SSLWantReadError:
                    data = None
                if data:
                    print(f"[C] Remote Proxy -> *Local Proxy: {data}")
                    from_remote_proxy_packet.put(data)
                if not from_local_vpn_packet.empty():
                    local_data = from_local_vpn_packet.get()
                    print(f"[C] *Local Proxy -> Remote Proxy: {local_data}")
                    ssock.sendall(local_data)


def local_vpn_to_local_proxy():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(config.LOCAL_PROXY_ADDRESS)
        while True:
            data, _ = sock.recvfrom(2048)
            print(f"[C] Local VPN -> *Local Proxy: {data}")
            from_local_vpn_packet.put(data)


def local_proxy_to_local_vpn():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while True:
            try:
                data = from_remote_proxy_packet.get()
            except queue.Empty:
                continue
            print(f"[C] *Local Proxy -> Local VPN: {data}")
            sock.sendto(data, config.LOCAL_VPN_ADDRESS)


if __name__ == "__main__":
    threading.Thread(target=local_proxy_to_remote_proxy).start()
    threading.Thread(target=local_vpn_to_local_proxy).start()
    threading.Thread(target=local_proxy_to_local_vpn).start()
