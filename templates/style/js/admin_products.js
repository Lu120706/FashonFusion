document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".btn-delete-product").forEach((btn) => {
      btn.addEventListener("click", (event) => {
        if (!confirm("¿Eliminar este producto?")) {
          event.preventDefault();
        }
      });
    });
  });
  