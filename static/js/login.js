const body = document.body;
const themeBtn = document.getElementById("themeBtn");
const toggleSenha = document.getElementById("toggleSenha");
const senha = document.getElementById("id_password");
const cardLogin = document.getElementById("cardLogin");

if (themeBtn) {
  themeBtn.addEventListener("click", () => {
    body.classList.toggle("light");
    const claro = body.classList.contains("light");
    themeBtn.textContent = claro ? "Dia" : "Noite";
    themeBtn.title = claro ? "Ativar modo escuro" : "Ativar modo claro";
  });
}

if (toggleSenha && senha) {
  toggleSenha.addEventListener("click", () => {
    const mostrando = senha.type === "text";
    senha.type = mostrando ? "password" : "text";
    toggleSenha.textContent = mostrando ? "Mostrar" : "Ocultar";
  });
}

if (cardLogin) {
  document.addEventListener("mousemove", (event) => {
    const x = (window.innerWidth / 2 - event.clientX) / 75;
    const y = (window.innerHeight / 2 - event.clientY) / 75;
    cardLogin.style.transform = `rotateY(${-x}deg) rotateX(${y}deg)`;
  });

  document.addEventListener("mouseleave", () => {
    cardLogin.style.transform = "rotateY(0deg) rotateX(0deg)";
  });
}
