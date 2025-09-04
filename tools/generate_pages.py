#!/usr/bin/env python3
# coding: utf-8
"""
Генерим НЧ-страницы «Как зайти на … в России» из CSV.
Каждая страница получает уникальные блоки контента из таблицы.
- Вставляет Метрику
- Всегда ПЕРЕЗАПИСЫВАЕТ index.html (старые страницы можно не удалять вручную)
- Поля CSV см. в tools/pages.csv (ниже)

Запуск локально/в CI:
    python tools/generate_pages.py
"""

import csv, sys, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CSV  = REPO / "tools" / "pages.csv"

# ---------- Метрика
METRIKA = """<!-- Yandex.Metrika counter -->
<script type="text/javascript">
(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
m[i].l=1*new Date();for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=103602117', 'ym');
ym(103602117,'init',{ssr:true,webvisor:true,clickmap:true,ecommerce:"dataLayer",accurateTrackBounce:true,trackLinks:true});
</script><noscript><div><img src="https://mc.yandex.ru/watch/103602117" style="position:absolute; left:-9999px;" alt=""></div></noscript>
<!-- /Yandex.Metrika counter -->"""

# ---------- Стиль
STYLE = """
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css">
<style>
html{scroll-behavior:smooth}
:root{--primary:#2563eb;--secondary:#1e40af;--accent:#10b981;--danger:#ef4444;--card:#1e293b}
body{font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);color:#e2e8f0;line-height:1.6}
.nav{background:rgba(15,23,42,.95);backdrop-filter:blur(10px);border-bottom:1px solid #334155}
.card{background:var(--card);border:1px solid #334155;border-radius:14px}
.btn{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;padding:12px 18px;border-radius:12px;font-weight:800;display:inline-flex;gap:10px;align-items:center;text-decoration:none}
.btn-alt{background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff;padding:12px 18px;border-radius:12px;font-weight:800;display:inline-flex;gap:10px;align-items:center;text-decoration:none}
.badge{display:inline-block;background:#0ea5e9;color:#fff;padding:.15rem .5rem;border-radius:.5rem;font-size:.75rem;font-weight:700}
.hero{background:linear-gradient(135deg,#1e40af 0%, #3730a3 50%, #7c3aed 100%);position:relative;overflow:hidden}
.hero:before{content:'';position:absolute;inset:0;background:radial-gradient(900px 350px at 10% -10%, rgba(255,255,255,.08), transparent)}
ul li::marker{color:#60a5fa}
code{background:#0b1220;padding:.12rem .4rem;border-radius:.35rem}
</style>
"""

def _split(s: str):
    s = (s or "").strip()
    if not s: return []
    return [x.strip() for x in s.split("|") if x.strip()]

def render_list(items):
    if not items: return "<p class='text-gray-400'>—</p>"
    lis = "\n".join([f"<li>{i}</li>" for i in items])
    return f"<ul class='list-disc ml-5 space-y-1 text-gray-200'>\n{lis}\n</ul>"

def ensure_path(url: str) -> Path:
    url = url.strip()
    if not url.startswith("/"): url = "/" + url
    if not url.endswith("/"):  url = url + "/"
    return REPO / url.lstrip("/") / "index.html"

def page_html(row: dict) -> str:
    title       = row["title"].strip()
    desc        = row["description"].strip()
    h1          = row["h1"].strip()
    lead        = row["lead"].strip()
    service     = row["service"].strip()
    category    = row["category"].strip()
    country     = row["country_hint"].strip()
    problems    = render_list(_split(row["problems"]))
    fixes       = render_list(_split(row["fixes"]))
    errors      = render_list(_split(row["errors"]))
    faq1_q      = row["faq1_q"].strip()
    faq1_a      = row["faq1_a"].strip()
    faq2_q      = row["faq2_q"].strip()
    faq2_a      = row["faq2_a"].strip()
    extra_html  = (row.get("extra_html","") or "").replace("{","&#123;").replace("}","&#125;")
    noindex     = (row.get("noindex","no").strip().lower() in ("yes","true","1"))

    today = datetime.datetime.utcnow().strftime("%d.%m.%Y")
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""

    category_note = {
        "social":  "Соцсети часто режутся по IP и ASN провайдера. Нужен VPN с обфускацией.",
        "video":   "Видеосервисы помимо сайта блокируют CDN — DNS редко спасает, лучше VPN.",
        "games":   "Игровые сервисы чувствительны к задержке: берите ближайшие страны ЕС.",
        "work":    "Рабочие сервисы иногда блокируются по корпоративным политикам и IP-пулу.",
        "media":   "Музыка/стриминг фильтруется по гео. Без стабильного VPN часть треков недоступна.",
        "other":   "От провайдера к провайдеру фильтры разные — пробуйте несколько подходов."
    }.get(category or "other")

    return f"""<!DOCTYPE html><html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}
{STYLE}
{METRIKA}
</head><body>

<!-- NAV -->
<nav class="nav sticky top-0 z-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
    <a href="https://proxy-plus.github.io/" class="text-xl font-bold text-white flex items-center gap-2">
      <i class="fas fa-shield-alt text-blue-400"></i> Internet Security Hub
    </a>
    <div class="hidden md:flex items-center space-x-6">
      <a href="https://proxy-plus.github.io/guide/" class="text-gray-300 hover:text-white">Руководства</a>
      <a href="https://proxy-plus.github.io/devices/" class="text-gray-300 hover:text-white">Устройства</a>
      <a href="https://proxy-plus.github.io/streaming/" class="text-gray-300 hover:text-white">Стриминг</a>
      <a href="https://t.me/SafeNetVpn_bot?start=afrrica" class="btn-alt"><i class="fab fa-telegram"></i> Получить VPN</a>
    </div>
  </div>
</nav>

<!-- HERO -->
<section class="hero py-14">
  <div class="max-w-5xl mx-auto px-4 text-center relative z-10">
    <h1 class="text-4xl md:text-5xl font-extrabold text-white mb-3">{h1}</h1>
    <p class="text-blue-100 text-lg md:text-xl mb-6">{lead}</p>
    <div class="flex flex-col sm:flex-row gap-3 justify-center">
      <a href="https://t.me/SafeNetVpn_bot?start=afrrica" class="btn"><i class="fab fa-telegram"></i> Быстрое решение</a>
      <a href="#methods" class="btn-alt"><i class="fas fa-list"></i> Все способы</a>
    </div>
    <p class="text-blue-200 text-xs mt-4 opacity-80">Обновлено: {today}</p>
  </div>
</section>

<main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10" id="methods">

  <div class="card p-6 mb-8">
    <div class="badge mb-2">О сервисе</div>
    <p class="text-gray-200">{category_note}</p>
  </div>

  <div class="grid md:grid-cols-2 gap-6 mb-8">
    <div class="card p-6">
      <h2 class="text-2xl font-bold mb-2">Почему {service} не открывается в РФ</h2>
      {problems}
    </div>
    <div class="card p-6">
      <h2 class="text-2xl font-bold mb-2">Быстрые решения</h2>
      {fixes}
      <p class="text-gray-400 text-sm mt-3">Страна сервера: <b>{country}</b></p>
    </div>
  </div>

  <div class="card p-6 mb-8">
    <h2 class="text-2xl font-bold mb-2">Типичные ошибки</h2>
    {errors}
  </div>

  <div class="card p-6 mb-8">
    <h2 class="text-2xl font-bold mb-2">Рекомендуем</h2>
    <p class="mb-4">Проще всего включить готовый профиль VPN: европейский сервер + обфускация, чтобы {service} открылся без бубна.</p>
    <div class="flex flex-wrap gap-3">
      <a class="btn" href="https://t.me/SafeNetVpn_bot?start=afrrica"><i class="fab fa-telegram"></i> Подключить SAFENET-VPN</a>
      <a class="btn-alt" href="https://t.me/normwpn_bot?start=partner_228691787">Альтернативный VPN</a>
    </div>
  </div>

  {extra_html}

  <div class="grid md:grid-cols-2 gap-6">
    <div class="card p-6">
      <h3 class="text-xl font-bold mb-2">{faq1_q}</h3>
      <p class="text-gray-200">{faq1_a}</p>
    </div>
    <div class="card p-6">
      <h3 class="text-xl font-bold mb-2">{faq2_q}</h3>
      <p class="text-gray-200">{faq2_a}</p>
    </div>
  </div>

  <div class="mt-10 text-sm text-gray-400">
    *Материал образовательный. Соблюдайте законы вашей страны.
  </div>
</main>

<footer class="bg-slate-900 border-t border-slate-700 py-10 mt-10">
  <div class="max-w-7xl mx-auto px-4 text-center text-gray-400 text-sm">
    © 2025 Internet Security Hub • Гайды по обходу блокировок.
  </div>
</footer>

</body></html>"""

def main():
    if not CSV.exists():
        print(f"Нет файла: {CSV}", file=sys.stderr)
        sys.exit(1)

    created = 0
    with CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        need = {"url","title","description","h1","lead","service","category",
                "country_hint","problems","fixes","errors","faq1_q","faq1_a","faq2_q","faq2_a","extra_html","noindex"}
        if set(reader.fieldnames) != need:
            print("Нужно вот такое множество колонок:\n" + ", ".join(sorted(need)), file=sys.stderr)
            print("А сейчас: " + ", ".join(reader.fieldnames), file=sys.stderr)
            sys.exit(2)

        for row in reader:
            out = ensure_path(row["url"])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page_html(row), encoding="utf-8")
            created += 1
            print("[ok] ", str(out.relative_to(REPO)))

    print(f"\nГотово. Сгенерировано страниц: {created}")

if __name__ == "__main__":
    main()
