# Ay Yıldız Ağız ve Diş Sağlığı Polikliniği – Web Sitesi

Statik, üç dilli (TR / EN / AR) ve SEO + yapay zeka araması için işaretlenmiş site.
Hiçbir sunucu tarafı kod gerektirmez; her statik hosting'e (cPanel, Netlify, Cloudflare Pages, GitHub Pages) yüklenebilir.

## Klasör yapısı

```
site/
├── index.html, hakkimizda/, tedaviler/, hekimler/, sikca-sorulan-sorular/, iletisim/   ← Türkçe (kök)
├── en/            ← İngilizce
├── ar/            ← Arapça (sağdan sola)
├── assets/        ← css, js, img (logo, hekim fotoğrafları, favicon, og görseli)
├── sitemap.xml, robots.txt, llms.txt, llms-full.txt, site.webmanifest, favicon.ico, 404.html
└── build/         ← ÜRETİM KAYNAĞI (hosting'e yüklenmesine gerek yok)
    ├── build.py              ← derleme betiği
    ├── site.json             ← telefon, adres, saatler, sosyal medya, koordinat
    ├── content/tr.json       ← tüm Türkçe metinler (ana kaynak)
    ├── content/en.json       ← İngilizce
    ├── content/ar.json       ← Arapça
    └── templates/            ← Jinja2 şablonları
```

## İçerik değiştirme

1. `build/content/tr.json` (veya en/ar) içindeki metni düzenleyin. Telefon, adres, saat gibi
   dil bağımsız bilgiler `build/site.json` dosyasındadır.
2. Siteyi yeniden derleyin (Python 3 + `pip install jinja2` gerekir):

```bash
python build/build.py
```

3. Yerelde görmek için:

```bash
python -m http.server 8765
```

ve tarayıcıda http://127.0.0.1:8765/ adresini açın.

## Yayına almadan önce tamamlanacaklar

- [ ] **Çalışma saatleri**: `build/site.json` → `hours` ve her dilin `common.hours_text` değeri.
      Şu an varsayılan olarak Pzt–Cum 09:00–19:00, Cmt 09:00–17:00 yazılıdır; doğrulayın.
- [ ] **Dt. Fatih Gülcü fotoğrafı ve özgeçmişi**: fotoğrafı `assets/img/fatih.jpg` ve `fatih.webp` olarak
      ekleyip `content/*.json` içinde `"has_photo": true` yapın; `about`, `education` alanlarını doldurun.
- [ ] **Klinik fotoğrafları**: ana sayfa hero alanında şu an logo kartı var; iç mekân fotoğrafı eklenebilir.
- [ ] **Google İşletme Profili**: adres, telefon ve çalışma saatleri siteyle birebir aynı olmalı
      (yerel SEO için en önemli adım). Haritadan alınan gerçek koordinatları `site.json` → `address.lat/lng` içine yazın.
- [ ] **Alan adı**: `build/site.json` → `domain` (şu an https://basaksehirdishekimi.com). Değişirse yeniden derleyin.
- [ ] **Google Search Console**: sitemap.xml'i gönderin. **Google Analytics** kullanılacaksa gtag kodunu
      `build/templates/base.html` head bölümüne ekleyin (main.js WhatsApp/telefon tıklamalarını otomatik olay olarak gönderir).
- [ ] **Instagram adresi**: şu an eski "hilalklinik" hesabı bağlı (`site.json` → `social`). Yeni hesap varsa güncelleyin.

## SEO ve yapay zeka uyumluluğu – nelere sahip?

- Her sayfada `Dentist` + `MedicalClinic` + `LocalBusiness` şeması (adres, saat, koordinat, diller, WhatsApp).
- Tedavi sayfalarında `MedicalWebPage` + `FAQPage`; SSS sayfasında tüm sorular `FAQPage`; hekim sayfalarında `Person/Dentist`.
- `BreadcrumbList`, `hreflang` (tr/en/ar/x-default), canonical, Open Graph.
- `llms.txt` ve `llms-full.txt`: ChatGPT, Claude, Perplexity gibi araçların kliniği doğru özetlemesi için.
- `robots.txt` yapay zeka tarayıcılarına (GPTBot, ClaudeBot, PerplexityBot…) açık.
- Anahtar kelime odağı: "Kayaşehir diş polikliniği", "Başakşehir diş hekimi", "Kayaşehir çocuk diş hekimi", tedavi adı + Kayaşehir.
