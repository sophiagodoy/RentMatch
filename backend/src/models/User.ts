import z from "zod";

export const UserEntitySchema = z.object({
    id: z.uuid(),
    name: z.string().min(2, "Nome invalido"),
    email: z.email("email invalido"),
    password: z.string(),
    createdAt: z.date()
})

export const UserRegisterSchemaDto = UserEntitySchema.omit({
    id: true,
    createdAt: true
}).extend({
    password: z.string().min(6, "A senha deve ter no minimo 6 caracteres.")
})

export const UserUpdateSchemaDto = UserRegisterSchemaDto.partial()

export const UserLoginSchemaDto = UserEntitySchema.pick({
    email: true,
    password: true
})

export const UserResponseSchemaDto = UserEntitySchema.omit({
    password: true
})

export type UserRegisterDTO = z.infer<typeof UserRegisterSchemaDto>
export type UserUpdateDTO = z.infer<typeof UserUpdateSchemaDto>
export type UserLoginDTO = z.infer<typeof UserLoginSchemaDto>
export type UserResponseDTO = z.infer<typeof UserResponseSchemaDto>