import type { NextFunction, Request, Response } from "express";
import { verifyToken } from "../utils/TokenService.js";

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
    const authHeader = req.headers.authorization;
    if (!authHeader) return res.status(401).json({ error: 'Token não fornecido' });

    const parts = authHeader.split(' ');
    if (parts.length !== 2) return res.status(401).json({ error: 'Erro no formato do token' });

    const [, token] = parts;
    if (!token) return res.status(401).json({ error: 'Erro ao extrair conteudo do token' });

    try {
        const decoded = verifyToken(token) as { id: string };
        res.locals.userId = decoded.id;
        return next();
    } catch (err) {
        return res.status(401).json({ error: 'Token inválido ou expirado' });
    }
}