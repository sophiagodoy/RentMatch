import "dotenv/config";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { once } from "node:events";
import { test } from "node:test";
import express from "express";
import { hash } from "bcryptjs";
import { prisma } from "../src/lib/prisma.js";
import { errorHandler } from "../src/middleware/ErrorHandler.js";
import { evaluationRoutes } from "../src/routes/EvaluationRoutes.js";
import { generateToken } from "../src/utils/TokenService.js";

test("Criação, consulta e salvamento de avaliações por usuário", { timeout: 60_000 }, async (t) => {
    const userId = randomUUID();
    const otherUserId = randomUUID();
    const app = express();
    app.use(express.json());
    app.use("/evaluations", evaluationRoutes);
    app.use(errorHandler);
    const server = app.listen(0, "127.0.0.1");

    t.after(async () => {
        try {
            await new Promise<void>((resolve, reject) => {
                server.close((error) => error ? reject(error) : resolve());
            });
        } finally {
            try {
                // A exclusão em cascata remove somente os dados criados neste teste.
                await prisma.user.deleteMany({ where: { id: { in: [userId, otherUserId] } } });
            } finally {
                await prisma.$disconnect();
            }
        }
    });

    await once(server, "listening");
    const address = server.address();
    assert(address && typeof address === "object");
    const baseUrl = `http://127.0.0.1:${address.port}`;
    const token = generateToken(userId);
    const otherToken = generateToken(otherUserId);

    async function request(path: string, method = "GET", authToken: string | null = token, body?: object) {
        const headers = new Headers();
        if (authToken !== null) headers.set("Authorization", `Bearer ${authToken}`);
        if (body !== undefined) headers.set("Content-Type", "application/json");
        return fetch(`${baseUrl}/evaluations${path}`, {
            method,
            headers,
            body: body === undefined ? undefined : JSON.stringify(body),
            signal: AbortSignal.timeout(method === "POST" ? 35_000 : 5_000)
        });
    }

    const password = await hash(randomUUID(), 4);
    await prisma.user.createMany({
        data: [userId, otherUserId].map((id) => ({
            id, name: "Teste de avaliações", email: `evaluations-${id}@example.invalid`, password
        }))
    });

    const fatores = [
        { descricao: "Localização", valor_informado: "Cambuí", contribuicao_reais: 150.2 },
        { fator: "Área", valor_informado: 65.5, contribuicao_reais: -50 }
    ];
    const createdAt = new Date("2026-11-01T12:00:00Z");
    const evaluationData = {
        userId, bairro: "Cambuí", tipo: "Apartamento", areaM2: 65.5, quartos: 2, vagas: 1,
        valorAnunciado: 1800.45, valorEstimado: 1650.25, condominio: null, iptu: 0,
        classificacao: "Caro", fatores, createdAt
    };
    // O padrão do banco precisa ser false, sem exigir que o criador informe saved.
    const evaluation = await prisma.evaluation.create({ data: evaluationData });
    assert.equal(evaluation.saved, false);
    const alreadySaved = await prisma.evaluation.create({
        data: { ...evaluationData, classificacao: "Oportunidade", fatores: [], saved: true }
    });
    const foreignEvaluation = await prisma.evaluation.create({
        data: { ...evaluationData, userId: otherUserId }
    });

    await t.test("POST, GET e PATCH exigem autenticação válida", async () => {
        for (const [method, path] of [["POST", ""], ["GET", `/${evaluation.id}`], ["PATCH", `/${evaluation.id}/save`]]) {
            for (const authToken of [null, "token-invalido"]) {
                const response = await request(path!, method, authToken);
                assert.equal(response.status, 401);
            }
        }
    });

    await t.test("IDs inválidos retornam 400 e IDs inexistentes retornam 404", async () => {
        for (const method of ["GET", "PATCH"]) {
            const suffix = method === "PATCH" ? "/save" : "";
            assert.equal((await request(`/id-invalido${suffix}`, method)).status, 400);
            const missing = await request(`/${randomUUID()}${suffix}`, method);
            assert.equal(missing.status, 404);
            assert.deepEqual(await missing.json(), { message: "Avaliação não encontrada" });
        }
    });

    await t.test("GET retorna o resultado completo e fatores sem salvar a avaliação", async () => {
        const response = await request(`/${evaluation.id}`);
        assert.equal(response.status, 200);
        assert.deepEqual(await response.json(), {
            id: evaluation.id, bairro: "Cambuí", tipo: "Apartamento", areaM2: 65.5,
            quartos: 2, vagas: 1, valorAnunciado: 1800.45, valorEstimado: 1650.25,
            condominio: null, iptu: 0, classificacao: "Caro", fatores,
            modelo: null, saved: false, createdAt: createdAt.toISOString()
        });
        const persisted = await prisma.evaluation.findUniqueOrThrow({ where: { id: evaluation.id } });
        assert.equal(persisted.saved, false);
        const noFactors = await (await request(`/${alreadySaved.id}`)).json();
        assert.deepEqual(noFactors.fatores, []);
    });

    await t.test("outra conta recebe 404 e não consegue salvar ou alterar o registro", async () => {
        for (const [method, path] of [["GET", `/${evaluation.id}`], ["PATCH", `/${evaluation.id}/save`]]) {
            const response = await request(path!, method, otherToken, method === "PATCH" ? { userId } : undefined);
            assert.equal(response.status, 404);
            assert.deepEqual(await response.json(), { message: "Avaliação não encontrada" });
        }
        const foreignResponse = await request(`/${foreignEvaluation.id}/save`, "PATCH");
        assert.equal(foreignResponse.status, 404);
        assert.equal((await prisma.evaluation.findUniqueOrThrow({ where: { id: evaluation.id } })).saved, false);
        assert.equal((await prisma.evaluation.findUniqueOrThrow({ where: { id: foreignEvaluation.id } })).saved, false);
    });

    await t.test("histórico e totais incluem somente as salvas do usuário", async () => {
        const response = await request("");
        assert.equal(response.status, 200);
        const history = await response.json();
        assert.deepEqual(history.data.map((item: { id: string }) => item.id), [alreadySaved.id]);
        assert.deepEqual(history.summary, { total: 1, caro: 0, precoJusto: 0, oportunidade: 1 });
        assert.equal(history.pagination.total, 1);
        assert.equal((await (await request("", "GET", otherToken)).json()).data.length, 0);
    });

    await t.test("PATCH persiste saved e ignora tentativas de alterar outros campos", async () => {
        const response = await request(`/${evaluation.id}/save`, "PATCH", token, {
            userId: otherUserId, valorEstimado: 1, classificacao: "Oportunidade", saved: false
        });
        assert.equal(response.status, 200);
        const result = await response.json();
        assert.equal(result.id, evaluation.id);
        assert.equal(result.saved, true);
        assert.equal(result.valorEstimado, 1650.25);
        assert.equal(result.classificacao, "Caro");
        assert.deepEqual(result.fatores, fatores);
        const persisted = await prisma.evaluation.findUniqueOrThrow({ where: { id: evaluation.id } });
        assert.equal(persisted.saved, true);
        assert.equal(persisted.userId, userId);
        assert.equal((await (await request(`/${evaluation.id}`)).json()).saved, true);
    });

    await t.test("salvar novamente é idempotente e atualiza histórico, totais e paginação", async () => {
        const response = await request(`/${evaluation.id}/save`, "PATCH");
        assert.equal(response.status, 200);
        assert.equal((await response.json()).saved, true);
        const history = await (await request("?limit=1&page=1")).json();
        assert.equal(history.data.length, 1);
        assert.deepEqual(history.summary, { total: 2, caro: 1, precoJusto: 0, oportunidade: 1 });
        assert.equal(history.pagination.totalPages, 2);
        assert.equal(history.pagination.hasNext, true);
        const all = await (await request("")).json();
        assert.deepEqual(new Set(all.data.map((item: { id: string }) => item.id)), new Set([evaluation.id, alreadySaved.id]));
        assert.equal(await prisma.evaluation.count({ where: { userId } }), 2);
    });

    await t.test("exclusão continua restrita ao dono e remove a avaliação salva", async () => {
        assert.equal((await request(`/${evaluation.id}`, "DELETE", otherToken)).status, 404);
        assert.equal((await request(`/${evaluation.id}`, "DELETE")).status, 204);
        assert.equal((await request(`/${evaluation.id}`)).status, 404);
        assert.equal((await request(`/${evaluation.id}/save`, "PATCH")).status, 404);
        assert.equal((await (await request("")).json()).summary.total, 1);
    });

    const input = {
        bairro: "Centro", tipo: "Apartamento", areaM2: 65, quartos: 2, vagas: 1,
        valorAnunciado: 1800.45, condominio: null, iptu: 0
    };

    await t.test("POST rejeita dados inválidos sem criar registros", async () => {
        const before = await prisma.evaluation.count({ where: { userId } });
        for (const invalid of [{}, { ...input, areaM2: 0 }, { ...input, quartos: 1.5 },
            { ...input, bairro: " " }, { ...input, condominio: -1 }, { ...input, valorAnunciado: "1800" },
            { ...input, valorAnunciado: 1.001 }]) {
            assert.equal((await request("", "POST", token, invalid)).status, 400);
        }
        assert.equal(await prisma.evaluation.count({ where: { userId } }), before);
    });

    await t.test("POST usa o modelo, protege o dono e só entra no histórico após salvar", async () => {
        const response = await request("", "POST", token, {
            ...input, userId: otherUserId, saved: true, valorEstimado: 1, fatores: [], classificacao: "Caro"
        });
        assert.equal(response.status, 201);
        const created = await response.json();
        assert.equal(created.saved, false);
        assert(created.valorEstimado > 1);
        assert.equal(created.valorAnunciado, 1800.45);
        assert.equal(created.condominio, null);
        assert.equal(created.iptu, 0);
        assert.equal(created.fatores.length, 4);
        assert(created.modelo.versao);
        assert.equal(created.modelo.intervaloEstimado.length, 2);
        const persisted = await prisma.evaluation.findUniqueOrThrow({ where: { id: created.id } });
        assert.equal(persisted.userId, userId);
        assert.deepEqual(persisted.fatores, created.fatores);
        assert.deepEqual(await (await request(`/${created.id}`)).json(), created);
        assert.equal((await request(`/${created.id}`, "GET", otherToken)).status, 404);
        assert.equal((await (await request("")).json()).summary.total, 1);
        assert.equal((await request(`/${created.id}/save`, "PATCH")).status, 200);
        const history = await (await request("")).json();
        assert(history.data.some((item: { id: string }) => item.id === created.id));
        assert.equal(history.summary.total, 2);
    });

    await t.test("falha do Python retorna 503 sem gravar uma avaliação fictícia", async () => {
        const previous = process.env.PYTHON_EXECUTABLE;
        const before = await prisma.evaluation.count({ where: { userId } });
        try {
            process.env.PYTHON_EXECUTABLE = "rentmatch-python-inexistente";
            assert.equal((await request("", "POST", token, input)).status, 503);
            assert.equal(await prisma.evaluation.count({ where: { userId } }), before);
        } finally {
            if (previous === undefined) delete process.env.PYTHON_EXECUTABLE;
            else process.env.PYTHON_EXECUTABLE = previous;
        }
    });
});
