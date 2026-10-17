import type { Request, Response } from "express";
import type { UserService } from "../service/UserService.js";
import { UserChangePasswordSchemaDto, UserLoginSchemaDto, UserRegisterSchemaDto, UserUpdateProfileSchemaDto } from "../models/User.js";

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

    async me(req: Request, res: Response) {
        const user = await this.userService.getProfile(res.locals.userId)
        return res.status(200).json(user)
    }

    async updateMe(req: Request, res: Response) {
        const data = UserUpdateProfileSchemaDto.parse(req.body)
        const user = await this.userService.updateProfile(res.locals.userId, data)
        return res.status(200).json(user)
    }

    async changePassword(req: Request, res: Response) {
        const data = UserChangePasswordSchemaDto.parse(req.body)
        await this.userService.changePassword(res.locals.userId, data)
        return res.status(204).send()
    }
}