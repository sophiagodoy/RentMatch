const avaliacoesHome = criarHistoricoAvaliacoes({ aoExcluir: carregarAvaliacoes, aoSalvar: carregarAvaliacoes });
const formularioAvaliacao = document.querySelector("#form-avaliacao");
const mensagemAvaliacao = document.querySelector("#mensagem-avaliacao");
const reabrirResultado = document.querySelector("#ver-resultado");
let ultimoResultado = null;
let avaliando = false;

formularioAvaliacao.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    if (avaliando || !avaliacoesHome.autenticado) return;
    const numero = (id) => document.getElementById(id).valueAsNumber;
    const taxa = (id) => document.getElementById(id).value === "" ? null : numero(id);
    const dados = {
        bairro: document.querySelector("#bairro").value,
        tipo: document.querySelector("#tipo").value,
        areaM2: numero("metragem"), quartos: numero("quartos"), vagas: numero("vagas"),
        valorAnunciado: numero("valor-anunciado"), condominio: taxa("condominio"), iptu: taxa("iptu")
    };
    avaliando = true;
    formularioAvaliacao.setAttribute("aria-busy", "true");
    const controles = [...formularioAvaliacao.querySelectorAll("input, select, button")];
    controles.forEach((controle) => { controle.disabled = true; });
    const botao = document.querySelector("#criar-avaliacao");
    botao.textContent = "Calculando...";
    mensagemAvaliacao.textContent = "Calculando a estimativa e os fatores do imóvel...";
    try {
        const resposta = await sessaoRentMatch.requisitar("/evaluations", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados), signal: AbortSignal.timeout(40_000)
        });
        ultimoResultado = await sessaoRentMatch.lerDados(resposta, "Não foi possível avaliar o imóvel. Tente novamente.");
        mensagemAvaliacao.textContent = "Resultado pronto. Salve a avaliação para consultar depois no histórico.";
        reabrirResultado.hidden = false;
        avaliacoesHome.abrirDetalhes(ultimoResultado);
    } catch (erro) {
        if (!erro.sessaoExpirada) {
            mensagemAvaliacao.textContent = erro instanceof TypeError
                ? "Não foi possível conectar ao servidor. Seus dados foram mantidos; tente novamente."
                : erro.name === "TimeoutError"
                    ? "O cálculo demorou mais que o esperado. Tente novamente."
                    : erro.message;
        }
    } finally {
        avaliando = false;
        formularioAvaliacao.setAttribute("aria-busy", "false");
        controles.forEach((controle) => { controle.disabled = false; });
        botao.textContent = "Avaliar imóvel";
    }
});

reabrirResultado.addEventListener("click", () => {
    if (ultimoResultado) avaliacoesHome.abrirDetalhes(ultimoResultado);
});

async function carregarAvaliacoes() {
    const tabela = document.querySelector("#lista-avaliacoes");
    tabela.setAttribute("aria-busy", "true");
    avaliacoesHome.mostrarMensagem("Carregando avaliações...");
    try {
        const resposta = await avaliacoesHome.buscar(4);
        avaliacoesHome.atualizarResumo(resposta.summary);
        avaliacoesHome.renderizar(resposta.data);
    } catch (erro) {
        if (!erro.sessaoExpirada) {
            avaliacoesHome.mostrarMensagem(
                "Não foi possível carregar suas avaliações. Tente novamente.",
                carregarAvaliacoes
            );
        }
    } finally {
        tabela.setAttribute("aria-busy", "false");
    }
}

if (avaliacoesHome.autenticado) carregarAvaliacoes();
