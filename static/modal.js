/* Styled modal system — replaces browser prompt/alert/confirm */

function sfModal({ title, fields = [], confirmText = "Confirm", cancelText = "Cancel", isConfirm = false, message = "" }) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "sf-modal-overlay";

    const box = document.createElement("div");
    box.className = "sf-modal-box";

    let fieldsHtml = "";
    if (isConfirm) {
      fieldsHtml = `<p class="sf-modal-message">${message}</p>`;
    } else {
      fieldsHtml = fields.map(f => `
        <label class="sf-modal-label">${f.label}</label>
        <input type="${f.type || 'text'}" id="sf-field-${f.key}" value="${f.value ?? ''}" ${f.step ? `step="${f.step}"` : ''} class="sf-modal-input">
      `).join("");
    }

    box.innerHTML = `
      <h3 class="sf-modal-title">${title}</h3>
      ${fieldsHtml}
      <div class="sf-modal-actions">
        <button type="button" class="sf-modal-cancel">${cancelText}</button>
        <button type="button" class="sf-modal-confirm">${confirmText}</button>
      </div>
    `;

    overlay.appendChild(box);
    document.body.appendChild(overlay);

    const cleanup = (result) => {
      document.body.removeChild(overlay);
      resolve(result);
    };

    box.querySelector(".sf-modal-cancel").onclick = () => cleanup(null);
    overlay.onclick = (e) => { if (e.target === overlay) cleanup(null); };

    box.querySelector(".sf-modal-confirm").onclick = () => {
      if (isConfirm) {
        cleanup(true);
        return;
      }
      const result = {};
      fields.forEach(f => {
        const el = document.getElementById(`sf-field-${f.key}`);
        result[f.key] = f.type === "number" ? parseFloat(el.value) : el.value;
      });
      cleanup(result);
    };
  });
}

function sfConfirm(message) {
  return sfModal({ title: "Confirm", message, isConfirm: true, confirmText: "Yes", cancelText: "No" });
}

function sfAlert(message) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "sf-modal-overlay";
    const box = document.createElement("div");
    box.className = "sf-modal-box";
    box.innerHTML = `
      <p class="sf-modal-message">${message}</p>
      <div class="sf-modal-actions">
        <button type="button" class="sf-modal-confirm">OK</button>
      </div>
    `;
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    const close = () => { document.body.removeChild(overlay); resolve(); };
    box.querySelector(".sf-modal-confirm").onclick = close;
    overlay.onclick = (e) => { if (e.target === overlay) close(); };
  });
}
