document.addEventListener('click', (e) => {
  if (e.target.matches('.toggle')) {
    const btn = e.target;
    const header = btn.closest('.block-header');
    if (!header) return;
    const content = header.nextElementSibling;
    if (!content || !content.classList.contains('block-content')) return;
    content.classList.toggle('collapsed');
    btn.textContent = content.classList.contains('collapsed') ? '▶' : '▼';
    MathJax.typesetPromise();
  }
  const header = e.target.closest('.block-header');
  if (header) {
    const context_vars = header.nextElementSibling.innerHTML;
    const context_formulas = header.nextElementSibling.nextElementSibling.innerHTML;
    infoContent.innerHTML = `Clicked line: ${header.innerHTML}<br>context.vars: ${context_vars}<br>context.formulas: ${context_formulas}`;
    MathJax.typesetPromise();
  }
});
document.getElementById('expandAll').addEventListener('click', () => {
  document.querySelectorAll('.block-content').forEach(c => c.classList.remove('collapsed'));
  document.querySelectorAll('.toggle').forEach(b => b.textContent='▼');
  MathJax.typesetPromise();
});
document.getElementById('collapseAll').addEventListener('click', () => {
  document.querySelectorAll('.block-content').forEach(c => c.classList.add('collapsed'));
  document.querySelectorAll('.toggle').forEach(b => b.textContent='▶');
});
