import express from "express"
import "dotenv/config"
import { userRoutes } from "./routes/UserRoutes.js"

const app = express()
const port = process.env.PORT

app.use(express.json())
app.use("/user", userRoutes)

app.listen(port, () => console.log(`Servidor rodando na porta ${port}`))