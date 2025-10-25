document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("foto_producto");
  
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (file && file.size > 2 * 1024 * 1024) {
        alert("La imagen no debe superar los 2 MB.");
        fileInput.value = "";
      }
    });
  });
  