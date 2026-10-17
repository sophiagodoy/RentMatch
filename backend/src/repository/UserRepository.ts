import { prisma } from "../lib/prisma.js";
import { UserEntitySchema, UserResponseSchemaDto, type UserRegisterDTO, type UserUpdateDTO } from "../models/User.js";

export class UserRepository {
    async create(data: UserRegisterDTO) {
        const { name, email, password } = data
        const user = await prisma.user.create({
            data: {
                name,
                email,
                password
            }
        })
        return UserResponseSchemaDto.parse(user)
    }

    async update(id: string, data: UserUpdateDTO) {
        let { name, email, password } = data
        const user = await prisma.user.update({
            where: {id},
            data: {
                name,
                email,
                password
            }
        })
        return UserResponseSchemaDto.parse(user)
    }

    async findById(id: string) {
        const user = await prisma.user.findUnique({
            where: {id}
        })
        return UserResponseSchemaDto.parse(user)
    }

    async findByEmail(email: string) {
        const userFound = await prisma.user.findUnique({
            where: {email}
        })
        return UserEntitySchema.parse(userFound)
    }

    async delete(id: string) {
        await prisma.user.delete({
            where: {id}
        })
    }
}