import os
import random
import telebot
from telebot import types

# ============================================================
# AYARLAR
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable bulunamadı! Render panelinden ekle.")

bot = telebot.TeleBot(BOT_TOKEN)

# ============================================================
# KELİME HAVUZU (kategorili, geniş)
# ============================================================
KELIMELER = {
    "Yiyecekler": [
        "Karpuz", "Pizza", "Lahmacun", "Mercimek Çorbası", "Baklava", "Simit",
        "Döner", "Sushi", "Hamburger", "Makarna", "Pilav", "Kebap", "Çikolata",
        "Dondurma", "Waffle", "Kruvasan", "Menemen", "Köfte", "Sarma",
        "Cacık", "Ayran", "Kokoreç", "Mantı", "Börek", "Şalgam", "Turşu",
        "Tost", "Kumpir", "Balık Ekmek", "Kavun", "Çilek", "Muz", "Nar",
        "Cips", "Fındık", "Bal", "Kaymak", "Yoğurt", "Zeytin", "Peynir",
        "Ekmek Kadayıfı", "Künefe", "Lokum", "Şekerpare", "Revani"
    ],
    "Hayvanlar": [
        "Aslan", "Kedi", "Köpek", "Fil", "Zürafa", "Penguen", "Kaplumbağa",
        "Yılan", "Timsah", "Kartal", "Baykuş", "Papağan", "Tavşan", "Ayı",
        "Kurt", "Tilki", "Geyik", "Yunus", "Balina", "Köpekbalığı", "Ahtapot",
        "Karınca", "Arı", "Kelebek", "Örümcek", "Akrep", "Panda", "Koala",
        "Kanguru", "Zebra", "Gergedan", "Su Aygırı", "Maymun", "Deve", "At",
        "İnek", "Koyun", "Keçi", "Tavuk", "Ördek", "Flamingo", "Yarasa"
    ],
    "Meslekler": [
        "Doktor", "Öğretmen", "Mühendis", "Avukat", "Polis", "İtfaiyeci",
        "Aşçı", "Pilot", "Hemşire", "Mimar", "Ressam", "Müzisyen", "Berber",
        "Terzi", "Marangoz", "Elektrikçi", "Tesisatçı", "Şoför", "Garson",
        "Kasap", "Fırıncı", "Eczacı", "Veteriner", "Muhasebeci", "Gazeteci",
        "Fotoğrafçı", "Yazılımcı", "Dedektif", "Balıkçı", "Çiftçi", "Postacı",
        "Diş Hekimi", "Psikolog", "Antrenör", "Aktör", "Şarkıcı", "Yazar"
    ],
    "Ülkeler ve Şehirler": [
        "Türkiye", "Japonya", "Fransa", "İtalya", "Brezilya", "Mısır",
        "Almanya", "İspanya", "Kanada", "Meksika", "Hindistan", "Çin",
        "İstanbul", "Paris", "Roma", "Tokyo", "New York", "Londra",
        "Kapadokya", "Antalya", "Venedik", "Dubai", "Amsterdam", "Berlin",
        "Kahire", "Rio de Janeiro", "Sidney", "Barcelona", "Prag", "Atina"
    ],
    "Spor Dalları": [
        "Futbol", "Basketbol", "Voleybol", "Tenis", "Yüzme", "Koşu",
        "Güreş", "Boks", "Judo", "Karate", "Bisiklet", "Kayak", "Golf",
        "Bilardo", "Satranç", "Okçuluk", "Eskrim", "Halter", "Jimnastik",
        "Su Topu", "Masa Tenisi", "Badminton", "Buz Hokeyi", "Sörf",
        "Dalış", "Dağcılık", "Atletizm", "Formula 1", "Bowling"
    ],
    "Ev Eşyaları": [
        "Buzdolabı", "Televizyon", "Koltuk", "Masa", "Sandalye", "Lamba",
        "Halı", "Yatak", "Dolap", "Ayna", "Saat", "Perde", "Çamaşır Makinesi",
        "Bulaşık Makinesi", "Fırın", "Mikrodalga", "Süpürge", "Ütü",
        "Klima", "Vantilatör", "Kitaplık", "Yastık", "Battaniye", "Termos"
    ],
    "Doğa ve Yerler": [
        "Orman", "Dağ", "Deniz", "Göl", "Nehir", "Çöl", "Ada", "Şelale",
        "Mağara", "Volkan", "Plaj", "Vadi", "Yanardağ", "Buzul", "Ova",
        "Bahçe", "Park", "Yıldız", "Ay", "Güneş", "Gökkuşağı", "Fırtına",
        "Kar", "Yağmur", "Bulut", "Rüzgar"
    ],
    "Taşıtlar": [
        "Araba", "Otobüs", "Uçak", "Tren", "Gemi", "Bisiklet", "Motosiklet",
        "Helikopter", "Metro", "Tramvay", "Kamyon", "Vapur", "Yat",
        "Kaykay", "Scooter", "Roket", "Balon", "Traktör", "İtfaiye Aracı",
        "Ambulans", "Taksi", "Teleferik"
    ],
    "Soyut / Zor": [
        "Aşk", "Zaman", "Özgürlük", "Hayal", "Korku", "Mutluluk", "Sabır",
        "Cesaret", "Adalet", "Dostluk", "Umut", "Rüya", "Sessizlik",
        "Müzik", "Sanat", "Hafıza", "Şans", "Merak", "Yalnızlık", "Huzur"
    ],
}

TUM_KATEGORILER = list(KELIMELER.keys()) + ["Karışık (Hepsi)"]

# ============================================================
# OYUN DURUMU (chat_id bazlı hafıza)
# ============================================================
oyunlar = {}
# oyunlar[chat_id] = {
#   "asama": "kisi_sayisi" | "tur_sayisi" | "kategori" | "gosterme" | "tartisma" | "bitti",
#   "kisi_sayisi": int,
#   "toplam_tur": int,
#   "mevcut_tur": int,
#   "kategori": str,
#   "kelime": str,
#   "imposter_index": int,
#   "gosterilen_oyuncu": int,
#   "kullanilmis_kelimeler": set(),
#   "son_mesaj_id": int,
# }


def yeni_kelime_sec(chat_id, kategori):
    game = oyunlar[chat_id]
    if kategori == "Karışık (Hepsi)":
        havuz = [k for liste in KELIMELER.values() for k in liste]
    else:
        havuz = KELIMELER[kategori]

    kullanilan = game["kullanilmis_kelimeler"]
    aday_havuz = [k for k in havuz if k not in kullanilan]

    # Havuz tükendiyse sıfırla (aynı kelime tekrar gelmeden önce tüm havuz dönsün)
    if not aday_havuz:
        kullanilan.clear()
        aday_havuz = havuz

    secilen = random.choice(aday_havuz)
    kullanilan.add(secilen)
    return secilen


def sil_onceki_mesaj(chat_id):
    game = oyunlar.get(chat_id)
    if game and game.get("son_mesaj_id"):
        try:
            bot.delete_message(chat_id, game["son_mesaj_id"])
        except Exception:
            pass  # Mesaj zaten silinmiş olabilir, sorun değil


def gonder_ve_kaydet(chat_id, text, markup=None):
    msg = bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    oyunlar[chat_id]["son_mesaj_id"] = msg.message_id
    return msg


# ============================================================
# /start KOMUTU
# ============================================================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    oyunlar[chat_id] = {
        "asama": "kisi_sayisi",
        "kisi_sayisi": None,
        "toplam_tur": None,
        "mevcut_tur": 0,
        "kategori": None,
        "kelime": None,
        "imposter_index": None,
        "gosterilen_oyuncu": 0,
        "kullanilmis_kelimeler": set(),
        "son_mesaj_id": None,
    }

    markup = types.InlineKeyboardMarkup(row_width=4)
    butonlar = [types.InlineKeyboardButton(str(n), callback_data=f"kisi_{n}") for n in range(3, 11)]
    markup.add(*butonlar)

    bot.send_message(
        chat_id,
        "🎭 <b>Imposter Oyununa Hoş Geldiniz!</b>\n\nMasada kaç kişisiniz? (3-10 kişi)",
        reply_markup=markup,
        parse_mode="HTML",
    )


# ============================================================
# CALLBACK HANDLER (tüm buton tıklamaları)
# ============================================================
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    chat_id = call.message.chat.id
    data = call.data

    if chat_id not in oyunlar:
        bot.answer_callback_query(call.id, "Oyun bulunamadı, lütfen /start ile yeniden başlatın.")
        return

    game = oyunlar[chat_id]
    bot.answer_callback_query(call.id)  # butondaki "yükleniyor" animasyonunu kapatır

    # ---- Kişi sayısı seçimi ----
    if data.startswith("kisi_"):
        game["kisi_sayisi"] = int(data.split("_")[1])
        game["asama"] = "tur_sayisi"

        markup = types.InlineKeyboardMarkup()
        for n in [1, 3, 5]:
            markup.add(types.InlineKeyboardButton(f"{n} Tur", callback_data=f"tur_{n}"))

        bot.edit_message_text(
            f"👥 {game['kisi_sayisi']} kişi seçildi.\n\nKaç tur oynamak istersiniz?",
            chat_id, call.message.message_id, reply_markup=markup,
        )

    # ---- Tur sayısı seçimi ----
    elif data.startswith("tur_"):
        game["toplam_tur"] = int(data.split("_")[1])
        game["asama"] = "kategori"

        markup = types.InlineKeyboardMarkup(row_width=2)
        butonlar = [types.InlineKeyboardButton(k, callback_data=f"kategori_{i}") for i, k in enumerate(TUM_KATEGORILER)]
        markup.add(*butonlar)

        bot.edit_message_text(
            f"🎲 {game['toplam_tur']} tur seçildi.\n\nHangi kategoriden kelimeler gelsin?",
            chat_id, call.message.message_id, reply_markup=markup,
        )

    # ---- Kategori seçimi -> oyunu başlat ----
    elif data.startswith("kategori_"):
        idx = int(data.split("_")[1])
        game["kategori"] = TUM_KATEGORILER[idx]
        bot.delete_message(chat_id, call.message.message_id)
        yeni_tur_baslat(chat_id)

    # ---- "Kelimemi Göster" butonu ----
    elif data == "goster":
        goster_kelime(chat_id, call.message.message_id)

    # ---- "Gizle ve Sıradakine Ver" butonu ----
    elif data == "gizle_sirada":
        sirada_gec(chat_id, call.message.message_id)

    # ---- "Turu Başlat" (tartışma aşamasına geç) ----
    elif data == "tartisma_baslat":
        bot.delete_message(chat_id, call.message.message_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🕵️ Imposter Kimdi? (Açıkla)", callback_data="ifsa"))
        gonder_ve_kaydet(
            chat_id,
            "💬 <b>Tartışma Zamanı!</b>\n\nHerkes sırayla kelime hakkında TEK kelimelik bir ipucu versin. "
            "Sonra oylama yapın, kimin Imposter olduğunu düşünüyorsanız açıklayın.\n\n"
            "Hazır olunca aşağıdaki butona basın:",
            markup,
        )

    # ---- İfşa ----
    elif data == "ifsa":
        bot.delete_message(chat_id, call.message.message_id)
        ifsa_yap(chat_id)

    # ---- Sonraki tur ----
    elif data == "sonraki_tur":
        bot.delete_message(chat_id, call.message.message_id)
        yeni_tur_baslat(chat_id)


# ============================================================
# OYUN AKIŞI FONKSİYONLARI
# ============================================================
def yeni_tur_baslat(chat_id):
    game = oyunlar[chat_id]
    game["mevcut_tur"] += 1
    game["kelime"] = yeni_kelime_sec(chat_id, game["kategori"])
    game["imposter_index"] = random.randint(1, game["kisi_sayisi"])
    game["gosterilen_oyuncu"] = 1
    game["asama"] = "gosterme"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        f"👁️ 1. Oyuncu: Kelimemi Göster", callback_data="goster"
    ))
    gonder_ve_kaydet(
        chat_id,
        f"🔄 <b>Tur {game['mevcut_tur']}/{game['toplam_tur']}</b>\n\n"
        f"Telefon sırayla elden ele dolaşacak. Herkes kendi sırası geldiğinde butona basıp kelimesini görecek.",
        markup,
    )


def goster_kelime(chat_id, message_id):
    game = oyunlar[chat_id]
    oyuncu_no = game["gosterilen_oyuncu"]
    bot.delete_message(chat_id, message_id)

    if oyuncu_no == game["imposter_index"]:
        text = (
            "🕵️‍♂️ <b>SEN IMPOSTER'SIN!</b>\n\n"
            "Kelimeyi bilmiyorsun. Çaktırmadan dinle, diğerlerinin ipuçlarından kelimeyi tahmin etmeye çalış ve blöf yap!"
        )
    else:
        text = f"🔑 <b>Gizli Kelimeniz:</b>\n\n<b>{game['kelime']}</b>"

    if oyuncu_no < game["kisi_sayisi"]:
        buton_metni = "🙈 Gizle ve Sıradakine Ver"
        callback = "gizle_sirada"
    else:
        buton_metni = "▶️ Herkes Gördü, Turu Başlat"
        callback = "tartisma_baslat"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(buton_metni, callback_data=callback))
    gonder_ve_kaydet(chat_id, text, markup)


def sirada_gec(chat_id, message_id):
    game = oyunlar[chat_id]
    bot.delete_message(chat_id, message_id)
    game["gosterilen_oyuncu"] += 1
    n = game["gosterilen_oyuncu"]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"👁️ {n}. Oyuncu: Kelimemi Göster", callback_data="goster"))
    gonder_ve_kaydet(chat_id, f"📱 Telefonu {n}. oyuncuya verin.", markup)


def ifsa_yap(chat_id):
    game = oyunlar[chat_id]
    text = (
        f"🎉 <b>Tur {game['mevcut_tur']} Sonuçları</b>\n\n"
        f"🔑 Kelime: <b>{game['kelime']}</b>\n"
        f"🕵️ Imposter: <b>{game['imposter_index']}. Oyuncu</b> idi!"
    )

    if game["mevcut_tur"] < game["toplam_tur"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ Sonraki Tur", callback_data="sonraki_tur"))
        gonder_ve_kaydet(chat_id, text, markup)
    else:
        text += "\n\n🏁 <b>Oyun Bitti!</b> Yeni oyun için /start yazabilirsiniz."
        gonder_ve_kaydet(chat_id, text)


# ============================================================
# BOTU BAŞLAT
# ============================================================
if __name__ == "__main__":
    print("Bot çalışıyor...")
    bot.infinity_polling()
