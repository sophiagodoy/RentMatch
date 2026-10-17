import { UserController } from "./controller/UserController.js";
import { UserRepository } from "./repository/UserRepository.js";
import { UserService } from "./service/UserService.js";

const userRepository = new UserRepository()
const userService = new UserService(userRepository)
export const userController = new UserController(userService)
