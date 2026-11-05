const API_BASE_URL = "http://localhost:3000";
const formLogin = document.querySelector("#form-login");
const mensagemLogin = document.querySelector("#mensagem-login");

formLogin.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    mensagemLogin.textContent = "Entrando...";

    try {
        const resposta = await fetch(`${API_BASE_URL}/user/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: document.querySelector("#email").value.trim(),
                password: document.querySelector("#senha").value
            })
        });
        const dados = await resposta.json();

        if (!resposta.ok) {
            throw new Error(dados.message || "Não foi possível entrar. Confira seus dados.");
        }

        localStorage.setItem("rentmatch_token", dados.token);
        window.location.href = "home.html";
    } catch (erro) {
        mensagemLogin.textContent = erro instanceof TypeError
            ? "Não foi possível conectar ao servidor. Verifique se o backend está rodando."
            : erro.message;
    }
});
