const API_BASE_URL = "http://localhost:3000";
const token = localStorage.getItem("rentmatch_token");
const tabelaAvaliacoes = document.querySelector("#lista-avaliacoes");
const botaoHistorico = document.querySelector("#alternar-historico");
const modal = document.querySelector("#modal-avaliacao");
let listaCompletaCarregada = false;

if (!token) {
    window.location.href = "login.html";
} else {
    carregarAvaliacoes(true);
}

async function buscarAvaliacoes(recentes = true) {
    const url = recentes
        ? `${API_BASE_URL}/evaluations?limit=4`
        : `${API_BASE_URL}/evaluations`;
    const resposta = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
    });

    if (resposta.status === 401) {
        localStorage.removeItem("rentmatch_token");
        window.location.href = "login.html";
        throw new Error("Sessão expirada. Entre novamente.");
    }
    if (!resposta.ok) throw new Error("Não foi possível carregar o histórico.");
    return resposta.json();
}

async function carregarAvaliacoes(recentes) {
    tabelaAvaliacoes.innerHTML = '<tr><td colspan="6">Carregando avaliações...</td></tr>';
    try {
        const resposta = await buscarAvaliacoes(recentes);
        atualizarResumo(resposta.summary);
        renderizarAvaliacoes(resposta.data);
        listaCompletaCarregada = !recentes;
        botaoHistorico.textContent = recentes ? "Ver todas" : "Mostrar recentes";
        botaoHistorico.setAttribute("aria-expanded", String(!recentes));
    } catch (erro) {
        if (erro.message !== "Sessão expirada. Entre novamente.") {
            tabelaAvaliacoes.innerHTML = "";
            const linha = document.createElement("tr");
            const celula = document.createElement("td");
            celula.colSpan = 6;
            celula.textContent = `${erro.message} Verifique se o backend está rodando.`;
            linha.append(celula);
            tabelaAvaliacoes.append(linha);
        }
    }
}

function atualizarResumo(resumo) {
    document.querySelector("#total-avaliacoes").textContent = resumo.total;
    document.querySelector("#total-oportunidades").textContent = resumo.oportunidade;
    document.querySelector("#total-preco-justo").textContent = resumo.precoJusto;
    document.querySelector("#total-caros").textContent = resumo.caro;
}

function formatarMoeda(valor) {
    return new Intl.NumberFormat("pt-BR", {
        style: "currency", currency: "BRL", maximumFractionDigits: 2
    }).format(valor);
}

function classeClassificacao(classificacao) {
    const normalizada = classificacao.toLocaleLowerCase("pt-BR");
    if (normalizada.includes("oportunidade")) return "selo-oportunidade";
    if (normalizada.includes("caro")) return "selo-caro";
    return "selo-justo";
}

function criarCelula(texto) {
    const celula = document.createElement("td");
    celula.textContent = texto;
    return celula;
}

function renderizarAvaliacoes(avaliacoes) {
    tabelaAvaliacoes.replaceChildren();
    if (avaliacoes.length === 0) {
        const linha = document.createElement("tr");
        const celula = document.createElement("td");
        celula.colSpan = 6;
        celula.textContent = "Você ainda não tem avaliações salvas.";
        linha.append(celula);
        tabelaAvaliacoes.append(linha);
        return;
    }

    avaliacoes.forEach((avaliacao) => {
        const linha = document.createElement("tr");
        const imovel = document.createElement("td");
        const tipo = document.createElement("strong");
        tipo.textContent = avaliacao.bairro;
        const caracteristicas = document.createElement("small");
        caracteristicas.textContent = `${avaliacao.tipo} · ${avaliacao.quartos} quartos · ${avaliacao.areaM2} m²`;
        imovel.append(tipo, caracteristicas);

        const selo = document.createElement("span");
        selo.className = `selo ${classeClassificacao(avaliacao.classificacao)}`;
        selo.textContent = avaliacao.classificacao;
        const classificacao = document.createElement("td");
        classificacao.append(selo);

        const data = new Date(avaliacao.createdAt).toLocaleDateString("pt-BR");
        linha.append(
            imovel,
            criarCelula(formatarMoeda(avaliacao.valorAnunciado)),
            criarCelula(formatarMoeda(avaliacao.valorEstimado)),
            classificacao,
            criarCelula(data)
        );

        const detalhes = document.createElement("td");
        const botao = document.createElement("button");
        botao.className = "botao-detalhes";
        botao.type = "button";
        botao.title = "Ver detalhes";
        botao.setAttribute("aria-label", `Ver detalhes da avaliação em ${avaliacao.bairro}`);
        botao.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i>';
        botao.addEventListener("click", () => abrirDetalhes(avaliacao));

        const excluir = document.createElement("button");
        excluir.className = "botao-excluir";
        excluir.type = "button";
        excluir.title = "Excluir avaliação";
        excluir.setAttribute("aria-label", `Excluir avaliação em ${avaliacao.bairro}`);
        excluir.innerHTML = '<i class="bi bi-trash3" aria-hidden="true"></i>';
        excluir.addEventListener("click", () => excluirAvaliacao(avaliacao.id, avaliacao.bairro, excluir));

        const acoes = document.createElement("div");
        acoes.className = "acoes-avaliacao";
        acoes.append(botao, excluir);
        detalhes.append(acoes);
        linha.append(detalhes);
        tabelaAvaliacoes.append(linha);
    });
}

async function excluirAvaliacao(id, bairro, botao) {
    const confirmar = window.confirm(`Deseja excluir a avaliação do imóvel em ${bairro}?`);
    if (!confirmar) return;

    botao.disabled = true;
    try {
        const resposta = await fetch(`${API_BASE_URL}/evaluations/${encodeURIComponent(id)}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` }
        });

        if (resposta.status === 401) {
            localStorage.removeItem("rentmatch_token");
            window.location.href = "login.html";
            return;
        }
        if (!resposta.ok && resposta.status !== 404) {
            throw new Error("Não foi possível excluir a avaliação.");
        }

        await carregarAvaliacoes(!listaCompletaCarregada);
    } catch (erro) {
        window.alert(erro.message);
        botao.disabled = false;
    }
}

function abrirDetalhes(avaliacao) {
    document.querySelector("#modal-titulo").textContent = avaliacao.bairro;
    document.querySelector("#modal-resumo").textContent =
        `${avaliacao.tipo} · ${avaliacao.quartos} quartos · ${avaliacao.vagas} vagas · ${avaliacao.areaM2} m²`;
    document.querySelector("#modal-anunciado").textContent = formatarMoeda(avaliacao.valorAnunciado);
    document.querySelector("#modal-estimado").textContent = formatarMoeda(avaliacao.valorEstimado);
    document.querySelector("#modal-classificacao").textContent = avaliacao.classificacao;

    const lista = document.querySelector("#modal-lista-fatores");
    lista.replaceChildren();
    const fatores = Array.isArray(avaliacao.fatores) ? avaliacao.fatores : [];
    fatores.forEach((fator) => {
        const item = document.createElement("li");
        item.className = "modal-fator";
        const texto = document.createElement("span");
        texto.className = "modal-fator-texto";
        const titulo = document.createElement("strong");
        titulo.textContent = fator.descricao || fator.fator || "Fator";
        const detalhe = document.createElement("small");
        detalhe.textContent = fator.valor_informado == null
            ? "Valor não informado"
            : `Valor informado: ${fator.valor_informado}`;
        texto.append(titulo, detalhe);

        const valor = Number(fator.contribuicao_reais || 0);
        const impacto = document.createElement("strong");
        impacto.className = valor >= 0 ? "fator-positivo" : "fator-negativo";
        impacto.textContent = `${valor > 0 ? "+" : valor < 0 ? "−" : ""} ${formatarMoeda(Math.abs(valor))}`;
        item.append(texto, impacto);
        lista.append(item);
    });
    document.querySelector("#modal-aviso").textContent = fatores.length
        ? "Fatores retornados pela avaliação salva."
        : "Esta avaliação não possui fatores explicativos registrados.";
    modal.showModal();
}

botaoHistorico.addEventListener("click", () => {
    // O estado atual indica qual lista está carregada; o clique alterna para a outra.
    carregarAvaliacoes(listaCompletaCarregada);
});
document.querySelector(".modal-fechar").addEventListener("click", () => modal.close());
modal.addEventListener("click", (evento) => {
    if (evento.target === modal) modal.close();
});
