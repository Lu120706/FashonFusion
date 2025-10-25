// ===== Lógica del carrito =====
document.addEventListener('DOMContentLoaded', () => {
    const deleteButtons = document.querySelectorAll('.btn-danger');
  
    deleteButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        if (!confirm('¿Estás seguro de eliminar este producto del carrito?')) {
          e.preventDefault();
        }
      });
    });
  
    const checkoutForm = document.querySelector('.checkout-form');
    if (checkoutForm) {
      checkoutForm.addEventListener('submit', (e) => {
        const direccion = checkoutForm.querySelector('input[name="direccion_envio"]').value.trim();
        if (!direccion) {
          e.preventDefault();
          alert('Por favor ingresa una dirección de envío.');
        }
      });
    }
  });
  