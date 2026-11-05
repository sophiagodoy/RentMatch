import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { EvaluationPredictionSchema, type EvaluationCreateDTO, type EvaluationPrediction } from "../models/Evaluation.js";
import { AppError } from "../utils/AppError.js";

const modelDirectory = fileURLToPath(new URL("../../../modelo_ml/", import.meta.url));
const localPython = fileURLToPath(new URL(
    process.platform === "win32" ? "../../../.venv/Scripts/python.exe" : "../../../.venv/bin/python",
    import.meta.url
));

export interface EvaluationPredictor {
    predict(data: EvaluationCreateDTO): Promise<EvaluationPrediction>;
}

export class PythonEvaluationPredictor implements EvaluationPredictor {
    async predict(data: EvaluationCreateDTO): Promise<EvaluationPrediction> {
        const executable = process.env.PYTHON_EXECUTABLE
            || (existsSync(localPython) ? localPython : process.platform === "win32" ? "python" : "python3");
        const unavailable = () => new AppError("A avaliação está indisponível no momento. Tente novamente mais tarde.", 503);

        return new Promise((resolve, reject) => {
            const child = execFile(executable, ["-X", "utf8", "prever.py", "--json"], {
                cwd: modelDirectory,
                windowsHide: true,
                timeout: 30_000,
                maxBuffer: 1024 * 1024,
                env: { ...process.env, OMP_NUM_THREADS: "2", OPENBLAS_NUM_THREADS: "2", MKL_NUM_THREADS: "2" }
            }, (error, stdout) => {
                if (error) {
                    // Falha do processo ou modelo nunca deve produzir uma estimativa fictícia.
                    return reject(unavailable());
                }
                try {
                    const result = EvaluationPredictionSchema.safeParse(JSON.parse(stdout));
                    if (!result.success) return reject(unavailable());
                    resolve(result.data);
                } catch {
                    reject(unavailable());
                }
            });
            // O processo pode terminar antes de consumir a entrada.
            child.stdin?.on("error", () => {});
            child.stdin?.end(JSON.stringify({
                bairro: data.bairro, tipo: data.tipo, area_m2: data.areaM2,
                quartos: data.quartos, vagas: data.vagas,
                condominio: data.condominio, iptu: data.iptu, valor_anunciado: data.valorAnunciado
            }));
        });
    }
}
