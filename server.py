import socket
import ssl

import config

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('127.0.0.1.pem', '127.0.0.1-key.pem')

with socket.create_server(config.REMOTE_PROXY_ADDRESS) as sock:
    sock.listen(5)
    with context.wrap_socket(sock, server_side=True) as ssock:
        conn, addr = ssock.accept()
        conn.setblocking(False)
        while True:
            try:
                data = conn.recv(1024)
                if data:
                    print(f"[S] Local Proxy -> *Remote Proxy: {data}")
                    print(f"[S] *Remote Proxy -> Local Proxy: {data}")
                    conn.sendall(data + b" [ECHO]")
            except ssl.SSLWantReadError:
                pass