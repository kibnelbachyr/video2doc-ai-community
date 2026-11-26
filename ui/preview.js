/* Deliberately render model output as literal text, never executable HTML. */
"use strict";

const PREVIEW_LIMIT = 100000;

function renderMarkdownPreview(element, markdown) {
  const text = String(markdown);
  element.textContent = text.length > PREVIEW_LIMIT
    ? text.slice(0, PREVIEW_LIMIT) + "\n\n[Aperçu tronqué — téléchargez le Markdown complet.]"
    : text;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { renderMarkdownPreview, PREVIEW_LIMIT };
}
