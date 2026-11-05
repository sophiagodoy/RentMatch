const sessaoRentMatch = (() => {
    const API_BASE_URL = window.location.port === "3000"
        ? window.location.origin
        : "http://localhost:3000";
    const ouvintes = new Set();
    let usuarioAtual = null;
    let carregamento = null;

    function autenticado() {
        return Boolean(localStorage.getItem("rentmatch_token"));
    }

    function sair() {
        localStorage.removeItem("rentmatch_token");
        window.location.replace("login.html");
    }

    function encerrarSessao() {
        sair();
        const erro = new Error("Sessão expirada. Entre novamente.");
        erro.sessaoExpirada = true;
        return erro;
    }

    async function requisitar(caminho, opcoes = {}) {
        const token = localStorage.getItem("rentmatch_token");
        if (!token) throw encerrarSessao();
        const headers = new Headers(opcoes.headers);
        headers.set("Authorization", `Bearer ${token}`);
        const resposta = await fetch(`${API_BASE_URL}${caminho}`, { ...opcoes, headers });
        if (resposta.status === 401) throw encerrarSessao();
        return resposta;
    }

    async function lerDados(resposta, mensagemPadrao) {
        if (resposta.status === 204) return null;
        const dados = await resposta.json();
        if (!resposta.ok) {
            const mensagem = Array.isArray(dados.errors) && dados.errors.length
                ? dados.errors.map((erro) => erro.message).join(" ")
                : dados.message || mensagemPadrao;
            throw new Error(mensagem);
        }
        return dados;
    }

    function atualizarUsuario(usuario) {
        usuarioAtual = usuario;
        const primeiroNome = usuario.name.trim().split(/\s+/)[0];
        document.querySelectorAll("[data-usuario-nome]").forEach((elemento) => {
            elemento.textContent = primeiroNome;
        });
        document.querySelectorAll("[data-usuario-saudacao]").forEach((elemento) => {
            elemento.textContent = `Olá, ${primeiroNome}!`;
        });
        ouvintes.forEach((ouvinte) => ouvinte(usuario));
    }

    function aoAtualizarUsuario(ouvinte) {
        ouvintes.add(ouvinte);
        if (usuarioAtual) ouvinte(usuarioAtual);
    }

    function carregarUsuario() {
        if (carregamento) return carregamento;
        const aviso = document.querySelector("#aviso-sessao");
        const repetir = document.querySelector("#recarregar-sessao");
        repetir.disabled = true;
        carregamento = (async () => {
            try {
                const resposta = await requisitar("/user/me");
                const usuario = await lerDados(resposta, "Não foi possível carregar sua conta.");
                atualizarUsuario(usuario);
                aviso.hidden = true;
                return usuario;
            } catch (erro) {
                if (!erro.sessaoExpirada) aviso.hidden = false;
                throw erro;
            } finally {
                repetir.disabled = false;
                carregamento = null;
            }
        })();
        return carregamento;
    }

    document.querySelector("#recarregar-sessao").addEventListener("click", () => {
        carregarUsuario().catch(() => {});
    });
    document.querySelectorAll("[data-sair]").forEach((elemento) => {
        elemento.addEventListener("click", (evento) => {
            evento.preventDefault();
            sair();
        });
    });
    window.addEventListener("storage", (evento) => {
        if (evento.key === "rentmatch_token" || evento.key === null) {
            if (autenticado()) window.location.reload();
            else sair();
        }
    });
    window.addEventListener("pageshow", (evento) => {
        if (evento.persisted) window.location.reload();
    });

    if (autenticado()) carregarUsuario().catch(() => {});
    else sair();

    return { autenticado, requisitar, lerDados, atualizarUsuario, aoAtualizarUsuario, sair };
})();
