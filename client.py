import socket
import ssl
import time
import os

hostname = '127.0.0.1'
context = ssl.create_default_context(
    cafile=os.getenv('SSL_CA_CERT_FILE'),
)

with socket.create_connection((hostname, 8443)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print(ssock.version())
        while True:
            ssock.send(b"hello world\n")
            time.sleep(1)