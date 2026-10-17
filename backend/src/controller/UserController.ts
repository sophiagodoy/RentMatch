import type { Request, Response } from "express";
import type { UserService } from "../service/UserService.js";
import { UserLoginSchemaDto, UserRegisterSchemaDto } from "../models/User.js";

export class UserController {
    constructor(private readonly userService: UserService) {}

    async register(req: Request, res: Response) {
        const data = UserRegisterSchemaDto.parse(req.body)
        const userCreated = await this.userService.register(data)
        return res.status(201).json(userCreated)
    }

    async login(req: Request, res: Response) {
        const data = UserLoginSchemaDto.parse(req.body)
        const token = await this.userService.login(data)
        return res.status(200).json({token})
    }
}