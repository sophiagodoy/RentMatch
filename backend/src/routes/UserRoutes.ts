import { Router, type Request, type Response } from "express";
import { userController } from "../index.js";
import { authMiddleware } from "../middleware/AuthMiddleware.js";

const userRoutes = Router()
userRoutes.post("/register", (req: Request, res: Response) => userController.register(req,res))
userRoutes.post("/login", (req: Request, res: Response) => userController.login(req,res))

userRoutes.get("/me", authMiddleware, (req: Request, res: Response) => userController.me(req,res))
userRoutes.put("/me", authMiddleware, (req: Request, res: Response) => userController.updateMe(req,res))
userRoutes.put("/me/password", authMiddleware, (req: Request, res: Response) => userController.changePassword(req,res))

export {userRoutes}