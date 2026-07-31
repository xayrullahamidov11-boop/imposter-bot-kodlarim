import os
import random
import json
import threading
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable bulunamadı!")

bot = telebot.TeleBot(BOT_TOKEN)

YEDEK_HAVUZ = [
    {"kelime": "Elma", "ipucu": "Hasat"}, {"kelime": "Muz", "ipucu": "Sıcak"},
    {"kelime": "Karpuz", "ipucu": "Bostan"}, {"kelime": "Pizza", "ipucu": "Dilim"},
    {"kelime": "Futbol", "ipucu": "Stadyum"}, {"kelime": "Sinema", "ipucu": "Seans"},
    {"kelime": "Hastane", "ipucu": "Nöbet"}, {"kelime": "Gitar", "ipucu": "Akort"},
    {"kelime": "Aslan", "ipucu": "Savana"}, {"kelime": "Deniz", "ipucu": "Derinlik"}
]

oyunlar = {}

def kelime_depodan_cek(chat_id):
    game = oyunlar.get(chat_id, {})
    kullanilanlar = game.get("kullanilan_kelimeler", set())
    kelime_listesi = YEDEK_HAVUZ
    try:
        dosya_yolu = os.path.join(os.path.dirname(__file__), 'kelimeler.json')
        if os.path.exists(dosya_yolu):
            with open(dosya_yolu, 'r', encoding='utf-8') as f:
                kelime_listesi = json.load(f)
    except Exception:
        pass

    adaylar = [k for k in kelime_listesi if k["kelime"] not in kullanilanlar]
    if not adaylar:
        kullanilanlar.clear()
        adaylar = kelime_listesi

    secim = random.choice(adaylar)
    kullanilanlar.add(secim["kelime"])
    game["kullanilan_kelimeler"] = kullanilanlar
    return secim

def gonder_ve_kaydet(chat_id, text, markup=None):
    msg = bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    if chat_id in oyunlar:
        oyunlar[chat_id]["son_mesaj_id"] = msg.message_id
    return msg

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    yeni_oyun_menusu(chat_id)

def yeni_oyun_menusu(chat_id):
    kullanilan = oyunlar.get(chat_id, {}).get("kullanilan_kelimeler", set())
    oyunlar[chat_id] = {
        "kisi_sayisi": None,
        "imposter_sayisi": 1,
        "surpriz_mod": False,
        "kelime": None,
        "ipucu": None,
        "imposter_listesi": [],
        "gosterilen_oyuncu": 0,
        "son_mesaj_id": None,
        "kullanilan_kelimeler": kullanilan
    }

    markup = types.InlineKeyboardMarkup(row_width=4)
    butonlar = [types.InlineKeyboardButton(str(n), callback_data=f"kisi_{n}") for n in range(3, 11)]
    markup.add(*butonlar)
    gonder_ve_kaydet(chat_id, "🎭 <b>Yeni Oyuna Hoş Geldiniz!</b>\n\nMasada kaç kişisiniz?", markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    chat_id = call.message.chat.id
    data = call.data

    if chat_id not in oyunlar:
        bot.answer_callback_query(call.id, "Oyun bulunamadı, /start yazın.")
        return

    game = oyunlar[chat_id]
    bot.answer_callback_query(call.id)

    if data.startswith("kisi_"):
        game["kisi_sayisi"] = int(data.split("_")[1])
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("1 Imposter 🕵️", callback_data="imp_1"))
        if game["kisi_sayisi"] >= 6:
            markup.add(types.InlineKeyboardButton("2 Imposter 🕵️‍♂️🕵️‍♀️", callback_data="imp_2"))
            markup.add(types.InlineKeyboardButton("🎲 Sürpriz Mod", callback_data="imp_surpriz"))

        bot.edit_message_text(
            f"👥 <b>{game['kisi_sayisi']} Kişi</b>\n\nKaç Imposter olsun?",
            chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
        )

    elif data.startswith("imp_"):
        secim = data.split("_")[1]
        if secim == "surpriz":
            game["surpriz_mod"] = True
            game["imposter_sayisi"] = 1
        else:
            game["surpriz_mod"] = False
            game["imposter_sayisi"] = int(secim)

        bot.delete_message(chat_id, call.message.message_id)
        yeni_tur_baslat(chat_id)

    elif data == "goster":
        goster_kelime(chat_id, call.message.message_id)

    elif data == "gizle_sirada":
        sirada_gec(chat_id, call.message.message_id)

    elif data == "ilk_konusan":
        bot.delete_message(chat_id, call.message.message_id)
        ilk_kisi = random.randint(1, game["kisi_sayisi"])
        
        text = (
            "💬 <b>TARTIŞMA ZAMANI!</b>\n\n"
            f"🎲 İlk ipucunu 👉 <b>{ilk_kisi}. OYUNCU</b> 👈 verecek!\n"
            "<i>(Saat yönünde sırayla devam edin.)</i>\n\n"
            "⏳ <i>Yanlışlıkla basmayı önlemek için 'Sonucu Gör' butonu tam <b>1 dakika</b> sonra belirecektir...</i>"
        )
        msg = gonder_ve_kaydet(chat_id, text)

        # 60 Saniye (1 Dk) Sonra Butonu Ekleme Fonksiyonu
        def buton_ekle(cid, mid):
            try:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🏁 Oylama Bitti (Sonucu Gör)", callback_data="ifsa"))
                bot.edit_message_reply_markup(chat_id=cid, message_id=mid, reply_markup=markup)
            except Exception:
                pass
        
        # Threading Timer ile botu dondurmadan arka planda 60 saniye bekle
        threading.Timer(60.0, buton_ekle, args=(chat_id, msg.message_id)).start()

    elif data == "ifsa":
        bot.delete_message(chat_id, call.message.message_id)
        ifsa_yap(chat_id)

    elif data == "yeni_oyun_kur":
        bot.delete_message(chat_id, call.message.message_id)
        yeni_oyun_menusu(chat_id)


def yeni_tur_baslat(chat_id):
    game = oyunlar[chat_id]
    secim = kelime_depodan_cek(chat_id)
    game["kelime"] = secim["kelime"]
    game["ipucu"] = secim["ipucu"]
    
    kisi = game["kisi_sayisi"]
    oyuncular_listesi = list(range(1, kisi + 1))
    
    if game["surpriz_mod"]:
        sans = random.randint(1, 100)
        if sans <= 10:
            game["imposter_listesi"] = oyuncular_listesi
        elif sans <= 20:
            game["imposter_listesi"] = []
        else:
            imp_sayisi = 2 if kisi >= 6 and random.choice([True, False]) else 1
            game["imposter_listesi"] = random.sample(oyuncular_listesi, imp_sayisi)
    else:
        game["imposter_listesi"] = random.sample(oyuncular_listesi, game["imposter_sayisi"])
        
    game["gosterilen_oyuncu"] = 1

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👁️ 1. Oyuncu: Göster", callback_data="goster"))
    gonder_ve_kaydet(chat_id, "🔄 <b>Yeni Oyun Başladı!</b>\n\n📱 Telefonu 1. Oyuncuya verin.", markup)


def goster_kelime(chat_id, message_id):
    game = oyunlar[chat_id]
    oyuncu_no = game["gosterilen_oyuncu"]
    bot.delete_message(chat_id, message_id)

    if oyuncu_no in game["imposter_listesi"]:
        text = f"🕵️‍♂️ <b>SEN İMPOSTER'SIN!</b>\n\n💡 İpucu: <b>{game['ipucu'].upper()}</b>"
    else:
        text = f"🔑 Gizli Kelime: <b>{game['kelime'].upper()}</b>"

    markup = types.InlineKeyboardMarkup()
    if oyuncu_no < game["kisi_sayisi"]:
        markup.add(types.InlineKeyboardButton("➡️ Gizle ve Sıradakine Ver", callback_data="gizle_sirada"))
    else:
        markup.add(types.InlineKeyboardButton("▶️ Herkes Gördü (İlk Konuşanı Seç)", callback_data="ilk_konusan"))

    gonder_ve_kaydet(chat_id, text, markup)


def sirada_gec(chat_id, message_id):
    game = oyunlar[chat_id]
    bot.delete_message(chat_id, message_id)
    game["gosterilen_oyuncu"] += 1
    n = game["gosterilen_oyuncu"]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"👁️ {n}. Oyuncu: Göster", callback_data="goster"))
    gonder_ve_kaydet(chat_id, f"📱 Telefonu <b>{n}. Oyuncuya</b> verin.", markup)


def ifsa_yap(chat_id):
    game = oyunlar[chat_id]
    imp_listesi = game["imposter_listesi"]
    
    if len(imp_listesi) == 0:
        imp_metin = "🤯 <b>HİÇ İMPOSTER YOKTU! (Herkes Masumdu)</b>"
    elif len(imp_listesi) == game["kisi_sayisi"]:
        imp_metin = "😈 <b>HERKES İMPOSTER'DI! (Kimse kelimeyi bilmiyordu)</b>"
    else:
        imp_metin = f"🕵️ Imposter: <b>{', '.join(map(str, imp_listesi))}. Oyuncu</b>"

    text = (
        f"🎉 <b>Sonuçlar:</b>\n\n"
        f"🔑 Asıl Kelime: <b>{game['kelime'].upper()}</b>\n"
        f"{imp_metin}"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Yeni Oyun Kur", callback_data="yeni_oyun_kur"))
    gonder_ve_kaydet(chat_id, text, markup)


if __name__ == "__main__":
    bot.infinity_polling()
