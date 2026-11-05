import { UserController } from "./controller/UserController.js";
import { UserRepository } from "./repository/UserRepository.js";
import { UserService } from "./service/UserService.js";
import { EvaluationController } from "./controller/EvaluationController.js";
import { EvaluationRepository } from "./repository/EvaluationRepository.js";
import { EvaluationService } from "./service/EvaluationService.js";

const userRepository = new UserRepository()
const userService = new UserService(userRepository)
export const userController = new UserController(userService)

const evaluationRepository = new EvaluationRepository();
const evaluationService = new EvaluationService(evaluationRepository);
export const evaluationController = new EvaluationController(evaluationService);
