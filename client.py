import socket
import ssl
import os

hostname = '127.0.0.1'
context = ssl.create_default_context(
    cafile=os.getenv('SSL_CA_CERT_FILE'),
)

with socket.create_connection((hostname, 8443)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        ssock.do_handshake()
        ssock.setblocking(False)
        while True:
            ssock.send(b"hello client\n")
            try:
                print(ssock.recv(1024))
            except ssl.SSLWantReadError:
                pass