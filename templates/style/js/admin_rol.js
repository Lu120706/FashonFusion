document.addEventListener("DOMContentLoaded", function () {
    const modalRoleName = document.getElementById("modal-role-name");
    const modalRoleId = document.getElementById("modal-role-id");
    const deleteForm = document.getElementById("delete-form");
  
    document.querySelectorAll(".btn-eliminar").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.getAttribute("data-action");
        const nombre = btn.getAttribute("data-nombre");
        const id = btn.getAttribute("data-id");
  
        modalRoleName.textContent = nombre;
        modalRoleId.textContent = id;
        deleteForm.action = action;
      });
    });
  });
  