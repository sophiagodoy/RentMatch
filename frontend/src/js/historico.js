const avaliacoesHistorico = criarHistoricoAvaliacoes({ aoExcluir: carregarHistorico });
const filtros = document.querySelector("#filtros-historico");
const busca = document.querySelector("#busca-historico");
const classificacao = document.querySelector("#classificacao-historico");
const ordenacao = document.querySelector("#ordenacao-historico");
const contagem = document.querySelector("#contagem-historico");
const paginacao = document.querySelector("#paginacao-historico");
const anterior = document.querySelector("#pagina-anterior");
const proxima = document.querySelector("#pagina-proxima");
const TAMANHO_PAGINA = 10;
let avaliacoesSalvas = [];
let paginaAtual = 1;

async function carregarHistorico() {
    const tabela = document.querySelector("#lista-avaliacoes");
    tabela.setAttribute("aria-busy", "true");
    filtros.disabled = true;
    paginacao.hidden = true;
    contagem.textContent = "Carregando seu histórico...";
    avaliacoesHistorico.mostrarMensagem("Carregando avaliações salvas...");
    try {
        // Sem limite, a API retorna todas as avaliações salvas do usuário.
        const resposta = await avaliacoesHistorico.buscar();
        avaliacoesSalvas = resposta.data;
        avaliacoesHistorico.atualizarResumo(resposta.summary);
        filtros.disabled = false;
        atualizarLista();
    } catch (erro) {
        if (!erro.sessaoExpirada) {
            contagem.textContent = "Seu histórico está indisponível no momento.";
            avaliacoesHistorico.mostrarMensagem(
                "Não foi possível carregar suas avaliações. Tente novamente.",
                carregarHistorico
            );
        }
    } finally {
        tabela.setAttribute("aria-busy", "false");
    }
}

function normalizar(texto) {
    return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
}

function atualizarLista() {
    const termo = normalizar(busca.value.trim());
    const categoria = normalizar(classificacao.value);
    const filtradas = avaliacoesSalvas.filter((avaliacao) =>
        normalizar(`${avaliacao.bairro} ${avaliacao.tipo}`).includes(termo)
        && (!categoria || normalizar(avaliacao.classificacao) === categoria)
    );
    const comparadores = {
        recentes: (a, b) => new Date(b.createdAt) - new Date(a.createdAt),
        antigas: (a, b) => new Date(a.createdAt) - new Date(b.createdAt),
        menorValor: (a, b) => Number(a.valorAnunciado) - Number(b.valorAnunciado),
        maiorValor: (a, b) => Number(b.valorAnunciado) - Number(a.valorAnunciado)
    };
    filtradas.sort(comparadores[ordenacao.value]);

    const totalPaginas = Math.max(1, Math.ceil(filtradas.length / TAMANHO_PAGINA));
    paginaAtual = Math.min(paginaAtual, totalPaginas);
    const inicio = (paginaAtual - 1) * TAMANHO_PAGINA;
    const fim = Math.min(inicio + TAMANHO_PAGINA, filtradas.length);
    avaliacoesHistorico.renderizar(
        filtradas.slice(inicio, fim),
        avaliacoesSalvas.length === 0
            ? "Você ainda não tem avaliações salvas. Avalie um imóvel para começar."
            : "Nenhuma avaliação corresponde à busca. Altere ou limpe os filtros."
    );
    const descricao = filtradas.length === 1 ? "avaliação" : "avaliações";
    contagem.textContent = filtradas.length === 0
        ? `0 avaliações encontradas · ${avaliacoesSalvas.length} salvas no total`
        : `Mostrando ${inicio + 1}–${fim} de ${filtradas.length} ${descricao}`
            + (filtradas.length !== avaliacoesSalvas.length ? ` · ${avaliacoesSalvas.length} salvas no total` : "");
    document.querySelector("#pagina-atual").textContent = `Página ${paginaAtual} de ${totalPaginas}`;
    anterior.disabled = paginaAtual === 1;
    proxima.disabled = paginaAtual === totalPaginas;
    paginacao.hidden = filtradas.length <= TAMANHO_PAGINA;
}

function filtrar() {
    paginaAtual = 1;
    atualizarLista();
}

document.querySelector("#form-filtros-historico").addEventListener("submit", (evento) => evento.preventDefault());
busca.addEventListener("input", filtrar);
classificacao.addEventListener("change", filtrar);
ordenacao.addEventListener("change", filtrar);
document.querySelector("#limpar-filtros").addEventListener("click", () => {
    busca.value = "";
    classificacao.value = "";
    ordenacao.value = "recentes";
    filtrar();
    busca.focus();
});
anterior.addEventListener("click", () => {
    paginaAtual -= 1;
    atualizarLista();
});
proxima.addEventListener("click", () => {
    paginaAtual += 1;
    atualizarLista();
});

if (avaliacoesHistorico.autenticado) carregarHistorico();
