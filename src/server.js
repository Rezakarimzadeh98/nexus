import app from "./app.js";
import { APP_PORT } from "./config/constants.js";

app.listen(APP_PORT, () => {
  console.log(`Nexus server is running on http://localhost:${APP_PORT}`);
});
