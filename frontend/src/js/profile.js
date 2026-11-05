const formPerfil = document.querySelector("#form-perfil");
const formSenha = document.querySelector("#form-senha");
const camposPerfil = document.querySelector("#campos-perfil");
const camposSenha = document.querySelector("#campos-senha");
const nomePerfil = document.querySelector("#nome");
const novaSenha = document.querySelector("#nova-senha");
const confirmarNovaSenha = document.querySelector("#confirmar-nova-senha");
let resumoIniciado = false;

sessaoRentMatch.aoAtualizarUsuario((usuario) => {
    const nomes = usuario.name.trim().split(/\s+/);
    document.querySelector("#perfil-avatar").textContent =
        (nomes[0][0] + (nomes.length > 1 ? nomes[nomes.length - 1][0] : "")).toLocaleUpperCase("pt-BR");
    document.querySelector("#perfil-nome").textContent = usuario.name;
    document.querySelector("#perfil-email").textContent = usuario.email;
    document.querySelector("#perfil-desde").textContent =
        `Membro desde ${new Date(usuario.createdAt).toLocaleDateString("pt-BR", { month: "long", year: "numeric" })}`;
    nomePerfil.value = usuario.name;
    document.querySelector("#email").value = usuario.email;
    camposPerfil.disabled = false;
    camposSenha.disabled = false;
    if (!resumoIniciado) {
        resumoIniciado = true;
        carregarResumoPerfil();
    }
});

async function carregarResumoPerfil() {
    const aviso = document.querySelector("#mensagem-resumo-perfil");
    const botao = document.querySelector("#recarregar-resumo");
    botao.disabled = true;
    try {
        const resposta = await sessaoRentMatch.requisitar("/evaluations?limit=1");
        const dados = await sessaoRentMatch.lerDados(resposta, "Não foi possível carregar os totais.");
        document.querySelector("#perfil-total-avaliacoes").textContent = dados.summary.total;
        document.querySelector("#perfil-total-oportunidades").textContent = dados.summary.oportunidade;
        document.querySelector("#perfil-total-caros").textContent = dados.summary.caro;
        aviso.hidden = true;
    } catch (erro) {
        if (!erro.sessaoExpirada) aviso.hidden = false;
    } finally {
        botao.disabled = false;
    }
}

document.querySelector("#recarregar-resumo").addEventListener("click", carregarResumoPerfil);
nomePerfil.addEventListener("input", () => nomePerfil.setCustomValidity(""));

formPerfil.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    if (camposPerfil.disabled) return;
    nomePerfil.setCustomValidity(nomePerfil.value.trim().length < 2 ? "Informe seu nome com pelo menos 2 caracteres." : "");
    if (!formPerfil.reportValidity()) return;
    const mensagem = document.querySelector("#mensagem-perfil");
    const dados = { name: nomePerfil.value.trim(), email: document.querySelector("#email").value.trim() };
    camposPerfil.disabled = true;
    mensagem.textContent = "Salvando seus dados...";
    try {
        const resposta = await sessaoRentMatch.requisitar("/user/me", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        });
        const usuario = await sessaoRentMatch.lerDados(resposta, "Não foi possível salvar seus dados.");
        sessaoRentMatch.atualizarUsuario(usuario);
        mensagem.textContent = "Dados atualizados com sucesso.";
    } catch (erro) {
        if (!erro.sessaoExpirada) {
            mensagem.textContent = erro instanceof TypeError
                ? "Não foi possível conectar ao servidor. Tente novamente."
                : erro.message;
        }
    } finally {
        camposPerfil.disabled = false;
    }
});

function validarNovaSenha() {
    confirmarNovaSenha.setCustomValidity(
        confirmarNovaSenha.value && novaSenha.value !== confirmarNovaSenha.value
            ? "As senhas não conferem."
            : ""
    );
}

novaSenha.addEventListener("input", validarNovaSenha);
confirmarNovaSenha.addEventListener("input", validarNovaSenha);
formSenha.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    if (camposSenha.disabled) return;
    validarNovaSenha();
    if (!formSenha.reportValidity()) return;
    const dados = {
        currentPassword: document.querySelector("#senha-atual").value,
        newPassword: novaSenha.value,
        confirmNewPassword: confirmarNovaSenha.value
    };
    const mensagem = document.querySelector("#mensagem-senha");
    camposSenha.disabled = true;
    mensagem.textContent = "Alterando sua senha...";
    try {
        const resposta = await sessaoRentMatch.requisitar("/user/me/password", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        });
        await sessaoRentMatch.lerDados(resposta, "Não foi possível alterar sua senha.");
        formSenha.reset();
        mensagem.textContent = "Senha alterada com sucesso.";
    } catch (erro) {
        if (!erro.sessaoExpirada) {
            mensagem.textContent = erro instanceof TypeError
                ? "Não foi possível conectar ao servidor. Tente novamente."
                : erro.message;
        }
    } finally {
        camposSenha.disabled = false;
    }
});
