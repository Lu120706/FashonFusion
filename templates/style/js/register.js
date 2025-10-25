document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const password = document.getElementById("password");
    const confirm = document.getElementById("confirm_password");
  
    form.addEventListener("submit", (e) => {
      if (password.value !== confirm.value) {
        e.preventDefault();
        alert("⚠️ Las contraseñas no coinciden.");
      }
    });
  });
  