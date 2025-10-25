document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".delete-form").forEach(form => {
      form.addEventListener("submit", e => {
        const confirmed = confirm("¿Eliminar usuario?");
        if (!confirmed) e.preventDefault();
      });
    });
  });
  