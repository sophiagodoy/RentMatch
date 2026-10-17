import { Router, type Request, type Response } from "express";
import { userController } from "../index.js";

const userRoutes = Router()
userRoutes.post("/register", (req: Request, res: Response) => userController.register(req,res))
userRoutes.post("/login", (req: Request, res: Response) => userController.login(req,res))
export {userRoutes}