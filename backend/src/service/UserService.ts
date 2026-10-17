import type { UserLoginDTO, UserRegisterDTO } from "../models/User.js";
import type { UserRepository } from "../repository/UserRepository.js";
import { hash, compare } from "bcryptjs"
import { generateToken } from "../utils/TokenService.js";

export class UserService {
    constructor(private readonly userRepository: UserRepository) {}

    async register(data: UserRegisterDTO) {
        const { password } = data
        data.password = await hash(password, 12)
        const userCreated = await this.userRepository.create(data)
        return userCreated;    
    }

    async login(data: UserLoginDTO) {
        const {email, password} = data
        const user = await this.userRepository.findByEmail(email)
        if (!user) throw new Error("Email ou senha incorretos")
        const passwordCorrect = await compare(password, user.password)
        if (!passwordCorrect) throw new Error("Email ou senha incorretos")
        const token = await generateToken(user.id)
        return token
    }
}