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
    raise RuntimeError("BOT_TOKEN environment variable bulunamadı!")

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
        return {"kelime": "Elma", "ipucu": "Hasat"}

oyunlar = {}

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
        "imposter_sayisi": 1,
        "surpriz_mod": False,
        "toplam_tur": None,
        "mevcut_tur": 0,
        "kelime": None,
        "ipucu": None,
        "imposter_listesi": [],
        "gosterilen_oyuncu": 0,
        "son_mesaj_id": None,
    }

    markup = types.InlineKeyboardMarkup(row_width=4)
    butonlar = [types.InlineKeyboardButton(str(n), callback_data=f"kisi_{n}") for n in range(3, 11)]
    markup.add(*butonlar)

    bot.send_message(
        chat_id,
        "🎭 <b>Gelirmiş Casus Oyununa Hoş Geldiniz!</b>\n\nMasada kaç kişisiniz? (3-10 kişi)",
        reply_markup=markup,
        parse_mode="HTML",
    )

# ============================================================
# CALLBACK HANDLER (Buton Kontrolleri)
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

    # 1. ADIM: Kişi sayısı seçildi -> Casus sayısını sor
    if data.startswith("kisi_"):
        game["kisi_sayisi"] = int(data.split("_")[1])
        game["asama"] = "imposter_secimi"

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("1 Casus 🕵️", callback_data="imp_1"))
        
        # Akıllı Kontrol: Sadece 6 kişi ve fazlasıysa 2 Casus butonunu ekle!
        if game["kisi_sayisi"] >= 6:
            markup.add(types.InlineKeyboardButton("2 Casus 🕵️‍♂️🕵️‍♀️", callback_data="imp_2"))
            
        markup.add(types.InlineKeyboardButton("🎲 Sürpriz Mod (Kaos)", callback_data="imp_surpriz"))

        bot.edit_message_text(
            f"👥 <b>{game['kisi_sayisi']} Kişi</b> seçildi.\n\nMasada kaç Imposter (Casus) olsun?\n"
            "<i>(Not: 2 Casus seçeneği dengeli bir oyun için sadece 6 kişi ve üzeri masalarda açılır.)</i>",
            chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
        )

    # 2. ADIM: Casus sayısı seçildi -> Tur sayısını sor
    elif data.startswith("imp_"):
        secim = data.split("_")[1]
        if secim == "surpriz":
            game["surpriz_mod"] = True
            game["imposter_sayisi"] = 1 # Varsayılan olarak 1 alır ama tur başı rastgele değişir
        else:
            game["surpriz_mod"] = False
            game["imposter_sayisi"] = int(secim)

        game["asama"] = "tur_sayisi"
        markup = types.InlineKeyboardMarkup()
        for n in [1, 3, 5]:
            markup.add(types.InlineKeyboardButton(f"{n} Tur", callback_data=f"tur_{n}"))

        bot.edit_message_text(
            f"⚙️ Casus ayarı yapıldı!\n\nKaç tur oynamak istersiniz?",
            chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
        )

    # 3. ADIM: Tur sayısı seçildi -> Oyunu başlat
    elif data.startswith("tur_"):
        game["toplam_tur"] = int(data.split("_")[1])
        bot.delete_message(chat_id, call.message.message_id)
        yeni_tur_baslat(chat_id)

    elif data == "goster":
        goster_kelime(chat_id, call.message.message_id)

    elif data == "gizle_sirada":
        sirada_gec(chat_id, call.message.message_id)

    elif data == "tartisma_baslat":
        bot.delete_message(chat_id, call.message.message_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🕵️ Imposter Kimdi? (Açıkla)", callback_data="ifsa"))
        gonder_ve_kaydet(
            chat_id,
            "💬 <b>Tartışma Zamanı!</b>\n\nHerkes sırayla kelime hakkında TEK kelimelik bir ipucu versin. "
            "Sonra oylama yapın ve şüphelendiğiniz kişileri seçin!\n\n"
            "Hazır olunca aşağıdaki butona basın:",
            markup,
        )

    elif data == "ifsa":
        bot.delete_message(chat_id, call.message.message_id)
        ifsa_yap(chat_id)

    elif data == "sonraki_tur":
        bot.delete_message(chat_id, call.message.message_id)
        yeni_tur_baslat(chat_id)

# ============================================================
# OYUN AKIŞI FONKSİYONLARI
# ============================================================
def yeni_tur_baslat(chat_id):
    game = oyunlar[chat_id]
    game["mevcut_tur"] += 1
    
    secim = kelime_depodan_cek()
    game["kelime"] = secim["kelime"]
    game["ipucu"] = secim["ipucu"]
    
    kisi = game["kisi_sayisi"]
    oyuncular_listesi = list(range(1, kisi + 1))
    
    # SÜRPRİZ MOD KONTROLÜ (Trol Turlar!)
    if game["surpriz_mod"]:
        sans = random.randint(1, 100)
        if sans <= 15: # %15 İhtimalle HERKES IMPOSTER
            game["imposter_listesi"] = oyuncular_listesi
        elif sans <= 30: # %15 İhtimalle HERKES MASUM (0 Imposter)
            game["imposter_listesi"] = []
        else: # %70 İhtimalle Normal 1 veya 2 Imposter
            imp_sayisi = 2 if kisi >= 6 and random.choice([True, False]) else 1
            game["imposter_listesi"] = random.sample(oyuncular_listesi, imp_sayisi)
    else:
        # Normal Seçim
        game["imposter_listesi"] = random.sample(oyuncular_listesi, game["imposter_sayisi"])
        
    game["gosterilen_oyuncu"] = 1
    game["asama"] = "gosterme"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👁️ 1. Oyuncu: Kelimemi Göster", callback_data="goster"))
    gonder_ve_kaydet(
        chat_id,
        f"🔄 <b>Tur {game['mevcut_tur']}/{game['toplam_tur']}</b>\n\n"
        f"Telefon sırayla elden ele dolaşacak. Lütfen hazırsanız butona basın.",
        markup,
    )

def goster_kelime(chat_id, message_id):
    game = oyunlar[chat_id]
    oyuncu_no = game["gosterilen_oyuncu"]
    bot.delete_message(chat_id, message_id)

    # OYUNCU IMPOSTER MI KONTROL ET
    if oyuncu_no in game["imposter_listesi"]:
        text = (
            "🕵️‍♂️ <b>SEN İMPOSTER'SIN! (GİZLİ CASUS)</b>\n\n"
            f"💡 <b>1 KELİMEYLE SANA ÖZEL İPUCU:</b>\n👉 <b>{game['ipucu'].upper()}</b> 👈\n\n"
            "🤫 <i>Asıl gizli kelimeyi bilmiyorsun! Diğerlerini dinle ve çaktırmadan blöf yap!</i>"
        )
    else:
        text = (
            f"🔑 <b>Gizli Kelimeniz:</b>\n\n👉 <b>{game['kelime'].upper()}</b> 👈\n\n"
            "<i>(Bu kelimeyi aklında tut! Tur başlayınca Imposter'a kelimeyi belli etmeyecek bir ipucu söyle!)</i>"
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
    imp_listesi = game["imposter_listesi"]
    
    if len(imp_listesi) == 0:
        imp_metin = "🤯 <b>BU TURDA HİÇ CASUS YOKTU! (Herkes Masumdu)</b>\n<i>Boşuna birbirinizden şüphelendiniz!</i>"
    elif len(imp_listesi) == game["kisi_sayisi"]:
        imp_metin = "😈 <b>BU TURDA HERKES CASUSTU! (Kimse kelimeyi bilmiyordu)</b>\n<i>Herkes birbirine blöf yapıyormuş!</i>"
    else:
        imp_metin = f"🕵️ Casus(lar): <b>{', '.join(map(str, imp_listesi))}. Oyuncu</b>"

    text = (
        f"🎉 <b>Tur {game['mevcut_tur']} Sonuçları</b>\n\n"
        f"🔑 Asıl Gizli Kelime: <b>{game['kelime'].upper()}</b>\n"
        f"💡 Casus İpucusu: <b>{game['ipucu'].upper()}</b>\n\n"
        f"{imp_metin}"
    )

    if game["mevcut_tur"] < game["toplam_tur"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ Sonraki Tur", callback_data="sonraki_tur"))
        gonder_ve_kaydet(chat_id, text, markup)
    else:
        text += "\n\n🏁 <b>Oyun Bitti!</b> Yeni oyun için /start yazabilirsiniz."
        gonder_ve_kaydet(chat_id, text)

if __name__ == "__main__":
    bot.infinity_polling()
