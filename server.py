import socket
import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('127.0.0.1.pem', '127.0.0.1-key.pem')

with socket.create_server(('127.0.0.1', 8443)) as sock:
    sock.listen(5)
    with context.wrap_socket(sock, server_side=True) as ssock:
        conn, addr = ssock.accept()
        while True:
            print(conn.recv(1024))
