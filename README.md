# WireGuard over TLS Relay System

It allows you to use WireGuard when your ISP or network administrator blocks WireGuard connections by wrapping WireGuard packets in TLS packets.

# How does it work?

```text
+------------------------------------+
|  +-----------+   +--------------+  |  +--------------+   +-----------+
|  | WG Client |<->| Relay Client |<--->| Relay Server |<->| WG Server |
|  +-----------+   +--------------+  |  +--------------+   +-----------+
+------------------------------------+
```

## Usage

Note that you have to configure a WireGuard server because this script only wraps WireGuard packets in TLS packets and forwards them to the WireGuard server.

### Relay Server

```bash
node relay.server.js /path/to/key /path/to/cert 8443
```

First argument is the path to the private key file, second argument is the path to the certificate file, third argument is the port number.

### Relay Client

```bash
node relay.client.js https://relay-server.example.com vpn-server.example.com 51820 51820
```

First argument is the URL of the relay server, second argument is the domain name or IP address of the WireGuard server, third argument is the port number of the WireGuard server, fourth argument is the local port number of receiving WireGuard packets.

### Security Considerations

It forwards all packets to the WireGuard server **without** any filtering.
