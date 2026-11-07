// Lightbox for photo pages: click a photo to enlarge; arrows / swipe-free buttons to move; Esc to close.
(function () {
  var box = document.getElementById('lightbox');
  if (!box) return;
  var img = document.getElementById('lightbox-image');
  var count = document.getElementById('lightbox-count');
  var links = Array.prototype.slice.call(document.querySelectorAll('figure a'));
  var current = 0;

  function show(i) {
    current = (i + links.length) % links.length;
    var a = links[current], thumb = a.querySelector('img');
    img.src = a.href;
    img.alt = thumb ? thumb.alt : '';
    count.textContent = (current + 1) + ' / ' + links.length;
    box.classList.add('open');
  }
  function close() { box.classList.remove('open'); img.src = ''; }

  links.forEach(function (a, i) {
    a.addEventListener('click', function (e) { e.preventDefault(); show(i); });
  });
  document.getElementById('lightbox-close').addEventListener('click', close);
  document.getElementById('lightbox-prev').addEventListener('click', function (e) { e.stopPropagation(); show(current - 1); });
  document.getElementById('lightbox-next').addEventListener('click', function (e) { e.stopPropagation(); show(current + 1); });
  box.addEventListener('click', function (e) { if (e.target === box) close(); });
  document.addEventListener('keydown', function (e) {
    if (!box.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') show(current - 1);
    if (e.key === 'ArrowRight') show(current + 1);
  });
})();
