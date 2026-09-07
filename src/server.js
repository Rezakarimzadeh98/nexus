import app from "./app.js";
import { APP_PORT } from "./config/constants.js";

const server = app.listen(APP_PORT, () => {
  console.log(`Nexus server is running on http://localhost:${APP_PORT}`);
});

server.requestTimeout = 15000;
server.headersTimeout = 16000;
server.keepAliveTimeout = 10000;
