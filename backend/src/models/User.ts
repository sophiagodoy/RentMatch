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

// Acrescente ao final de models/User.ts

export const UserUpdateProfileSchemaDto = UserEntitySchema.pick({
    name: true,
    email: true
}).partial()

export const UserChangePasswordSchemaDto = z.object({
    currentPassword: z.string().min(1, "Informe a senha atual"),
    newPassword: z.string().min(6, "A senha deve ter no minimo 6 caracteres."),
    confirmNewPassword: z.string()
}).refine(d => d.newPassword === d.confirmNewPassword, {
    message: "As senhas nao conferem",
    path: ["confirmNewPassword"]
})

export type UserRegisterDTO = z.infer<typeof UserRegisterSchemaDto>
export type UserUpdateDTO = z.infer<typeof UserUpdateSchemaDto>
export type UserLoginDTO = z.infer<typeof UserLoginSchemaDto>
export type UserResponseDTO = z.infer<typeof UserResponseSchemaDto>
export type UserUpdateProfileDTO = z.infer<typeof UserUpdateProfileSchemaDto>
export type UserChangePasswordDTO = z.infer<typeof UserChangePasswordSchemaDto>