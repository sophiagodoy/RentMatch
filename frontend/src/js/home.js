const avaliacoesHome = criarHistoricoAvaliacoes({ aoExcluir: carregarAvaliacoes });

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
