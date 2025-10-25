// ===== JS de la página de factura =====
document.addEventListener('DOMContentLoaded', () => {
    const pdfBtn = document.querySelector('.btn-success');
  
    if (pdfBtn) {
      pdfBtn.addEventListener('click', () => {
        console.log('Descargando comprobante PDF...');
      });
    }
  
    // Mensaje de éxito opcional
    if (sessionStorage.getItem('factura_generada')) {
      alert('✅ Tu compra fue registrada correctamente. Se ha generado la factura.');
      sessionStorage.removeItem('factura_generada');
    }
  });
  