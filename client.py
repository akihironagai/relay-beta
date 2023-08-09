import socket
import ssl
import os
import threading
import queue

import config

client_proxy_vpn_side_packet: queue.Queue[bytes] = queue.Queue()
client_proxy_proxy_side_packet: queue.Queue[bytes] = queue.Queue()


def client_proxy_proxy_side():
    print("Client Proxy Proxy Side")
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
                    print(f"[C] Remote Proxy -> Local Proxy: {data}")
                    client_proxy_proxy_side_packet.put(data)
                if not client_proxy_vpn_side_packet.empty():
                    data = client_proxy_vpn_side_packet.get()
                    # TODO: 正しく送信できた場合のみ Queue から削除する
                    # VPN -> Proxy
                    ssock.sendall(client_proxy_vpn_side_packet.get())


def client_proxy_vpn_side():
    print("Client Proxy VPN Side")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(config.LOCAL_PROXY_ADDRESS)
        #  sock.setblocking(False)
        while True:
            try:
                data, addr = sock.recvfrom(2048)
            except BlockingIOError:
                data = None
            if data:
                print(f"[C] Local VPN -> Local Proxy: {data}")
                client_proxy_vpn_side_packet.put(data)
            if not client_proxy_proxy_side_packet.empty():
                # Proxy -> VPN
                sock.sendto(
                    client_proxy_proxy_side_packet.get(), config.REMOTE_PROXY_ADDRESS
                )


if __name__ == "__main__":
    proxy_side_thread = threading.Thread(target=client_proxy_proxy_side)
    vpn_side_thread = threading.Thread(target=client_proxy_vpn_side)
    proxy_side_thread.start()
    vpn_side_thread.start()
