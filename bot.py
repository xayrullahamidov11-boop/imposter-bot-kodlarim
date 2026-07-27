import os
import random
import json
import telebot
from telebot import types

# ============================================================
# AYARLAR
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable bulunamadı! Render/GitHub panelinden ekle.")

bot = telebot.TeleBot(BOT_TOKEN)

# ============================================================
# KELİME DEPOSUNU (.json) OKUMA FONKSİYONU
# ============================================================
def kelime_depodan_cek():
    try:
        dosya_yolu = os.path.join(os.path.dirname(__file__), 'kelimeler.json')
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            kelime_listesi = json.load(f)
        return random.choice(kelime_listesi)
    except Exception as e:
        # JSON dosyası bulunamazsa veya hata olursa çökmeyi önleyen yedek kelime
        return {"kelime": "Elma", "ipucu": "Hasat"}

# ============================================================
# OYUN DURUMU (chat_id bazlı hafıza)
# ============================================================
oyunlar = {}
# oyunlar[chat_id] = {
#   "asama": str,
#   "kisi_sayisi": int,
#   "toplam_tur": int,
#   "mevcut_tur": int,
#   "kelime": str,
#   "ipucu": str,
#   "imposter_index": int,
#   "gosterilen_oyuncu": int,
#   "son_mesaj_id": int,
# }

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
        "kelime": None,
        "ipucu": None,
        "imposter_index": None,
        "gosterilen_oyuncu": 0,
        "son_mesaj_id": None,
    }

    markup = types.InlineKeyboardMarkup(row_width=4)
    butonlar = [types.InlineKeyboardButton(str(n), callback_data=f"kisi_{n}") for n in range(3, 11)]
    markup.add(*butonlar)

    bot.send_message(
        chat_id,
        "🎭 <b>1-Kelime İpuculu Imposter Oyununa Hoş Geldiniz!</b>\n\nMasada kaç kişisiniz? (3-10 kişi)",
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
    bot.answer_callback_query(call.id)

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

    # ---- Tur sayısı seçimi -> oyunu doğrudan başlat ----
    elif data.startswith("tur_"):
        game["toplam_tur"] = int(data.split("_")[1])
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
    
    # KELİME VE İPUCUNU JSON DEPOSUNDAN ÇEKİYORUZ
    secim = kelime_depodan_cek()
    game["kelime"] = secim["kelime"]
    game["ipucu"] = secim["ipucu"]
    
    game["imposter_index"] = random.randint(1, game["kisi_sayisi"])
    game["gosterilen_oyuncu"] = 1
    game["asama"] = "gosterme"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "👁️ 1. Oyuncu: Kelimemi Göster", callback_data="goster"
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
            "🕵️‍♂️ <b>SEN İMPOSTER'SIN! (GİZLİ CASUS)</b>\n\n"
            f"💡 <b>1 KELİMEYLE SANA ÖZEL İPUCU:</b>\n👉 <b>{game['ipucu'].upper()}</b> 👈\n\n"
            "🤫 <i>Asıl gizli kelimeyi bilmiyorsun! Sadece bu tek kelimelik ipucuna dayanarak çaktırmadan blöf yap ve kendini gizle!</i>"
        )
    else:
        text = (
            f"🔑 <b>Gizli Kelimeniz:</b>\n\n👉 <b>{game['kelime'].upper()}</b> 👈\n\n"
            "<i>(Bu kelimeyi aklında tut! Şimdi telefonu sıradakine ver ve tur başlayınca Imposter'a kelimeyi belli etmeyecek bir ipucu söyle!)</i>"
        )

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
        f"🔑 Asıl Gizli Kelime: <b>{game['kelime'].upper()}</b>\n"
        f"💡 Imposter İpucusu: <b>{game['ipucu'].upper()}</b>\n"
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
