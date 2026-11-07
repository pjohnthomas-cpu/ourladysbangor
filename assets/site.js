  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobile-nav');

  hamburger.addEventListener('click', function () {
    const isOpen = mobileNav.classList.toggle('open');
    hamburger.classList.toggle('open', isOpen);
    hamburger.setAttribute('aria-expanded', isOpen);
    mobileNav.setAttribute('aria-hidden', !isOpen);
  });

  function closeMenu() {
    mobileNav.classList.remove('open');
    hamburger.classList.remove('open');
    hamburger.setAttribute('aria-expanded', 'false');
    mobileNav.setAttribute('aria-hidden', 'true');
  }

  /* ── Announcement loader ── */
  fetch('announcement.json?t=' + Date.now())
    .then(function(r) { return r.json(); })
    .then(function(ann) {
      var section = document.getElementById('announcement-section');
      if (!section) return;
      if (ann.hidden) {
        section.hidden = true;
        return;
      }
      document.getElementById('announcement-title').textContent = ann.title;
      document.getElementById('announcement-body').innerHTML   = ann.body;
      section.hidden = false;
    })
    .catch(function() {
      /* If JSON fails to load, hide the section gracefully */
      var section = document.getElementById('announcement-section');
      if (section) section.hidden = true;
    });

  /* ── Lightbox Gallery ── */
  (function () {
    const gallery  = document.getElementById('gallery-thumbs');
    const overlay  = document.getElementById('lb-overlay');
    const lbImg    = document.getElementById('lb-img');
    const lbCap    = document.getElementById('lb-caption');
    const btnClose = document.getElementById('lb-close');
    const btnPrev  = document.getElementById('lb-prev');
    const btnNext  = document.getElementById('lb-next');

    const figures  = Array.from(gallery.querySelectorAll('figure'));
    let current    = 0;

    function open(index) {
      current = index;
      const fig = figures[current];
      lbImg.src = fig.querySelector('img').src;
      lbImg.alt = fig.querySelector('img').alt;
      lbCap.textContent = fig.dataset.caption || '';
      overlay.classList.add('active');
      btnPrev.style.display = figures.length < 2 ? 'none' : '';
      btnNext.style.display = figures.length < 2 ? 'none' : '';
      lbImg.focus();
    }

    function close() {
      overlay.classList.remove('active');
      lbImg.src = '';
    }

    function step(dir) {
      current = (current + dir + figures.length) % figures.length;
      const fig = figures[current];
      lbImg.src = fig.querySelector('img').src;
      lbImg.alt = fig.querySelector('img').alt;
      lbCap.textContent = fig.dataset.caption || '';
    }

    figures.forEach((fig, i) => {
      fig.addEventListener('click', () => open(i));
      fig.setAttribute('tabindex', '0');
      fig.addEventListener('keydown', e => { if (e.key === 'Enter') open(i); });
    });

    btnClose.addEventListener('click', close);
    btnPrev.addEventListener('click', () => step(-1));
    btnNext.addEventListener('click', () => step(1));

    overlay.addEventListener('click', e => { if (e.target === overlay) close(); });

    document.addEventListener('keydown', e => {
      if (!overlay.classList.contains('active')) return;
      if (e.key === 'Escape')     close();
      if (e.key === 'ArrowLeft')  step(-1);
      if (e.key === 'ArrowRight') step(1);
    });
  })();
