import express from "express"
import { fileURLToPath } from "node:url"
import "dotenv/config"
import { userRoutes } from "./routes/UserRoutes.js"
import { evaluationRoutes } from "./routes/EvaluationRoutes.js"
import { errorHandler } from "./middleware/ErrorHandler.js"

const app = express()
const port = process.env.PORT
const frontendDirectory = fileURLToPath(new URL("../../frontend/src/", import.meta.url))

const frontendOrigins = new Set([
    "http://localhost:5500",
    "http://127.0.0.1:5500"
]);

app.use((req, res, next) => {
    const origin = req.headers.origin;

    if (origin && frontendOrigins.has(origin)) {
        res.setHeader("Access-Control-Allow-Origin", origin);
        res.setHeader("Vary", "Origin");
        res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
        res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS");
    }

    if (req.method === "OPTIONS") return res.sendStatus(204);
    next();
});

app.use(express.json())
app.use("/user", userRoutes)
app.use("/evaluations", evaluationRoutes)

app.get("/", (_req, res) => res.redirect("/html/login.html"))
app.use(express.static(frontendDirectory))

app.use(errorHandler);

app.listen(port, () => console.log(`Servidor rodando na porta ${port}`))
