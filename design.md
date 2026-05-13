# ChiliScan — Design Specification Document

> Platform AI untuk Deteksi Penyakit Tanaman Cabai

**Versi:** 1.0.0
**Terakhir diperbarui:** Mei 2026
**Status:** Draft Desain

---

## Daftar Isi

1. [Identitas Brand](#1-identitas-brand)
2. [Design System](#2-design-system)
3. [Tipografi](#3-tipografi)
4. [Sistem Warna](#4-sistem-warna)
5. [Spacing & Layout](#5-spacing--layout)
6. [Komponen UI](#6-komponen-ui)
7. [Animasi (Framer Motion)](#7-animasi-framer-motion)
8. [Spesifikasi Halaman](#8-spesifikasi-halaman)
9. [Responsivitas](#9-responsivitas)
10. [Aksesibilitas](#10-aksesibilitas)
11. [Performa & Optimasi](#11-performa--optimasi)

---

## 1. Identitas Brand

### Nama & Konsep
- **Nama Produk:** ChiliScan
- **Tagline:** *"Kenali penyakit cabaimu, sebelum terlambat."*
- **Tone of Voice:** Profesional, tepercaya, informatif — namun tetap ramah bagi petani dan pengguna awam
- **Karakter Desain:** Clean & Professional — dominasi ruang putih, aksen hijau organik, tipografi tegas

### Logo Konsep
- Ikon: Stilasi daun cabai dengan elemen scan/garis digital
- Warna ikon: Gradien hijau `#2D7A3A` → `#52B069`
- Wordmark: Font heading bold, huruf kapital untuk "CHILI", reguler untuk "Scan"

---

## 2. Design System

### Prinsip Desain
1. **Clarity First** — Setiap elemen harus memiliki tujuan yang jelas, tidak ada dekorasi berlebihan
2. **Trust Through Consistency** — Warna, spasi, dan tipografi konsisten di semua halaman
3. **Progressive Disclosure** — Tampilkan informasi bertahap, jangan membanjiri pengguna sekaligus
4. **Natural Identity** — Aksen hijau memperkuat identitas pertanian/tanaman tanpa terasa kaku

---

## 3. Tipografi

### Font Pairing

| Peran | Font | Source | Alasan |
|---|---|---|---|
| **Heading / Display** | `DM Serif Display` | Google Fonts | Berkarakter elegan, tegas, cocok untuk judul ilmiah/profesional |
| **Body / UI** | `DM Sans` | Google Fonts | Bersih, sangat mudah dibaca, pasangan sempurna dengan DM Serif |

### Import Google Fonts

```html
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;400;500;600;700&display=swap" rel="stylesheet">
```

### Skala Tipografi

```css
/* Heading — DM Serif Display */
--font-heading: 'DM Serif Display', Georgia, serif;

/* Body & UI — DM Sans */
--font-body: 'DM Sans', system-ui, sans-serif;

/* Ukuran */
--text-xs:   0.75rem;    /* 12px — caption, label kecil */
--text-sm:   0.875rem;   /* 14px — label, helper text */
--text-base: 1rem;       /* 16px — body default */
--text-lg:   1.125rem;   /* 18px — body besar, subheading kecil */
--text-xl:   1.25rem;    /* 20px — subheading */
--text-2xl:  1.5rem;     /* 24px — H4 */
--text-3xl:  1.875rem;   /* 30px — H3 */
--text-4xl:  2.25rem;    /* 36px — H2 */
--text-5xl:  3rem;       /* 48px — H1 halaman */
--text-6xl:  3.75rem;    /* 60px — Hero display */
--text-7xl:  4.5rem;     /* 72px — Hero jumbo */
```

### Hierarki Teks

| Level | Font | Size | Weight | Line Height | Letter Spacing |
|---|---|---|---|---|---|
| H1 (Hero) | DM Serif Display | `--text-6xl` | 400 | 1.1 | -0.02em |
| H1 (Halaman) | DM Serif Display | `--text-5xl` | 400 | 1.15 | -0.01em |
| H2 | DM Serif Display | `--text-4xl` | 400 | 1.2 | 0 |
| H3 | DM Serif Display | `--text-3xl` | 400 | 1.25 | 0 |
| H4 | DM Sans | `--text-2xl` | 600 | 1.3 | 0 |
| Body Large | DM Sans | `--text-lg` | 400 | 1.7 | 0 |
| Body Base | DM Sans | `--text-base` | 400 | 1.6 | 0 |
| Body Small | DM Sans | `--text-sm` | 400 | 1.5 | 0 |
| Label | DM Sans | `--text-sm` | 500 | 1.4 | 0.02em |
| Caption | DM Sans | `--text-xs` | 400 | 1.4 | 0.01em |
| Button | DM Sans | `--text-sm` | 600 | 1 | 0.03em |

---

## 4. Sistem Warna

### Palet Utama

```css
:root {
  /* === PRIMARY — Hijau === */
  --green-50:  #F0FAF2;
  --green-100: #D9F2DF;
  --green-200: #B3E5C0;
  --green-300: #7FD09A;
  --green-400: #52B069;
  --green-500: #2D7A3A;   /* PRIMARY UTAMA */
  --green-600: #236130;
  --green-700: #1A4A24;
  --green-800: #123319;
  --green-900: #0A1E0F;

  /* === NEUTRAL — Abu & Putih === */
  --white:     #FFFFFF;
  --gray-50:   #F8F9F8;   /* Background halaman */
  --gray-100:  #F1F3F1;   /* Background card alt */
  --gray-200:  #E4E7E4;   /* Border default */
  --gray-300:  #C8CEC8;   /* Border aktif */
  --gray-400:  #9AA59A;   /* Placeholder text */
  --gray-500:  #6B776B;   /* Teks sekunder */
  --gray-600:  #4A534A;   /* Teks body */
  --gray-700:  #2E352E;   /* Teks primer */
  --gray-800:  #1A1F1A;   /* Teks heading */
  --gray-900:  #0D100D;   /* Teks display */

  /* === SEMANTIC === */
  --color-success:     #2D7A3A;
  --color-success-bg:  #F0FAF2;
  --color-warning:     #B45309;
  --color-warning-bg:  #FFFBEB;
  --color-danger:      #B91C1C;
  --color-danger-bg:   #FEF2F2;
  --color-info:        #1D4ED8;
  --color-info-bg:     #EFF6FF;

  /* === SURFACE === */
  --surface-base:      var(--white);
  --surface-raised:    var(--white);
  --surface-overlay:   var(--white);
  --surface-subtle:    var(--gray-50);
  --surface-muted:     var(--gray-100);

  /* === TEXT === */
  --text-primary:      var(--gray-800);
  --text-secondary:    var(--gray-600);
  --text-tertiary:     var(--gray-500);
  --text-disabled:     var(--gray-400);
  --text-inverse:      var(--white);
  --text-accent:       var(--green-500);

  /* === BORDER === */
  --border-default:    var(--gray-200);
  --border-strong:     var(--gray-300);
  --border-accent:     var(--green-400);

  /* === BRAND === */
  --brand-primary:     var(--green-500);
  --brand-hover:       var(--green-600);
  --brand-light:       var(--green-50);
  --brand-mid:         var(--green-100);
}
```

### Penggunaan Warna

| Elemen | Token |
|---|---|
| Background halaman | `--gray-50` |
| Background card | `--white` |
| Teks utama | `--gray-800` |
| Teks sekunder | `--gray-600` |
| Tombol primary | `--green-500` |
| Tombol hover | `--green-600` |
| Border input | `--gray-200` |
| Border input fokus | `--green-400` |
| Badge penyakit ringan | `--color-warning-bg` + `--color-warning` |
| Badge penyakit parah | `--color-danger-bg` + `--color-danger` |
| Badge sehat | `--color-success-bg` + `--color-success` |

---

## 5. Spacing & Layout

### Skala Spacing (Base: 4px)

```css
--space-0:   0px;
--space-1:   4px;
--space-2:   8px;
--space-3:   12px;
--space-4:   16px;
--space-5:   20px;
--space-6:   24px;
--space-8:   32px;
--space-10:  40px;
--space-12:  48px;
--space-16:  64px;
--space-20:  80px;
--space-24:  96px;
--space-32:  128px;
```

### Border Radius

```css
--radius-sm:   4px;     /* Input kecil, badge */
--radius-md:   8px;     /* Card kecil, button */
--radius-lg:   12px;    /* Card standar */
--radius-xl:   16px;    /* Modal, card besar */
--radius-2xl:  24px;    /* Card hero, container scan */
--radius-full: 9999px;  /* Pill, avatar */
```

### Shadow

```css
--shadow-xs:  0 1px 2px rgba(0,0,0,0.05);
--shadow-sm:  0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
--shadow-md:  0 4px 6px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04);
--shadow-lg:  0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.04);
--shadow-xl:  0 20px 25px rgba(0,0,0,0.08), 0 8px 10px rgba(0,0,0,0.04);
--shadow-green: 0 4px 14px rgba(45,122,58,0.2);  /* Untuk tombol primary */
```

### Grid System

```
Layout:        12 kolom
Max Width:     1280px
Gutter:        24px (desktop), 16px (tablet), 16px (mobile)
Margin:        auto (centered)
```

---

## 6. Komponen UI

### 6.1 Button

#### Varian

| Varian | Latar | Teks | Border | Gunakan untuk |
|---|---|---|---|---|
| **Primary** | `--green-500` | `white` | Tidak ada | Aksi utama (Scan, Login, Simpan) |
| **Secondary** | `white` | `--green-500` | `--green-400` | Aksi sekunder |
| **Ghost** | Transparan | `--gray-700` | `--gray-200` | Aksi tersier |
| **Danger** | `#B91C1C` | `white` | Tidak ada | Hapus, keluar |
| **Disabled** | `--gray-100` | `--gray-400` | Tidak ada | State tidak aktif |

#### Ukuran

| Size | Padding | Font Size | Height |
|---|---|---|---|
| **sm** | `8px 16px` | `--text-sm` | 36px |
| **md** | `10px 20px` | `--text-sm` | 40px |
| **lg** | `12px 24px` | `--text-base` | 48px |
| **xl** | `14px 32px` | `--text-lg` | 56px |

#### Spesifikasi

```
border-radius:    --radius-md
font-family:      --font-body
font-weight:      600
letter-spacing:   0.03em
transition:       all 150ms ease
hover transform:  translateY(-1px)
hover shadow:     --shadow-green (primary), --shadow-sm (lainnya)
active transform: translateY(0px)
```

---

### 6.2 Input Field

```
height:           44px (md), 40px (sm)
padding:          0 16px
border:           1.5px solid --border-default
border-radius:    --radius-md
font-family:      --font-body
font-size:        --text-base
color:            --text-primary
background:       --white
transition:       border-color 150ms ease, box-shadow 150ms ease

:focus
  border-color:   --green-400
  box-shadow:     0 0 0 3px rgba(45,122,58,0.12)
  outline:        none

:placeholder
  color:          --text-disabled

:error
  border-color:   --color-danger
  box-shadow:     0 0 0 3px rgba(185,28,28,0.10)
```

---

### 6.3 Card

#### Card Standar

```
background:     --white
border:         1px solid --border-default
border-radius:  --radius-lg
padding:        24px
box-shadow:     --shadow-sm
transition:     box-shadow 200ms ease, transform 200ms ease

:hover
  box-shadow:   --shadow-md
  transform:    translateY(-2px)
```

#### Card Hasil Scan

```
background:     --white
border:         1.5px solid --green-200
border-radius:  --radius-xl
padding:        32px
box-shadow:     0 4px 20px rgba(45,122,58,0.08)

Header:
  background:   --green-50
  border-radius: --radius-xl --radius-xl 0 0
  padding:      20px 32px
```

---

### 6.4 Navbar

```
height:           64px
background:       rgba(255,255,255,0.92)
backdrop-filter:  blur(12px)
border-bottom:    1px solid --gray-100
padding:          0 32px
position:         sticky, top: 0
z-index:          100

Logo:             kiri
Nav links:        tengah (desktop) / hamburger (mobile)
Auth actions:     kanan (Login / Avatar profil)

Nav link style:
  font:           --font-body, --text-sm, weight 500
  color:          --text-secondary
  :hover color:   --text-accent
  active:         --text-accent + border-bottom 2px --green-500
```

---

### 6.5 Avatar

```
Shape:          circle (--radius-full)
Sizes:          24px (xs), 32px (sm), 40px (md), 48px (lg), 64px (xl)
Fallback:       Inisial nama, background --green-100, teks --green-700
Border:         2px solid --white (when stacked)
```

---

### 6.6 Badge / Chip

| Tipe | Background | Teks | Ikon |
|---|---|---|---|
| Sehat | `--green-50` | `--green-700` | ✓ |
| Ringan | `#FFFBEB` | `#B45309` | ⚠ |
| Parah | `#FEF2F2` | `#B91C1C` | ✗ |
| Info | `#EFF6FF` | `#1D4ED8` | ℹ |

```
padding:        4px 10px
border-radius:  --radius-full
font-size:      --text-xs
font-weight:    600
letter-spacing: 0.04em
text-transform: uppercase
```

---

### 6.7 Scan Area (Kamera / Upload)

```
Container:
  border:         2px dashed --green-300
  border-radius:  --radius-2xl
  background:     --green-50
  min-height:     320px
  display:        flex, center, column
  transition:     all 250ms ease

:hover / drag-over:
  border-color:   --green-500
  background:     --green-100
  box-shadow:     0 0 0 4px rgba(45,122,58,0.08)

Live Camera View:
  border-radius:  --radius-2xl
  overflow:       hidden
  position:       relative
  scan-overlay:   SVG corner brackets, warna --green-400, animated pulse

Upload prompt:
  Ikon upload (32px, --green-400)
  Teks utama: "Seret foto ke sini"
  Teks sekunder: "atau klik untuk memilih file"
  Format info: "JPG, PNG, WEBP — Maks. 10MB"
```

---

### 6.8 Chat Bubble

```
User bubble:
  background:     --green-500
  color:          white
  border-radius:  --radius-lg --radius-lg 4px --radius-lg
  padding:        10px 16px
  align:          kanan
  max-width:      70%

AI bubble:
  background:     --gray-100
  color:          --text-primary
  border-radius:  --radius-lg --radius-lg --radius-lg 4px
  padding:        10px 16px
  align:          kiri
  max-width:      75%

Timestamp:
  font-size:      --text-xs
  color:          --text-tertiary
  margin-top:     4px

Typing indicator:
  3 dots animasi bounce, warna --green-400
```

---

### 6.9 Modal / Dialog

```
Overlay:        rgba(0,0,0,0.4), backdrop-filter blur(4px)
Container:
  background:   --white
  border-radius: --radius-xl
  padding:      32px
  max-width:    480px (sm), 640px (md), 800px (lg)
  box-shadow:   --shadow-xl

Header:
  H3, --font-heading
  Close button: kanan atas, ghost, icon X

Footer:
  border-top:   1px solid --border-default
  padding-top:  24px
  gap:          12px
  justify:      kanan
```

---

### 6.10 Skeleton Loading

```
background:     linear-gradient(90deg, --gray-100 25%, --gray-200 50%, --gray-100 75%)
background-size: 200% 100%
animation:      shimmer 1.5s infinite
border-radius:  --radius-md (teks), --radius-lg (card), --radius-full (avatar)
```

---

## 7. Animasi (Framer Motion)

### 7.1 Konfigurasi Dasar

```ts
// Durasi standar
export const DURATION = {
  fast:   0.15,
  normal: 0.25,
  slow:   0.4,
  slower: 0.6,
}

// Easing standar
export const EASE = {
  default:   [0.4, 0, 0.2, 1],   // Material standard
  enter:     [0, 0, 0.2, 1],      // Masuk (decelerate)
  exit:      [0.4, 0, 1, 1],      // Keluar (accelerate)
  spring:    { type: 'spring', stiffness: 350, damping: 30 },
  softSpring:{ type: 'spring', stiffness: 200, damping: 25 },
}
```

---

### 7.2 Page Transitions

```ts
// Transisi antar halaman
export const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: DURATION.slow, ease: EASE.enter } },
  exit:    { opacity: 0, y: -8, transition: { duration: DURATION.normal, ease: EASE.exit } },
}
// Implementasi: <AnimatePresence mode="wait"> + <motion.div variants={pageVariants}>
```

---

### 7.3 Entrance Animations

```ts
// Fade up — untuk card, section
export const fadeUp = {
  hidden:  { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: DURATION.slow, ease: EASE.enter } },
}

// Stagger container — untuk list item
export const staggerContainer = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
}

// Scale in — untuk modal, popup
export const scaleIn = {
  hidden:  { opacity: 0, scale: 0.94 },
  visible: { opacity: 1, scale: 1, transition: EASE.spring },
  exit:    { opacity: 0, scale: 0.96, transition: { duration: DURATION.fast } },
}

// Slide in right — untuk panel chat
export const slideInRight = {
  hidden:  { opacity: 0, x: 40 },
  visible: { opacity: 1, x: 0, transition: { duration: DURATION.slow, ease: EASE.enter } },
  exit:    { opacity: 0, x: 40, transition: { duration: DURATION.normal } },
}
```

---

### 7.4 Animasi per Komponen

| Komponen | Animasi | Detail |
|---|---|---|
| **Navbar** | Fade down saat scroll ke atas | opacity + translateY(-100%) saat scroll turun |
| **Hero Section** | Stagger fade up | H1 → tagline → CTA, delay 0.1s tiap elemen |
| **Card (grid)** | Stagger fade up | `staggerContainer` + `fadeUp`, trigger saat masuk viewport |
| **Scan Area** | Scale bounce saat hover | `whileHover: { scale: 1.01 }` dengan `EASE.spring` |
| **Kamera aktif** | Pulse ring hijau | CSS keyframe `pulse`, ring `--green-300`, 2s infinite |
| **Upload drag** | Border glow + scale | `whileDrag: { scale: 1.02, borderColor: green-500 }` |
| **Hasil Scan** | Reveal bertahap | Score counter animasi (0 → nilai), section fade stagger |
| **Progress Bar** | Slide in kiri ke kanan | `scaleX: 0 → 1`, `originX: 0`, duration 0.8s |
| **Chat bubble** | Slide + fade | User: dari kanan; AI: dari kiri |
| **Typing indicator** | Bounce stagger | 3 dots, `y: [0, -6, 0]`, stagger 0.15s |
| **Button** | Lift + shadow | `whileHover: { y: -2 }`, `whileTap: { y: 0, scale: 0.98 }` |
| **Modal** | Scale in + overlay fade | `scaleIn` + overlay `opacity: 0 → 1` |
| **Toast notif** | Slide dari bawah-kanan | `y: 100 → 0`, auto dismiss 4s |
| **Avatar dropdown** | Scale + fade | `scale: 0.9 → 1`, `originY: 0` (dari atas) |
| **Tab indicator** | Layout animation | `layoutId="tab-indicator"` untuk smooth slide |
| **Page transition** | Fade + slide up | `pageVariants`, `AnimatePresence mode="wait"` |

---

### 7.5 Prinsip Performa Animasi

- Gunakan **hanya** properti `transform` dan `opacity` → tidak memicu reflow
- Aktifkan `will-change: transform` hanya pada elemen yang benar-benar butuh
- Gunakan `useReducedMotion()` untuk menghormati preferensi aksesibilitas pengguna
- Animasi scroll (`whileInView`) gunakan `once: true` agar tidak berulang
- Hindari animasi simultan lebih dari 5 elemen sekaligus

```ts
// Contoh penggunaan useReducedMotion
const prefersReduced = useReducedMotion()
const variants = prefersReduced ? {} : fadeUp
```

---

## 8. Spesifikasi Halaman

### 8.1 Landing Page (Belum Login)

**Tujuan:** Meyakinkan pengguna bahwa ChiliScan adalah solusi terpercaya

**Struktur:**

```
[Navbar]
  Logo | Nav: Fitur, Cara Kerja, Tentang | CTA: Login / Daftar

[Hero Section]
  Kiri: Badge "Didukung AI" | H1: "Deteksi Penyakit Cabai Lebih Cepat & Akurat" 
        Tagline | Tombol: "Mulai Scan Gratis" + "Lihat Demo"
  Kanan: Mockup app / ilustrasi daun cabai dengan efek scan

[Feature Strip]
  3 ikon + teks singkat: Scan Instan | Diagnosa AI | Rekomendasi Ahli

[Cara Kerja — Steps]
  Step 1: Foto tanaman → Step 2: AI analisis → Step 3: Lihat hasil & tindakan
  Visual: Ilustrasi sederhana tiap step, koneksi dengan garis putus-putus

[Penyakit yang Dapat Dideteksi]
  Grid card: Antraknosa, Layu Fusarium, Virus Kuning, Bercak Daun, dll.
  Tiap card: Gambar contoh + nama + tingkat keparahan badge

[Statistik]
  3 angka: Pengguna Aktif | Penyakit Terdeteksi | Akurasi Model
  Animasi counter saat masuk viewport

[Testimoni]
  3 kartu kutipan dari petani / pengguna (avatar + nama + lokasi)

[CTA Bottom]
  Background: --green-500
  Teks putih: "Siap lindungi kebun cabaimu?" + tombol putih

[Footer]
  Logo | Navigasi | Media sosial | Copyright
```

**Animasi Landing Page:**
- Hero: Stagger entrance H1 → tagline → CTA → ilustrasi
- Steps: Scroll-triggered fade up tiap step
- Statistik: Count-up animation saat masuk viewport
- Penyakit cards: Stagger grid reveal

---

### 8.2 Halaman Login / Register

**Layout:** Split screen — kiri visual, kanan form

```
[Kiri — Dekoratif]
  Background: --green-500
  Ilustrasi: Daun cabai / tanaman
  Quote/testimonial singkat
  Logo ChiliScan besar (putih)

[Kanan — Form]
  Background: --white
  Padding: 48px

  TAB: "Masuk" | "Daftar"
  (Tab indicator dengan Framer Motion layoutId)

  === MASUK ===
  Google SSO Button (ikon Google + "Lanjutkan dengan Google")
  Divider: "atau dengan email"
  Input: Email
  Input: Password (eye toggle)
  Link: "Lupa password?"
  Tombol: "Masuk" (primary, full width)

  === DAFTAR ===
  Google SSO Button
  Divider
  Input: Nama Lengkap
  Input: Email
  Input: Buat Password (strength indicator)
  Input: Konfirmasi Password
  Checkbox: Setuju syarat & ketentuan
  Tombol: "Buat Akun" (primary, full width)

  Note: Jika daftar via Google SSO → modal popup wajib buat password
```

**Modal Buat Password (SSO):**
```
Judul: "Satu langkah lagi"
Subjudul: "Buat password untuk keamanan akun kamu"
Input: Buat Password + Konfirmasi
Strength indicator: Lemah / Sedang / Kuat
Tombol: "Selesai & Masuk"
```

---

### 8.3 Dashboard Utama

**Tujuan:** Hub navigasi, tampilkan aktivitas terkini

```
[Navbar] — Sticky

[Greeting Section]
  "Halo, [Nama]! 👋"
  Tanggal hari ini
  Tombol besar: "Scan Baru" (CTA utama)

[Quick Stats — 3 Card Kecil]
  Total Scan | Scan Bulan Ini | Penyakit Ditemukan

[Scan Terbaru]
  Grid 3 kolom: Card preview hasil scan (foto thumbnail + nama penyakit + tanggal + badge)
  Link "Lihat semua riwayat →"

[Chat Terbaru]
  List 3 percakapan terbaru: Ikon chat + judul topik + tanggal
  Link "Lihat semua chat →"

[Tips Hari Ini]
  Card banner dengan background --green-50:
  "Tahukah kamu?" + konten tips perawatan cabai
```

---

### 8.4 Halaman Scan

**Tujuan:** Area utama untuk foto/upload tanaman

```
[Header]
  Judul: "Scan Tanaman Cabai"
  Subjudul: "Arahkan kamera ke daun atau buah yang terlihat sakit"

[Tab Switch — Kamera / Upload]
  Framer Motion layoutId tab indicator

[=== MODE KAMERA ===]
  Viewport kamera (fullwidth, rasio 4:3 atau 16:9)
  Overlay: 4 sudut bracket hijau (animasi pulse)
  Tips kecil: "Pastikan pencahayaan cukup"
  Tombol capture: Bulat besar (64px), ikon kamera, --green-500
  Tombol flip kamera (kanan atas viewport)

[=== MODE UPLOAD ===]
  Drop zone besar (lihat spesifikasi komponen 6.7)
  Setelah file dipilih: Preview gambar + nama file + ukuran + tombol "Ganti"
  Preview mengisi drop zone dengan tombol "Scan Sekarang"

[Tombol Scan Sekarang]
  Full width, --text-lg, height 56px
  Loading state: Spinner + "Menganalisis..."
  Disabled saat tidak ada gambar

[Panduan Foto — Collapsible]
  Tips foto yang baik untuk hasil akurat
  Contoh: foto terlalu jauh ✗ | foto tepat ✓
```

**Animasi Scan:**
- Kamera mount: Fade in bertahap
- Saat capture: Flash putih singkat (opacity 0→1→0, 300ms)
- Saat upload file: Scale in preview gambar
- Loading: Progress bar hijau di bawah viewport + pesan status berubah

---

### 8.5 Halaman Hasil Deteksi

**Tujuan:** Tampilkan hasil AI + berikan pilihan aksi selanjutnya

```
[Header dengan Foto]
  Foto yang discan (fullwidth, 280px height, object-fit cover)
  Overlay gradient bawah untuk teks

[Hasil Utama — Card Besar]
  Badge status: TERDETEKSI / SEHAT
  Nama Penyakit: H2 dengan --font-heading
  Tingkat Keparahan: Progress bar warna (hijau/kuning/merah) + label
  Tingkat Keyakinan AI: Persentase (mis. "94% akurat")

[Detail Penyakit — Accordion / Tab]
  Tab 1 — Deskripsi: Penjelasan singkat penyakit
  Tab 2 — Gejala: List gejala yang terlihat
  Tab 3 — Penanganan: Langkah-langkah rekomendasi (numbered list)
  Tab 4 — Pencegahan: Tips ke depannya

[Bagian Lain yang Terdeteksi]
  Jika ada beberapa area bermasalah: card kecil tiap area

[=== PILIHAN AKSI — 2 TOMBOL BESAR ===]
  [Lihat Hasil Saja]          [Diskusi dengan AI →]
  Ghost/Secondary             Primary, --green-500
  "Simpan & selesai"          "Tanya lebih lanjut seputar ini"

  Jika pilih "Lihat Hasil Saja":
    → Animasi konfirmasi (centang hijau)
    → Tombol "Kembali ke Dashboard" + "Scan Lagi"
    → Hasil tersimpan otomatis ke riwayat

  Jika pilih "Diskusi dengan AI":
    → Transisi ke halaman Chat dengan konteks sudah terisi
```

**Animasi Hasil:**
- Progress bar keparahan: Animate dari 0% ke nilai sebenarnya
- Persentase keyakinan: Count-up dari 0%
- Accordion: Expand/collapse smooth dengan height animation

---

### 8.6 Halaman Chat AI

**Tujuan:** Tanya jawab bebas seputar tanaman cabai yang discan

```
[Layout: Sidebar + Main]

[Sidebar Kiri — 280px]
  Tombol "+ Chat Baru"
  List riwayat chat (grouped: Hari Ini, Kemarin, Minggu Lalu)
  Tiap item: Ikon + Judul singkat + Timestamp
  Active state: Background --green-50, border-left 3px --green-500

[Main — Flex Column]
  [Header Chat]
    Judul topik / "Chat Baru"
    Tombol: Hapus, Ekspor

  [Context Banner — jika dari hasil scan]
    Card kecil --green-50: "Berdasarkan scan: [Nama Penyakit] [Tanggal]"
    Bisa diklik untuk lihat detail hasil

  [Area Pesan — Scrollable]
    Bubble chat (lihat spesifikasi 6.8)
    Timestamp dikelompokkan per jam
    Avatar AI: Logo ChiliScan kecil (28px)

  [Pesan Selamat Datang — jika chat baru]
    "Halo! Saya siap membantu kamu seputar tanaman cabai 🌶️"
    3 suggested question chips yang bisa diklik

  [Input Area — Sticky Bottom]
    Input teks: "Ketik pertanyaanmu..."
    Tombol kirim: Ikon panah → --green-500
    Karakter counter (opsional)
    Hint: "Tekan Enter untuk kirim, Shift+Enter baris baru"
```

**Animasi Chat:**
- Bubble masuk: Slide + fade dari sisi masing-masing
- Typing indicator: Muncul saat AI memproses
- Auto-scroll smooth ke pesan terbaru
- Suggested chips: Stagger fade in saat chat baru

---

### 8.7 Halaman Riwayat

**Tujuan:** Akses kembali semua scan dan chat

```
[Header]
  "Riwayat Saya"
  Tab: "Hasil Scan" | "Percakapan"
  Filter: Bulan, Penyakit (untuk scan) | Pencarian

[=== TAB HASIL SCAN ===]
  Layout: Grid 3 kolom (desktop), 2 (tablet), 1 (mobile)
  
  Card Scan:
    Foto thumbnail (atas, rasio 16:9)
    Badge penyakit (overlay kiri atas)
    Nama penyakit (H4)
    Tingkat keparahan (progress mini)
    Tanggal scan
    Tombol: "Lihat Detail" | "Hapus"

[=== TAB PERCAKAPAN ===]
  Layout: List vertikal

  Item Chat:
    Ikon chat (40px, --green-100)
    Judul percakapan (1 baris, truncate)
    Preview pesan terakhir (2 baris, truncate)
    Tanggal + jumlah pesan
    Chevron kanan

[Empty State]
  Ilustrasi daun cabai sederhana (SVG)
  Teks: "Belum ada riwayat scan"
  Tombol: "Mulai Scan Pertama"

[Pagination]
  Infinite scroll ATAU pagination bernomor
  Loading skeleton saat memuat data baru
```

---

### 8.8 Halaman Profil

**Tujuan:** Kelola akun dan preferensi pengguna

```
[Header Profil]
  Background: --green-50
  Avatar besar (80px) + Nama + Email
  Tombol: "Edit Foto"

[Section — Informasi Akun]
  Card:
    Nama Lengkap (editable)
    Email (read-only jika SSO)
    Tanggal Bergabung
    Tombol: "Simpan Perubahan"

[Section — Keamanan]
  Card:
    Ganti Password (dengan input lama + baru)
    Login aktif di perangkat
    Tombol logout semua perangkat

[Section — Preferensi]
  Bahasa: Indonesia / English
  Notifikasi email (toggle)

[Section — Data]
  Ekspor semua data (JSON/PDF)
  Hapus riwayat scan
  Hapus akun (danger zone — merah, konfirmasi modal)

[Statistik Akun]
  Total scan | Total chat | Bergabung sejak
```

---

## 9. Responsivitas

### Breakpoints

```css
/* Mobile first */
--bp-sm:  640px;   /* Smartphone landscape */
--bp-md:  768px;   /* Tablet portrait */
--bp-lg:  1024px;  /* Tablet landscape / Laptop kecil */
--bp-xl:  1280px;  /* Desktop */
--bp-2xl: 1536px;  /* Wide desktop */
```

### Adaptasi per Komponen

| Komponen | Mobile (<768px) | Tablet (768–1024px) | Desktop (>1024px) |
|---|---|---|---|
| Navbar | Hamburger menu + drawer | Hamburger / full | Full horizontal |
| Landing Hero | 1 kolom, center | 1 kolom atau 2 | 2 kolom split |
| Dashboard Stats | 1 kolom | 3 kolom | 3 kolom |
| Scan Cards Grid | 1 kolom | 2 kolom | 3 kolom |
| Hasil Deteksi | Full width stack | Full width | Max-width 800px centered |
| Chat Layout | Sidebar hidden (drawer) | Sidebar 240px | Sidebar 280px |
| Riwayat Grid | 1 kolom | 2 kolom | 3 kolom |
| Auth (Login) | Single kolom | Single kolom | Split screen |

### Navigasi Mobile

```
Bottom Navigation Bar (mobile only):
  5 ikon: Home | Scan | Riwayat | Chat | Profil
  Height: 60px + safe area
  Background: white
  Border-top: 1px solid --border-default
  Backdrop-filter: blur(8px)
  Active: ikon --green-500 + label kecil
```

---

## 10. Aksesibilitas

### Kontras Warna

| Pasangan | Rasio | Status |
|---|---|---|
| `--gray-800` di `--white` | 12.6:1 | ✅ AAA |
| `--gray-600` di `--white` | 5.9:1 | ✅ AA |
| `--white` di `--green-500` | 4.8:1 | ✅ AA |
| `--green-700` di `--green-50` | 7.2:1 | ✅ AAA |
| `--gray-400` (placeholder) di `--white` | 3.0:1 | ⚠ Minimum |

### Keyboard Navigation

- Semua interaksi dapat diakses via keyboard
- Tab order mengikuti alur visual yang logis
- Focus ring: `outline: 3px solid rgba(45,122,58,0.5)`, `outline-offset: 2px`
- Skip to main content link di awal halaman
- Modal trap focus saat terbuka

### Screen Reader

- Semua gambar memiliki `alt` yang deskriptif
- Form input memiliki `label` yang berasosiasi
- Status scan menggunakan `aria-live="polite"`
- Ikon dekoratif: `aria-hidden="true"`
- Tombol ikon: `aria-label` yang jelas

### Reduced Motion

```ts
// Semua animasi Framer Motion harus memeriksa ini
const prefersReducedMotion = useReducedMotion()
// Jika true → matikan atau sederhanakan animasi
```

---

## 11. Performa & Optimasi

### Target Performa

| Metrik | Target |
|---|---|
| LCP (Largest Contentful Paint) | < 2.5 detik |
| FID / INP | < 100ms |
| CLS | < 0.1 |
| TTI (Time to Interactive) | < 3.5 detik |
| Bundle size (initial JS) | < 150KB gzip |

### Strategi Optimasi

**Gambar:**
- Format: WebP dengan fallback JPEG
- Lazy loading untuk semua gambar di bawah fold
- `srcset` untuk gambar responsif
- Thumbnail scan: resize di server ke 400px sebelum disimpan

**Font:**
- `font-display: swap` untuk menghindari FOIT
- Preload font heading di `<head>`
- Subset hanya karakter Latin

**JavaScript:**
- Code splitting per route (React lazy + Suspense)
- Tree shaking Framer Motion (import per komponen, bukan bundle penuh)
- Debounce input pencarian (300ms)

**Animasi:**
- Hanya gunakan `transform` dan `opacity`
- `will-change: transform` hanya pada elemen aktif animasi
- Matikan animasi berat di perangkat low-end (deteksi via `navigator.hardwareConcurrency`)

**Caching:**
- Service Worker untuk asset statis
- API response cache untuk data yang tidak sering berubah (daftar penyakit, dsb.)

---

## Catatan Implementasi

### Stack yang Direkomendasikan

```
Framework:    React + Next.js (App Router)
Styling:      Tailwind CSS + CSS Variables
Animasi:      Framer Motion (tree-shaken)
State:        Zustand atau React Query
Auth:         NextAuth.js (Google Provider)
Camera API:   getUserMedia() + canvas
File Upload:  React Dropzone
Icons:        Lucide React (konsisten, ringan)
Toast:        Sonner
```

### Urutan Pengembangan yang Disarankan

1. Design system & komponen dasar (Button, Input, Card, Badge)
2. Auth (Login, Register, SSO + password)
3. Halaman Scan (kamera + upload)
4. Integrasi model AI + Halaman Hasil
5. Halaman Chat AI
6. Dashboard + Riwayat
7. Profil & pengaturan
8. Landing Page (terakhir, setelah produk matang)
9. Optimasi performa + aksesibilitas

---

*Dokumen ini adalah panduan desain hidup — perbarui setiap kali ada keputusan desain baru yang disepakati bersama tim.*
