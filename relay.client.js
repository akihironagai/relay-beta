import { HttpsProxyAgent } from "https-proxy-agent";
import { createSocket } from "node:dgram";
import { cursorTo } from "node:readline";
import { io } from "socket.io-client";

let wg_port;
let recv = 0;
let send = 0;

const wg = createSocket("udp4");

let agent = false;
if (process.env.HTTPS_PROXY) {
  agent = new HttpsProxyAgent(process.env.HTTPS_PROXY);
} else if (process.argv[6]) {
  agent = new HttpsProxyAgent(process.argv[6]);
}

const socket = io(process.argv[2], {
  agent,
  path: "/relay",
  query: {
    hostname: process.argv[3],
    port: process.argv[4],
  },
  transports: ["websocket"],
});

function update() {
  cursorTo(process.stdout, 0);
  process.stdout.write(`↑ ${send} / ↓ ${recv}`);
}

socket.on("connect", () => {
  update();
});

wg.on("message", (msg, rinfo) => {
  if (rinfo.port !== wg_port) {
    wg_port = rinfo.port;
  }
  recv += msg.length;
  socket.emit("wg", msg);
  update();
});

socket.on("wg", (msg) => {
  wg.send(msg, wg_port, "127.0.0.1");
  send += msg.length;
  update();
});

wg.bind(process.argv[5], "127.0.0.1");
