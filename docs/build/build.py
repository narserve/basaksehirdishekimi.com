# -*- coding: utf-8 -*-
"""Static site generator for Ay Yıldız Ağız ve Diş Sağlığı Polikliniği.

Usage:  python build/build.py          (run from the site folder)
Output: index.html, /en/, /ar/, tedaviler/..., sitemap.xml, robots.txt, llms.txt
"""
import json, os, sys, shutil, datetime, re
from pathlib import Path
from urllib.parse import quote
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT = ROOT

site = json.loads((BUILD / "site.json").read_text(encoding="utf-8"))
contents = {}
for lang in site["languages"]:
    p = BUILD / "content" / f"{lang}.json"
    if p.exists():
        contents[lang] = json.loads(p.read_text(encoding="utf-8"))
langs = [l for l in site["languages"] if l in contents]
for _c in contents.values():
    for _t in _c["treatments"]:
        for _s in _t["sections"]:
            _s.setdefault("items", []); _s.setdefault("text", "")
lang_names = {l: contents[l]["lang_name"] for l in langs}

env = Environment(
    loader=FileSystemLoader(str(BUILD / "templates")),
    autoescape=select_autoescape(["html"]),
    trim_blocks=False, lstrip_blocks=False,
)
env.filters["urlencode"] = lambda s: quote(str(s), safe="")

BUILD_ID = datetime.datetime.now().strftime("%Y%m%d%H%M")
YEAR = datetime.date.today().year
TODAY = datetime.date.today().isoformat()

def wa_link(lang, text=None):
    c = contents[lang]
    msg = text or c["common"]["whatsapp_message"]
    return f"https://wa.me/{site['whatsapp']}?text={quote(msg, safe='')}"

# ---------- page registry (key -> lang -> url) ----------
def page_urls(lang):
    c = contents[lang]
    urls = {
        "home": c["paths"]["home"],
        "about": c["paths"]["about"],
        "treatments": c["paths"]["treatments"],
        "dentists": c["paths"]["dentists"],
        "faq": c["paths"]["faq"],
        "contact": c["paths"]["contact"],
    }
    for t in c["treatments"]:
        urls[f"treatment:{t['id']}"] = c["paths"]["treatments"] + t["slug"] + "/"
    for d in c["dentists"]:
        urls[f"dentist:{d['id']}"] = c["paths"]["dentists"] + d["slug"] + "/"
    return urls

registry = {}
for l in langs:
    for key, url in page_urls(l).items():
        registry.setdefault(key, {})[l] = url

def alternates(key):
    return {l: registry[key][l] for l in langs if l in registry.get(key, {})}

# ---------- JSON-LD ----------
def opening_hours():
    return [{
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": h["days"], "opens": h["open"], "closes": h["close"],
    } for h in site["hours"]]

def org_node(lang):
    c = contents[lang]
    return {
        "@type": ["Dentist", "MedicalClinic", "LocalBusiness"],
        "@id": site["domain"] + "/#clinic",
        "name": c["site"]["name"],
        "alternateName": [c["site"]["short_name"], "Başakşehir Kayaşehir Diş", "Kayaşehir Diş Polikliniği"],
        "url": site["domain"] + c["paths"]["home"],
        "logo": site["domain"] + "/assets/img/logo.png",
        "image": site["domain"] + "/assets/img/og-default.jpg",
        "telephone": site["phone_landline_tel"],
        "email": site["email"],
        "priceRange": "₺₺",
        "currenciesAccepted": "TRY",
        "paymentAccepted": "Cash, Credit Card",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": site["address"]["street"],
            "addressLocality": site["address"]["district"],
            "addressRegion": site["address"]["city"],
            "postalCode": site["address"]["postal"],
            "addressCountry": site["address"]["country"],
        },
        "geo": {"@type": "GeoCoordinates", "latitude": site["address"]["lat"], "longitude": site["address"]["lng"]},
        "hasMap": site["maps_url"],
        "openingHoursSpecification": opening_hours(),
        "areaServed": [
            {"@type": "Place", "name": "Kayaşehir"}, {"@type": "Place", "name": "Başakşehir"},
            {"@type": "Place", "name": "Kayabaşı"}, {"@type": "Place", "name": "Bahçeşehir"},
            {"@type": "City", "name": "İstanbul"},
        ],
        "availableLanguage": ["tr", "en", "ar"],
        "sameAs": [site["social"]["instagram"], site["social"]["facebook"]],
        "founder": {"@type": "Person", "name": site["founder"]},
        "medicalSpecialty": ["Dentistry", "Orthodontic", "PediatricDentistry", "Prosthodontics", "Endodontic", "Periodontics", "OralSurgery"],
        "contactPoint": [{
            "@type": "ContactPoint", "contactType": "appointments",
            "telephone": site["phone_mobile_tel"], "availableLanguage": ["Turkish", "English", "Arabic"],
            "url": wa_link(lang),
        }],
    }

def website_node(lang):
    c = contents[lang]
    return {
        "@type": "WebSite", "@id": site["domain"] + "/#website",
        "url": site["domain"] + "/", "name": c["site"]["name"], "inLanguage": langs,
        "publisher": {"@id": site["domain"] + "/#clinic"},
    }

def breadcrumb_node(items):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": it["name"], "item": site["domain"] + it["url"]}
            for i, it in enumerate(items)
        ],
    }

def faq_node(items):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
            for f in items
        ],
    }

def graph(lang, *nodes):
    return {"@context": "https://schema.org", "@graph": [org_node(lang), website_node(lang), *[n for n in nodes if n]]}

# ---------- helpers ----------
def norm(s):
    return re.sub(r"[^\w]+", " ", s.lower()).strip()

def find_featured_faq(c):
    pool = []
    for cat in c["faq"]["categories"]:
        pool.extend(cat["items"])
    for t in c["treatments"]:
        pool.extend(t["faq"])
    out = []
    for q in c["home"]["faq_section"]["featured"]:
        hit = next((f for f in pool if f["q"] == q), None)
        if not hit:
            key = " ".join(norm(q).split()[:3])
            hit = next((f for f in pool if norm(f["q"]).startswith(key)), None)
        if hit and hit not in out:
            out.append(hit)
    return out

def write(path_url, html):
    rel = path_url.lstrip("/")
    target = OUT / rel / "index.html" if path_url.endswith("/") else OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return target

def render(template, lang, page, **extra):
    c = contents[lang]
    tmpl = env.get_template(template)
    return tmpl.render(
        site=site, c=c, page=page, build_id=BUILD_ID, year=YEAR, lang_names=lang_names,
        wa_link=wa_link(lang), tmap={t["id"]: t for t in c["treatments"]},
        dmap={d["id"]: d for d in c["dentists"]}, **extra,
    )

sitemap_entries = []  # (key, lang, url, lastmod, priority)

def add_sitemap(key, lang, url, priority):
    sitemap_entries.append((key, lang, url, TODAY, priority))

# ---------- build ----------
for lang in langs:
    c = contents[lang]
    home_name = c["common"]["breadcrumb_home"]

    # Home
    key = "home"
    page = dict(kind="home", url=registry[key][lang], alternates=alternates(key),
                meta_title=c["home"]["meta_title"], meta_description=c["home"]["meta_description"])
    home_faq = find_featured_faq(c)
    page["jsonld"] = graph(lang, faq_node(home_faq) if home_faq else None)
    write(page["url"], render("home.html", lang, page, home_faq=home_faq))
    add_sitemap(key, lang, page["url"], "1.0")

    # About
    key = "about"
    bc = [{"name": home_name, "url": registry["home"][lang]}, {"name": c["about"]["title"], "url": registry[key][lang]}]
    page = dict(kind="about", url=registry[key][lang], alternates=alternates(key), breadcrumb=bc,
                meta_title=c["about"]["meta_title"], meta_description=c["about"]["meta_description"])
    page["jsonld"] = graph(lang, breadcrumb_node(bc), {"@type": "AboutPage", "name": c["about"]["title"], "url": site["domain"] + page["url"], "about": {"@id": site["domain"] + "/#clinic"}})
    write(page["url"], render("about.html", lang, page))
    add_sitemap(key, lang, page["url"], "0.7")

    # Treatments index
    key = "treatments"
    bc = [{"name": home_name, "url": registry["home"][lang]}, {"name": c["treatments_index"]["title"], "url": registry[key][lang]}]
    page = dict(kind="treatments", url=registry[key][lang], alternates=alternates(key), breadcrumb=bc,
                meta_title=c["treatments_index"]["meta_title"], meta_description=c["treatments_index"]["meta_description"])
    page["jsonld"] = graph(lang, breadcrumb_node(bc), {
        "@type": "ItemList", "name": c["treatments_index"]["title"],
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t["name"], "url": site["domain"] + registry[f"treatment:{t['id']}"][lang]} for i, t in enumerate(c["treatments"])],
    })
    write(page["url"], render("treatments.html", lang, page))
    add_sitemap(key, lang, page["url"], "0.9")

    # Treatment pages
    for t in c["treatments"]:
        key = f"treatment:{t['id']}"
        bc = [{"name": home_name, "url": registry["home"][lang]}, {"name": c["treatments_index"]["title"], "url": registry["treatments"][lang]}, {"name": t["name"], "url": registry[key][lang]}]
        page = dict(kind="treatment", url=registry[key][lang], alternates=alternates(key), breadcrumb=bc,
                    meta_title=t["meta_title"], meta_description=t["meta_description"])
        page["jsonld"] = graph(lang, breadcrumb_node(bc), faq_node(t["faq"]), {
            "@type": "MedicalWebPage", "name": t["h1"], "url": site["domain"] + page["url"], "inLanguage": lang,
            "description": t["meta_description"], "about": {"@type": "MedicalProcedure", "name": t["name"], "procedureType": "https://schema.org/NoninvasiveProcedure" if t["id"] in ("dis-beyazlatma", "ortodonti", "gulus-tasarimi") else "https://schema.org/SurgicalProcedure" if t["id"] in ("implant", "dis-cekimi") else "https://schema.org/TherapeuticProcedure"},
            "provider": {"@id": site["domain"] + "/#clinic"}, "lastReviewed": TODAY,
        })
        write(page["url"], render("treatment.html", lang, page, t=t))
        add_sitemap(key, lang, page["url"], "0.9")

    # Dentists index
    key = "dentists"
    bc = [{"name": home_name, "url": registry["home"][lang]}, {"name": c["dentists_index"]["title"], "url": registry[key][lang]}]
    page = dict(kind="dentists", url=registry[key][lang], alternates=alternates(key), breadcrumb=bc,
                meta_title=c["dentists_index"]["meta_title"], meta_description=c["dentists_index"]["meta_description"])
    page["jsonld"] = graph(lang, breadcrumb_node(bc))
    write(page["url"], render("dentists.html", lang, page))
    add_sitemap(key, lang, page["url"], "0.8")

    # Dentist pages
    for d in c["dentists"]:
        key = f"dentist:{d['id']}"
        bc = [{"name": home_name, "url": registry["home"][lang]}, {"name": c["dentists_index"]["title"], "url": registry["dentists"][lang]}, {"name": d["name"], "url": registry[key][lang]}]
        page = dict(kind="dentist", url=registry[key][lang], alternates=alternates(key), breadcrumb=bc,
                    meta_title=d["meta_title"], meta_description=d["meta_description"],
                    og_image=f"{d['photo']}.jpg" if d["has_photo"] else "og-default.jpg")
        person = {
            "@type": ["Person", "Dentist"], "name": d["name"], "jobTitle": d["title"], "description": d["summary"],
            "url": site["domain"] + page["url"], "worksFor": {"@id": site["domain"] + "/#clinic"},
            "knowsAbout": d["areas"], "knowsLanguage": d["languages"],
        }
        if d["has_photo"]:
            person["image"] = site["domain"] + f"/assets/img/{d['photo']}.jpg"
        if d["education"]:
            person["alumniOf"] = [{"@type": "EducationalOrganization", "name": e} for e in d["education"]]
        if d["memberships"]:
            person["memberOf"] = [{"@type": "Organization", "name": m} for m in d["memberships"]]
        page["jsonld"] = graph(lang, breadcrumb_node(bc), person)
        msg = c["common"]["whatsapp_message"] + f" ({d['name']})"
        write(page["url"], render("dentist.html", lang, page, d=d, wa_link_doctor=wa_link(lang, msg)))
        add_sitemap(key, lang, page["url"], "0.7")

    # FAQ
    key = "faq"
    bc = [{"name": home_name, "url": registry["home"][lang]}, {"name": c["faq"]["title"], "url": registry[key][lang]}]
    page = dict(kind="faq", url=registry[key][lang], alternates=alternates(key), breadcrumb=bc,
                meta_title=c["faq"]["meta_title"], meta_description=c["faq"]["meta_description"])
    all_items = [f for cat in c["faq"]["categories"] for f in cat["items"]]
    page["jsonld"] = graph(lang, breadcrumb_node(bc), faq_node(all_items))
    write(page["url"], render("faq.html", lang, page))
    add_sitemap(key, lang, page["url"], "0.9")

    # Contact
    key = "contact"
    bc = [{"name": home_name, "url": registry["home"][lang]}, {"name": c["contact"]["title"], "url": registry[key][lang]}]
    page = dict(kind="contact", url=registry[key][lang], alternates=alternates(key), breadcrumb=bc,
                meta_title=c["contact"]["meta_title"], meta_description=c["contact"]["meta_description"])
    page["jsonld"] = graph(lang, breadcrumb_node(bc), {"@type": "ContactPage", "name": c["contact"]["title"], "url": site["domain"] + page["url"]})
    write(page["url"], render("contact.html", lang, page))
    add_sitemap(key, lang, page["url"], "0.8")

    # 404 (one per language; root 404.html is Turkish)
    page = dict(kind="404", url=c["paths"]["home"] + "404.html", alternates=alternates("home"),
                meta_title=c["common"]["page_not_found"] + " | " + c["site"]["short_name"], meta_description=c["common"]["page_not_found_text"])
    page["jsonld"] = graph(lang)
    write(page["url"], render("404.html", lang, page))

# ---------- sitemap.xml with hreflang ----------
by_key = {}
for key, lang, url, lastmod, prio in sitemap_entries:
    by_key.setdefault(key, {})[lang] = (url, lastmod, prio)
lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for key, per in by_key.items():
    for lang, (url, lastmod, prio) in per.items():
        lines.append("  <url>")
        lines.append(f"    <loc>{site['domain']}{url}</loc>")
        for l2, (u2, _, _) in per.items():
            lines.append(f'    <xhtml:link rel="alternate" hreflang="{l2}" href="{site["domain"]}{u2}"/>')
        if "tr" in per:
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{site["domain"]}{per["tr"][0]}"/>')
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <priority>{prio}</priority>")
        lines.append("  </url>")
lines.append("</urlset>")
(OUT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")

# ---------- robots.txt ----------
(OUT / "robots.txt").write_text(
    "User-agent: *\nAllow: /\n\n"
    "# AI crawlers are welcome to index and cite this site\n"
    "User-agent: GPTBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: anthropic-ai\nAllow: /\n"
    "User-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\nUser-agent: Applebot-Extended\nAllow: /\n"
    "User-agent: Bytespider\nAllow: /\nUser-agent: CCBot\nAllow: /\n\n"
    f"Sitemap: {site['domain']}/sitemap.xml\n", encoding="utf-8")

# ---------- llms.txt ----------
tr = contents["tr"]
llm = [f"# {tr['site']['name']}", "",
       f"> {tr['site']['description']}", "",
       f"Adres: {site['address']['street']}, {site['address']['district']} / {site['address']['city']}. "
       f"Telefon: {site['phone_landline']} / {site['phone_mobile']} (WhatsApp). E-posta: {site['email']}. "
       f"Çalışma saatleri: {tr['common']['hours_text']}. Mesul müdür: {site['founder']}. İlk muayene ücretsizdir. "
       f"Hizmet dilleri: Türkçe, İngilizce, Arapça. Konum: Kayaşehir, Başakşehir, İstanbul (Kayaşehir Merkez metrosuna yakın).", ""]
for lang in langs:
    c = contents[lang]
    llm.append(f"## {c['lang_name']}")
    llm.append("")
    llm.append(f"- [{c['nav']['home']}]({site['domain']}{c['paths']['home']}): {c['home']['meta_description']}")
    llm.append(f"- [{c['nav']['about']}]({site['domain']}{c['paths']['about']}): {c['about']['meta_description']}")
    llm.append(f"- [{c['nav']['faq']}]({site['domain']}{c['paths']['faq']}): {c['faq']['meta_description']}")
    llm.append(f"- [{c['nav']['contact']}]({site['domain']}{c['paths']['contact']}): {c['contact']['meta_description']}")
    llm.append(f"- [{c['nav']['dentists']}]({site['domain']}{c['paths']['dentists']}): {c['dentists_index']['meta_description']}")
    for t in c["treatments"]:
        llm.append(f"- [{t['name']}]({site['domain']}{c['paths']['treatments']}{t['slug']}/): {t['short']}")
    for d in c["dentists"]:
        llm.append(f"- [{d['name']}]({site['domain']}{c['paths']['dentists']}{d['slug']}/): {d['title']} – {d['specialty']}")
    llm.append("")
(OUT / "llms.txt").write_text("\n".join(llm), encoding="utf-8")

# llms-full.txt: all Turkish Q&A in plain text for AI answer engines
full = [f"# {tr['site']['name']} – Soru-Cevap", ""]
for cat in tr["faq"]["categories"]:
    full.append(f"## {cat['name']}")
    for f in cat["items"]:
        full.append(f"S: {f['q']}")
        full.append(f"C: {f['a']}")
        full.append("")
for t in tr["treatments"]:
    full.append(f"## {t['name']}")
    full.append(t["intro"])
    for f in t["faq"]:
        full.append(f"S: {f['q']}")
        full.append(f"C: {f['a']}")
    full.append("")
(OUT / "llms-full.txt").write_text("\n".join(full), encoding="utf-8")

# ---------- web manifest ----------
(OUT / "site.webmanifest").write_text(json.dumps({
    "name": tr["site"]["name"], "short_name": tr["site"]["short_name"],
    "icons": [{"src": "/assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"}],
    "theme_color": site["colors"]["dark"], "background_color": "#FFFFFF", "display": "browser", "start_url": "/",
}, ensure_ascii=False, indent=2), encoding="utf-8")

# root 404.html = Turkish
print(f"Built {len(sitemap_entries)} pages for {', '.join(langs)} (build {BUILD_ID})")
