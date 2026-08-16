# React Frontend — Local RAG Document Assistant

FastAPI backend'ine (`backend/api/main.py`) bağlanan, dark-mode, minimal bir
RAG doküman asistanı arayüzü. React + TypeScript + Vite ile yazıldı, ek bir
UI framework kullanılmadı (sade CSS).

## Kurulum

```bash
cd react_frontend
npm install
```

API adresini `.env` dosyasında belirt (varsayılan `http://localhost:8000`):

```bash
cp .env.example .env
```

## Çalıştırma

Önce backend'i ayrı bir terminalde başlat (proje kök dizininden):

```bash
uvicorn backend.api.main:app --reload
```

Sonra frontend'i başlat:

```bash
npm run dev
```

Vite dev sunucusu `http://localhost:5173` adresinde açılır.

## Yapı

- `src/config.ts` — API taban URL'si (`VITE_API_BASE_URL` env değişkeninden okunur, tek yerde tanımlı)
- `src/types.ts` — backend response'larına karşılık gelen TypeScript tipleri
- `src/api.ts` — tüm HTTP çağrılarının toplandığı merkezi servis katmanı
- `src/components/Sidebar.tsx` — koleksiyon listesi/oluşturma, belge listesi/yükleme
- `src/components/ChatPanel.tsx` — mesaj geçmişi, soru input'u
- `src/components/SourcesPanel.tsx` — seçili cevabın kaynakları (dar ekranlarda drawer)

## Kullanılan backend endpoint'leri

`POST /collections`, `GET /collections`, `POST /documents/upload`,
`GET /documents`, `POST /chat/ask`, `GET /chat/history`.

`POST /feedback` ve `GET /stats` bu arayüzde henüz kullanılmıyor.

## Bilinen sınırlama

`POST /chat/ask` yanıtındaki `sources` alanı yalnızca `document_name`,
`chunk_index` ve `similarity_score` döndürüyor; chunk metninin önizlemesi
API'de yok, bu yüzden sağ paneldeki kaynak kartlarında metin önizlemesi
gösterilmiyor.

## Build

```bash
npm run build
```
