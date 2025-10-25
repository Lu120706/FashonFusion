document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("userForm");
  
    form.addEventListener("submit", (e) => {
      const password = form.password.value.trim();
  
      // Validación opcional: advertir si el campo de contraseña está vacío al crear un usuario nuevo
      if (!password && !form.id_usuario.readOnly) {
        alert("Por favor, ingresa una contraseña para el nuevo usuario.");
        e.preventDefault();
      }
    });
  });
  