const API_BASE_URL = "http://localhost:3000";
const formCadastro = document.querySelector("#form-cadastro");
const mensagemCadastro = document.querySelector("#mensagem-cadastro");
const nomeCadastro = document.querySelector("#nome");
const senhaCadastro = document.querySelector("#senha");
const confirmarSenha = document.querySelector("#confirmar-senha");
const botaoCadastro = formCadastro.querySelector('button[type="submit"]');
let cadastroEmEnvio = false;

function validarSenhas() {
    confirmarSenha.setCustomValidity(
        confirmarSenha.value && senhaCadastro.value !== confirmarSenha.value
            ? "As senhas não conferem."
            : ""
    );
}

senhaCadastro.addEventListener("input", validarSenhas);
confirmarSenha.addEventListener("input", validarSenhas);
nomeCadastro.addEventListener("input", () => nomeCadastro.setCustomValidity(""));

formCadastro.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    if (cadastroEmEnvio) return;

    nomeCadastro.setCustomValidity(nomeCadastro.value.trim().length < 2 ? "Informe seu nome com pelo menos 2 caracteres." : "");
    validarSenhas();
    if (!formCadastro.reportValidity()) return;

    cadastroEmEnvio = true;
    botaoCadastro.disabled = true;
    botaoCadastro.textContent = "Cadastrando...";
    formCadastro.setAttribute("aria-busy", "true");
    mensagemCadastro.textContent = "Criando sua conta...";

    try {
        const resposta = await fetch(`${API_BASE_URL}/user/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: nomeCadastro.value.trim(),
                email: document.querySelector("#email").value.trim(),
                password: senhaCadastro.value
            })
        });
        const dados = await resposta.json();

        if (resposta.status === 409) {
            mensagemCadastro.textContent = "Já existe uma conta com este e-mail. Entre na sua conta ou use outro e-mail.";
            return;
        }
        if (!resposta.ok) {
            mensagemCadastro.textContent = Array.isArray(dados.errors) && dados.errors.length
                ? dados.errors.map((erro) => erro.message).join(" ")
                : dados.message || "Não foi possível criar sua conta. Tente novamente.";
            return;
        }

        mensagemCadastro.textContent = "Conta criada com sucesso! Abrindo o login...";
        window.location.href = "login.html?cadastro=sucesso";
    } catch (erro) {
        mensagemCadastro.textContent = erro instanceof TypeError
            ? "Não foi possível conectar ao servidor. Tente novamente em instantes."
            : "Não foi possível criar sua conta. Tente novamente.";
    } finally {
        cadastroEmEnvio = false;
        botaoCadastro.disabled = false;
        botaoCadastro.textContent = "Cadastrar";
        formCadastro.setAttribute("aria-busy", "false");
    }
});
