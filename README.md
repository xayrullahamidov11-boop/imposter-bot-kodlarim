# 🎭 Imposter Bot — Kurulum Rehberi

Bu bot, tek telefonla oynanan "Kim Casus?" tarzı bir parti oyununu Telegram üzerinden yönetir.

## 1) Telegram'da Bot Oluştur (BotFather)

1. Telegram'da **@BotFather** hesabına yaz.
2. `/newbot` yaz, botuna bir isim ve kullanıcı adı ver (kullanıcı adı `bot` ile bitmeli, örn: `imposter_oyun_bot`).
3. BotFather sana uzun bir **token** verecek (örn: `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`). Bunu bir yere kaydet, kimseyle paylaşma.

## 2) Kodu GitHub'a Yükle

1. [github.com](https://github.com) üzerinde yeni bir repo oluştur (örn: `imposter-bot`), **Public** veya **Private** olabilir.
2. Bu klasördeki 3 dosyayı (`bot.py`, `requirements.txt`, `README.md`) o repoya yükle:
   - GitHub'ın web arayüzünden "Add file → Upload files" diyerek sürükle-bırak yapabilirsin, komut satırı bilmene gerek yok.

## 3) Render'da Çalıştır

GitHub kodu sadece **saklar**, çalıştırmaz. Botun 7/24 açık kalması için Render kullanacağız (ücretsiz).

1. [render.com](https://render.com) adresine git, GitHub hesabınla giriş yap.
2. **New → Background Worker** seç (Web Service DEĞİL — bot bir web sitesi değil, sürekli arka planda çalışan bir işlem).
3. Az önce yüklediğin GitHub reposunu seç.
4. Ayarlar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. **Environment Variables** bölümüne git, şunu ekle:
   - Key: `BOT_TOKEN`
   - Value: BotFather'dan aldığın token
6. **Create Background Worker** butonuna bas. Render otomatik olarak kodu çekip botu başlatacak.

Birkaç dakika içinde botun Telegram'da `/start` komutuna cevap vermeye başlayacak. 🎉

## 4) Kodda Bir Şey Değiştirirsen

GitHub'daki dosyayı güncelle (web arayüzünden düzenleyebilirsin) → Render bunu otomatik algılar ve botu yeniden başlatır. Ekstra bir işlem yapmana gerek yok.

## Oyun Akışı (Özet)

1. `/start` → kaç kişi olduğunuzu ve kaç tur oynayacağınızı seçin.
2. Kategori seçin (Yiyecekler, Hayvanlar, Meslekler, Ülkeler, Spor, Ev Eşyaları, Doğa, Taşıtlar, Soyut, veya Karışık).
3. Telefon elden ele dolaşır, herkes sırayla "Kelimemi Göster" butonuna basar, önceki mesaj otomatik silinir.
4. Herkes gördükten sonra tartışma ve oylama yapılır.
5. "Imposter Kimdi?" butonuyla sonuç açıklanır, sıradaki tura geçilir.

## Notlar

- Kelime havuzunda ~230 kelime, 9 kategoride var; aynı kelime havuz tükenene kadar tekrar gelmez.
- `KELIMELER` sözlüğüne istediğin kadar yeni kelime veya yeni kategori ekleyebilirsin — kodun en üstünde, düz liste halinde.
