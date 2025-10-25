document.addEventListener('DOMContentLoaded', () => {
    const section = document.getElementById('productReviewSection');
    if (!section) return;
    const pid = section.dataset.productId;
    const currentUser = (section.dataset.currentUser || '').trim();
    const form = document.getElementById('reviewForm');
    const reviewsList = document.getElementById('reviewsList');
    const avgText = document.getElementById('avgText');
    const idResenaInput = document.getElementById('id_resena');
    const submitBtn = document.getElementById('submitBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
  
    let reviewsCache = [];
  
    async function loadReviews(){
      try {
        const r = await fetch('/api/obtener_reseñas?id_producto=' + encodeURIComponent(pid));
        if (!r.ok) throw new Error('No se pudieron cargar reseñas');
        const data = await r.json();
        reviewsCache = data.reseñas || [];
        renderSummary(reviewsCache);
        renderList(reviewsCache);
        checkUserReview(reviewsCache);
      } catch(e){ 
        console.error(e);
        avgText.textContent = 'No se pudieron cargar las reseñas';
      }
    }
  
    function renderSummary(list){
      if (!list.length) {
        avgText.innerHTML = 'Sin reseñas aún';
        return;
      }
      const sumQuality = list.reduce((s, x) => s + (Number(x.calidad)||0), 0);
      const sumComfort = list.reduce((s, x) => s + (Number(x.comodidad)||0), 0);
      const avgQuality = (sumQuality / list.length);
      const avgComfort = (sumComfort / list.length);
      avgText.innerHTML = `
        <div><strong>${list.length}</strong> reseña(s)</div>
        <div>Calidad: ${avgQuality.toFixed(1)} · Comodidad: ${avgComfort.toFixed(1)}</div>
      `;
    }
  
    function renderList(list){
      reviewsList.innerHTML = '';
      if (!list.length) {
        reviewsList.innerHTML = '<p class="text-muted">Sé el primero en dejar una reseña.</p>';
        return;
      }
      list.forEach(r => {
        const div = document.createElement('div');
        div.className = 'single-review card p-2 mb-2';
        const userEsc = escapeHtml(r.id_usuario);
        const commentEsc = escapeHtml(r.comentario_resena || '');
        const foto = r.foto_url ? `<img src="${r.foto_url}" alt="foto" style="max-width:180px; display:block; margin-top:6px;">` : '';
        const isOwner = currentUser && (currentUser === r.id_usuario);
        div.innerHTML = `
          <div class="d-flex justify-content-between">
            <div><strong>${userEsc}</strong> <span class="meta">· ${r.creado_en}</span></div>
            ${isOwner ? '<div class="text-end"><small class="text-muted">Tu reseña</small></div>' : ''}
          </div>
          <div class="mt-1">Calidad: ${stars(r.calidad)} · Comodidad: ${stars(r.comodidad)}</div>
          <p class="mt-2 mb-0">${commentEsc}</p>
          ${foto}
          ${isOwner ? `<div class="actions"><button class="btn btn-sm btn-outline-primary me-2" data-action="edit" data-id="${r.id_resena}">Editar</button><button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${r.id_resena}">Eliminar</button></div>` : ''}
        `;
        reviewsList.appendChild(div);
      });
      reviewsList.querySelectorAll('button[data-action]').forEach(btn => {
        btn.addEventListener('click', handleActionClick);
      });
    }
  
    function checkUserReview(list){
      if (!currentUser) return;
      const mine = list.find(r => r.id_usuario === currentUser);
      const wrapper = document.getElementById('reviewFormWrapper');
      if (!wrapper) return;
      if (mine){
        wrapper.querySelectorAll('input,textarea,button').forEach(el => el.disabled = true);
        wrapper.style.opacity = '0.7';
        const note = document.createElement('div');
        note.className = 'alert alert-info mt-2';
        note.id = 'alreadyNote';
        note.innerHTML = `Ya dejaste una reseña para este producto. Usa <strong>Editar</strong> si quieres modificarla.`;
        wrapper.appendChild(note);
      } else {
        wrapper.querySelectorAll('input,textarea,button').forEach(el => el.disabled = false);
        wrapper.style.opacity = '1';
        const note = document.getElementById('alreadyNote');
        if (note) note.remove();
      }
    }
  
    function handleActionClick(e){
      const action = e.currentTarget.dataset.action;
      const id = e.currentTarget.dataset.id;
      if (action === 'edit') startEdit(id);
      else if (action === 'delete') confirmDelete(id);
    }
  
    function startEdit(id){
      const r = reviewsCache.find(x => String(x.id_resena) === String(id));
      if (!r) return alert('Reseña no encontrada');
      idResenaInput.value = r.id_resena;
      document.getElementById('comentario_resena').value = r.comentario_resena || '';
      const calidadRadio = document.querySelector(`input[name="calidad"][value="${r.calidad}"]`);
      const comodidadRadio = document.querySelector(`input[name="comodidad"][value="${r.comodidad}"]`);
      if (calidadRadio) calidadRadio.checked = true;
      if (comodidadRadio) comodidadRadio.checked = true;
      document.getElementById('formTitle').textContent = 'Editar reseña';
      submitBtn.textContent = 'Guardar cambios';
      cancelEditBtn.classList.remove('d-none');
      document.querySelectorAll('#reviewForm input, #reviewForm textarea, #reviewForm button').forEach(el => el.disabled = false);
      document.getElementById('reviewForm').scrollIntoView({behavior:'smooth', block:'center'});
    }
  
    cancelEditBtn && cancelEditBtn.addEventListener('click', () => {
      idResenaInput.value = '';
      document.getElementById('comentario_resena').value = '';
      document.querySelectorAll('input[name="calidad"], input[name="comodidad"]').forEach(i => i.checked = false);
      document.getElementById('formTitle').textContent = 'Deja una reseña';
      submitBtn.textContent = 'Enviar reseña';
      cancelEditBtn.classList.add('d-none');
    });
  
    async function confirmDelete(id){
      if (!confirm('¿Estás seguro de eliminar tu reseña?')) return;
      try {
        const resp = await fetch('/api/eliminar_reseña', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({id_resena: id})
        });
        const json = await resp.json();
        if (resp.ok && json.success) {
          alert('Reseña eliminada.');
          await loadReviews();
        } else alert('Error al eliminar: ' + (json.message || ''));
      } catch (err) {
        console.error(err);
        alert('Error en la petición de eliminación.');
      }
    }
  
    if (form){
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        if (!fd.get('calidad') || !fd.get('comodidad')) {
          alert('Por favor califica calidad y comodidad.');
          return;
        }
        const id_resena = fd.get('id_resena');
        const url = id_resena ? '/api/editar_reseña' : '/api/guardar_reseña';
        try {
          const resp = await fetch(url, { method: 'POST', body: fd });
          const json = await resp.json();
          if (resp.ok && json.success){
            await loadReviews();
            if (id_resena) cancelEditBtn.click();
            else form.reset();
            alert(json.message || 'Operación exitosa.');
          } else alert('Error: ' + (json.message || 'No se pudo completar.'));
        } catch (err) {
          console.error(err);
          alert('Error en la petición.');
        }
      });
    }
  
    function stars(n){ n = Number(n) || 0; return '★'.repeat(n) + '☆'.repeat(5-n); }
    function escapeHtml(t){ if (!t) return ''; return t.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  
    loadReviews();
  });
  