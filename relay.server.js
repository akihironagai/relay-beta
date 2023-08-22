import { createSecureServer } from "http2";
import { createSocket } from "node:dgram";
import { createWriteStream } from "node:fs";
import { readFile } from "node:fs/promises";
import { cursorTo } from "node:readline";
import { Server } from "socket.io";

const port = process.argv[4] || 8443;

const server = createSecureServer(
  {
    allowHTTP1: true,
    key: await readFile(process.argv[2]),
    cert: await readFile(process.argv[3]),
  },
  (req, res) => {
    res.writeHead(200);
    res.end("Hello World!\n");
  }
);

if (process.env.SSLKEYLOGFILE) {
  const logFile = createWriteStream(process.env.SSLKEYLOGFILE, {
    flags: "a",
  });

  server.on("keylog", (line) => {
    logFile.write(line);
  });
}

const io = new Server(server, {
  path: "/relay",
  transports: ["websocket"],
});

io.on("connection", (socket) => {
  let recv = 0;
  let send = 0;

  const { address } = socket.handshake;
  const { hostname, port } = socket.handshake.query;

  const wg = createSocket("udp4");
  wg.bind();

  function update() {
    cursorTo(process.stdout, 0);
    process.stdout.write(
      `[${address}] - [${hostname}] | ↑ ${send} / ↓ ${recv}`
    );
  }

  wg.on("message", (msg) => {
    recv += msg.length;
    socket.emit("wg", msg);
    update();
  });

  socket.on("wg", (msg) => {
    wg.send(msg, port, hostname);
    send += msg.length;
    update();
  });

  socket.on("disconnect", () => {
    wg.close();
    process.stdout.write(` - Disconnected\n`);
  });
});

server.listen(port);
