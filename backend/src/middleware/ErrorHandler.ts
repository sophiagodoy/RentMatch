import type { NextFunction, Request, Response } from "express";
import { ZodError } from "zod";
import { AppError } from "../utils/AppError.js";

export function errorHandler(err: unknown, _req: Request, res: Response, _next: NextFunction) {
    if (err instanceof ZodError) {
        return res.status(400).json({
            message: "Dados invalidos",
            errors: err.issues.map(i => ({ field: i.path.join("."), message: i.message }))
        })
    }
    if (err instanceof AppError) {
        return res.status(err.statusCode).json({ message: err.message })
    }
    
    if (typeof err === "object" && err !== null && (err as any).code === "P2002") {
        return res.status(409).json({ message: "Registro ja existe" })
    }
    console.error(err)
    return res.status(500).json({ message: "Erro interno do servidor" })
}