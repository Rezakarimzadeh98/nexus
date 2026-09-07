import app from "./app.js";
import { APP_PORT } from "./config/constants.js";

const MAX_PORT_RETRIES = 10;

function configureServerTimeouts(server) {
  server.requestTimeout = 15000;
  server.headersTimeout = 16000;
  server.keepAliveTimeout = 10000;
}

function startServer(port, retriesLeft) {
  const server = app.listen(port, () => {
    if (port !== APP_PORT) {
      console.warn(`Port ${APP_PORT} was busy. Fallback port in use: ${port}`);
    }
    console.log(`Nexus server is running on http://localhost:${port}`);
  });

  configureServerTimeouts(server);

  server.on("error", (error) => {
    if (error?.code === "EADDRINUSE" && retriesLeft > 0) {
      const nextPort = port + 1;
      console.warn(`Port ${port} is in use. Retrying on ${nextPort}...`);
      startServer(nextPort, retriesLeft - 1);
      return;
    }

    throw error;
  });
}

startServer(APP_PORT, MAX_PORT_RETRIES);
