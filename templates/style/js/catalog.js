// ===== JS del catálogo =====
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('.add-to-cart-form');
    
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        const talla = form.querySelector('select[name="talla"]').value;
        const color = form.querySelector('select[name="color"]').value;
  
        if (!talla || !color) {
          e.preventDefault();
          alert('Por favor selecciona una talla y un color antes de añadir al carrito.');
        }
      });
    });
  });
  