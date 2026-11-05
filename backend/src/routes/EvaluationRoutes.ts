import { Router, type Request, type Response } from "express";
import { evaluationController } from "../index.js";
import { authMiddleware } from "../middleware/AuthMiddleware.js";

const evaluationRoutes = Router();

evaluationRoutes.post(
    "/",
    authMiddleware,
    (req: Request, res: Response) => evaluationController.create(req, res)
);

evaluationRoutes.get(
    "/",
    authMiddleware,
    (req: Request, res: Response) => evaluationController.list(req, res)
);

// Rotas GET fixas, como /summary e /options, devem vir antes de /:id.
evaluationRoutes.get(
    "/:id",
    authMiddleware,
    (req: Request, res: Response) => evaluationController.getById(req, res)
);

evaluationRoutes.patch(
    "/:id/save",
    authMiddleware,
    (req: Request, res: Response) => evaluationController.save(req, res)
);

evaluationRoutes.delete(
    "/:id",
    authMiddleware,
    (req: Request, res: Response) => evaluationController.delete(req, res)
);

export { evaluationRoutes };
