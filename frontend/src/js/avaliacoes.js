// Componentes compartilhados pela home e pelo histórico completo.
function criarHistoricoAvaliacoes({ aoExcluir, aoSalvar = async () => {} }) {
    const tabela = document.querySelector("#lista-avaliacoes");
    const modal = document.querySelector("#modal-avaliacao");
    const salvar = document.querySelector("#modal-salvar");
    const mensagemModal = document.querySelector("#modal-mensagem");
    let avaliacaoAberta = null;
    let salvando = false;

    if (!sessaoRentMatch.autenticado()) {
        return { autenticado: false };
    }

    async function buscar(limite) {
        const consulta = limite === undefined ? "" : `?limit=${limite}`;
        const resposta = await sessaoRentMatch.requisitar(`/evaluations${consulta}`);
        if (!resposta.ok) throw new Error("Não foi possível carregar suas avaliações. Tente novamente.");
        return resposta.json();
    }

    function mostrarMensagem(texto, tentarNovamente) {
        const linha = document.createElement("tr");
        const celula = document.createElement("td");
        celula.colSpan = 6;
        celula.className = "mensagem-avaliacoes";
        const mensagem = document.createElement("p");
        mensagem.textContent = texto;
        celula.append(mensagem);
        if (tentarNovamente) {
            const botao = document.createElement("button");
            botao.type = "button";
            botao.className = "link-secao botao-link-secao";
            botao.textContent = "Tentar novamente";
            botao.addEventListener("click", tentarNovamente);
            celula.append(botao);
        }
        linha.append(celula);
        tabela.replaceChildren(linha);
    }

    function atualizarResumo(resumo) {
        document.querySelector("#total-avaliacoes").textContent = resumo.total;
        document.querySelector("#total-oportunidades").textContent = resumo.oportunidade;
        document.querySelector("#total-preco-justo").textContent = resumo.precoJusto;
        document.querySelector("#total-caros").textContent = resumo.caro;
    }

    function formatarMoeda(valor) {
        if (valor == null) return "Não informado";
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

    function renderizar(avaliacoes, mensagemVazia = "Você ainda não tem avaliações salvas. Avalie um imóvel para começar.") {
        if (avaliacoes.length === 0) {
            mostrarMensagem(mensagemVazia);
            return;
        }
        tabela.replaceChildren();
        avaliacoes.forEach((avaliacao) => {
            const linha = document.createElement("tr");
            const imovel = document.createElement("td");
            const bairro = document.createElement("strong");
            bairro.textContent = avaliacao.bairro;
            const caracteristicas = document.createElement("small");
            caracteristicas.textContent = `${avaliacao.tipo} · ${avaliacao.quartos} quartos · ${avaliacao.areaM2} m²`;
            imovel.append(bairro, caracteristicas);

            const selo = document.createElement("span");
            selo.className = `selo ${classeClassificacao(avaliacao.classificacao)}`;
            selo.textContent = avaliacao.classificacao;
            const classificacao = document.createElement("td");
            classificacao.append(selo);

            linha.append(
                imovel,
                criarCelula(formatarMoeda(avaliacao.valorAnunciado)),
                criarCelula(formatarMoeda(avaliacao.valorEstimado)),
                classificacao,
                criarCelula(new Date(avaliacao.createdAt).toLocaleDateString("pt-BR"))
            );

            const detalhes = document.createElement("td");
            const botao = document.createElement("button");
            botao.className = "botao-detalhes";
            botao.type = "button";
            botao.title = "Ver detalhes";
            botao.setAttribute("aria-label", `Ver detalhes da avaliação em ${avaliacao.bairro}`);
            botao.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i>';
            botao.addEventListener("click", () => carregarDetalhes(avaliacao.id, botao));

            const excluir = document.createElement("button");
            excluir.className = "botao-excluir";
            excluir.type = "button";
            excluir.title = "Excluir avaliação";
            excluir.setAttribute("aria-label", `Excluir avaliação em ${avaliacao.bairro}`);
            excluir.innerHTML = '<i class="bi bi-trash3" aria-hidden="true"></i>';
            excluir.addEventListener("click", () => excluirAvaliacao(avaliacao, excluir));

            const acoes = document.createElement("div");
            acoes.className = "acoes-avaliacao";
            acoes.append(botao, excluir);
            detalhes.append(acoes);
            linha.append(detalhes);
            tabela.append(linha);
        });
    }

    async function excluirAvaliacao(avaliacao, botao) {
        if (!window.confirm(`Deseja excluir a avaliação do imóvel em ${avaliacao.bairro}?`)) return;
        botao.disabled = true;
        try {
            const resposta = await sessaoRentMatch.requisitar(`/evaluations/${encodeURIComponent(avaliacao.id)}`, {
                method: "DELETE"
            });
            if (!resposta.ok && resposta.status !== 404) {
                throw new Error("Não foi possível excluir a avaliação. Tente novamente.");
            }
            await aoExcluir();
        } catch (erro) {
            if (!erro.sessaoExpirada) window.alert(erro.message);
        } finally {
            botao.disabled = false;
        }
    }

    async function carregarDetalhes(id, botao) {
        if (botao.disabled) return;
        botao.disabled = true;
        botao.setAttribute("aria-busy", "true");
        try {
            const resposta = await sessaoRentMatch.requisitar(`/evaluations/${encodeURIComponent(id)}`);
            const avaliacao = await sessaoRentMatch.lerDados(
                resposta, "Não foi possível carregar os detalhes da avaliação. Tente novamente."
            );
            abrirDetalhes(avaliacao);
        } catch (erro) {
            if (!erro.sessaoExpirada) window.alert(erro.message);
        } finally {
            botao.disabled = false;
            botao.setAttribute("aria-busy", "false");
        }
    }

    function abrirDetalhes(avaliacao) {
        avaliacaoAberta = avaliacao;
        if (salvar) {
            salvar.hidden = avaliacao.saved;
            salvar.disabled = salvando;
            salvar.textContent = "Salvar no histórico";
        }
        if (mensagemModal) mensagemModal.textContent = "";
        document.querySelector("#modal-titulo").textContent = avaliacao.bairro;
        document.querySelector("#modal-resumo").textContent =
            `${avaliacao.tipo} · ${avaliacao.quartos} quartos · ${avaliacao.vagas} vagas · ${avaliacao.areaM2} m²`;
        document.querySelector("#modal-data").textContent =
            `Avaliação realizada em ${new Date(avaliacao.createdAt).toLocaleString("pt-BR")}`;
        document.querySelector("#modal-anunciado").textContent = formatarMoeda(avaliacao.valorAnunciado);
        document.querySelector("#modal-estimado").textContent = formatarMoeda(avaliacao.valorEstimado);
        const classificacao = document.querySelector("#modal-classificacao");
        classificacao.textContent = avaliacao.classificacao;
        classificacao.className = `selo ${classeClassificacao(avaliacao.classificacao)}`;
        document.querySelector("#modal-condominio").textContent = formatarMoeda(avaliacao.condominio);
        document.querySelector("#modal-iptu").textContent = formatarMoeda(avaliacao.iptu);

        const diferenca = Number(avaliacao.valorAnunciado) - Number(avaliacao.valorEstimado);
        document.querySelector("#modal-diferenca").textContent = diferenca === 0
            ? "O valor anunciado é igual ao estimado."
            : `${formatarMoeda(Math.abs(diferenca))} ${diferenca > 0 ? "acima" : "abaixo"} do valor estimado.`;

        const informacoes = document.querySelector("#modal-modelo");
        if (informacoes) {
            const modelo = avaliacao.modelo;
            const faixa = Array.isArray(modelo?.intervaloEstimado)
                ? `Faixa estimada: ${formatarMoeda(modelo.intervaloEstimado[0])} a ${formatarMoeda(modelo.intervaloEstimado[1])}. `
                : "";
            const avisos = Array.isArray(modelo?.avisos) ? modelo.avisos.filter((aviso) => typeof aviso === "string").join(" ") : "";
            informacoes.hidden = !modelo;
            informacoes.textContent = `${faixa}Estimativa baseada em anúncios de imóveis; os valores podem variar. ${avisos}`;
        }

        const lista = document.querySelector("#modal-lista-fatores");
        lista.replaceChildren();
        const fatores = Array.isArray(avaliacao.fatores)
            ? avaliacao.fatores.filter((fator) => fator && typeof fator === "object")
            : [];
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
            ? "Fatores registrados no momento da avaliação."
            : "Esta avaliação não possui fatores explicativos registrados.";
        modal.showModal();
    }

    salvar?.addEventListener("click", async () => {
        if (!avaliacaoAberta || avaliacaoAberta.saved || salvando) return;
        const avaliacao = avaliacaoAberta;
        salvando = true;
        salvar.disabled = true;
        salvar.textContent = "Salvando...";
        mensagemModal.textContent = "Salvando sua avaliação...";
        try {
            const resposta = await sessaoRentMatch.requisitar(`/evaluations/${encodeURIComponent(avaliacao.id)}/save`, {
                method: "PATCH"
            });
            const atualizada = await sessaoRentMatch.lerDados(resposta, "Não foi possível salvar a avaliação. Tente novamente.");
            Object.assign(avaliacao, atualizada);
            if (avaliacaoAberta === avaliacao) {
                salvar.hidden = true;
                mensagemModal.textContent = "Avaliação salva no seu histórico.";
            }
            await aoSalvar();
        } catch (erro) {
            if (!erro.sessaoExpirada && avaliacaoAberta === avaliacao) {
                mensagemModal.textContent = erro instanceof TypeError
                    ? "Não foi possível conectar ao servidor. Tente salvar novamente."
                    : erro.message;
            }
        } finally {
            salvando = false;
            salvar.disabled = false;
            salvar.textContent = "Salvar no histórico";
        }
    });

    document.querySelector(".modal-fechar").addEventListener("click", () => modal.close());
    modal.addEventListener("click", (evento) => {
        if (evento.target === modal) modal.close();
    });

    return { autenticado: true, buscar, mostrarMensagem, atualizarResumo, renderizar, abrirDetalhes };
}
