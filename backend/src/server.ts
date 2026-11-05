import express from "express"
import "dotenv/config"
import { userRoutes } from "./routes/UserRoutes.js"
import { evaluationRoutes } from "./routes/EvaluationRoutes.js"
import { errorHandler } from "./middleware/ErrorHandler.js"

const app = express()
const port = process.env.PORT

app.use(express.json())
app.use("/user", userRoutes)
app.use("/evaluations", evaluationRoutes)

app.use(errorHandler);

app.listen(port, () => console.log(`Servidor rodando na porta ${port}`))
