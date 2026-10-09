(() => {
  const css = `
    .top, .skip, .cta-row, .hero-note, .tune, #start > :not(.hero), footer { display: none !important; }
    .hero { height: 100vh !important; }
    .hero-inner { padding-top: 7vh !important; }
    .hero-copy { gap: 26px !important; max-width: 760px !important; }
    .hero h1 { font-size: 6.1rem !important; }
    .hero .lede { font-size: 1.95rem !important; max-width: 44rem !important; line-height: 1.42 !important; }
    .og-brand { display: flex; align-items: center; gap: 14px; font: 700 2rem/1 var(--font-display); color: var(--ink); }
    .og-brand svg { width: 40px; height: 40px; fill: var(--sun); }`;
  const style = document.createElement("style");
  style.textContent = css;
  document.head.append(style);
  const copy = document.querySelector(".hero-copy");
  const brand = document.createElement("p");
  brand.className = "og-brand";
  brand.innerHTML = document.querySelector(".brand-mark").outerHTML + "<span>Surya Saathi</span>";
  copy.prepend(brand);
  document.querySelector(".hero .lede").textContent = "Send a photo of your electricity bill on WhatsApp. Get the right solar size, your PM Surya Ghar subsidy, the EMI and the payback, in Hindi or English.";
  window.dispatchEvent(new Event("resize"));
})();
