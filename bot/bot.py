"""
eFootball Shop Bot - Professional versiya
To'lov cheki + Akkaunt rasmi bilan
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, 
    KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, InputMediaVideo
)
from dotenv import load_dotenv

load_dotenv()

# ============ CONFIGURATION ============
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

# ============ LOGGING ============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============ INITIALIZATION ============
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ============ STATES ============
class AdStates(StatesGroup):
    waiting_payment = State()
    waiting_payment_check = State()      # To'lov cheki
    waiting_media = State()              # Akkaunt rasmi
    waiting_type = State()
    waiting_platform = State()
    waiting_rating = State()
    waiting_players = State()
    waiting_price = State()
    waiting_description = State()

# ============ KEYBOARDS ============
def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 E'lon berish")],
            [KeyboardButton(text="📂 Mening e'lonlarim")],
            [KeyboardButton(text="❓ Qo'llanma")],
            [KeyboardButton(text="💰 E'lon narxi")]
        ],
        resize_keyboard=True
    )
    return kb

def cancel_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    return kb

def ad_type_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Sotaman", callback_data="ad_type_sell")],
            [InlineKeyboardButton(text="🛍️ Sotib olaman", callback_data="ad_type_buy")]
        ]
    )

def platform_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Android", callback_data="platform_android")],
            [InlineKeyboardButton(text="🍎 iPhone", callback_data="platform_iphone")],
            [InlineKeyboardButton(text="🎮 Konami ID", callback_data="platform_konami")]
        ]
    )

def admin_ad_kb(ad_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{ad_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{ad_id}")
            ]
        ]
    )

def get_user_link(user):
    if user.username:
        return f"@{user.username}"
    elif user.first_name:
        return f"[{user.first_name}](tg://user?id={user.id})"
    else:
        return f"[User](tg://user?id={user.id})"

def format_price(price):
    return f"{price:,}".replace(",", " ") + " so'm"

def create_ad_text(data, username, user_id):
    ad_type_text = "🛒 SOTAMAN" if data.get('ad_type') == 'sell' else "🛍️ SOTIB OLAMAN"
    tariff_text = "⭐ VIP" if data.get('tariff') == 'vip' else "📢 ODDIY"
    
    text = (
        "╔══════════════════════════════╗\n"
        f"    {ad_type_text}\n"
        "╚══════════════════════════════╝\n\n"
        "┌──────────────────────────────┐\n"
        f"│ 🎮 Platforma: {data.get('platform', 'N/A')}\n"
        f"│ ⭐ Overall: {data.get('rating', 'N/A')}\n"
        f"│ 👑 Top Players: {data.get('players', 'N/A')}\n"
        f"│ 💰 Narx: {format_price(data.get('price', 0))}\n"
    )
    
    if data.get('description'):
        text += f"│ 📝 Izoh: {data.get('description')}\n"
    
    text += (
        "└──────────────────────────────┘\n\n"
        "┌──────────────────────────────┐\n"
        f"│ 👤 Sotuvchi: {username}\n"
        f"│ 🏷 Tarif: {tariff_text}\n"
        "└──────────────────────────────┘\n\n"
        "════════════════════════════════\n"
        "   📲 Bog'lanish uchun yozing!\n"
        "════════════════════════════════"
    )
    return text

# ============ HANDLERS ============

@dp.message(CommandStart())
async def start_command(message: Message):
    user_link = get_user_link(message.from_user)
    
    welcome = (
        "⚽ **eFootball Shop Bot** ga xush kelibsiz!\n\n"
        f"👋 Salom {user_link}!\n\n"
        "Bu bot orqali siz:\n"
        "• ✅ E'lon berishingiz (sotish yoki olish)\n"
        "• 📂 E'lonlaringizni boshqarishingiz\n"
        "• 👀 Boshqa e'lonlarni ko'rishingiz\n\n"
        "💳 **To'lov ma'lumotlari:**\n"
        "🏦 Karta: `9860166654505204`\n"
        "👤 Egasi: `Sunnatov_Shukurullo`\n\n"
        "👇 Quyidagi tugmalardan foydalaning:"
    )
    await message.answer(welcome, reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amal bekor qilindi", reply_markup=main_menu())

@dp.message(F.text == "📢 E'lon berish")
async def create_ad_start(message: Message, state: FSMContext):
    payment_text = (
        "💰 **E'LON BERISH UCHUN TO'LOV**\n\n"
        "📌 E'lon berishdan oldin to'lov qilishingiz kerak!\n\n"
        "🏦 **Karta raqami:** `9860166654505204`\n"
        "👤 **Karta egasi:** `Sunnatov_Shukurullo`\n\n"
        "💰 **To'lov summalari:**\n"
        "• 📢 Oddiy e'lon: 1000 so'm\n"
        "• ⭐ VIP e'lon: 5000 so'm\n\n"
        "📸 **To'lov chekini (skrinshot) yuboring!**\n\n"
        "👇 Tarifni tanlang:"
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Oddiy (1000 so'm)", callback_data="pay_standard")],
            [InlineKeyboardButton(text="⭐ VIP (5000 so'm)", callback_data="pay_vip")]
        ]
    )
    
    await state.set_state(AdStates.waiting_payment)
    await message.answer(payment_text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    pay_type = callback.data.split("_")[1]
    await state.update_data(tariff=pay_type)
    
    price = "1000" if pay_type == "standard" else "5000"
    tariff_name = "Oddiy" if pay_type == "standard" else "VIP"
    
    await callback.message.edit_text(
        f"💳 **TO'LOV MA'LUMOTLARI**\n\n"
        f"📌 Tarif: {tariff_name}\n"
        f"💰 Summa: {price} so'm\n\n"
        f"🏦 **Karta raqami:** `9860166654505204`\n"
        f"👤 **Karta egasi:** `Sunnatov_Shukurullo`\n\n"
        f"📸 **To'lov chekini (skrinshot) yuboring!**\n"
        f"Chek yuborgandan so'ng akkaunt rasmini yuborasiz.\n\n"
        f"⬇️ **Chek rasmini yuboring:**",
        parse_mode="Markdown"
    )
    
    await state.set_state(AdStates.waiting_payment_check)
    await callback.answer()

@dp.message(AdStates.waiting_payment_check)
async def process_payment_check(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        file_size = message.photo[-1].file_size
    elif message.document:
        file_id = message.document.file_id
        file_size = message.document.file_size
    else:
        await message.answer("❌ Iltimos, to'lov chekining rasmini yuboring!")
        return
    
    if file_size > 20 * 1024 * 1024:
        await message.answer("❌ Fayl hajmi 20MB dan oshmasligi kerak!")
        return
    
    await state.update_data(payment_check_id=file_id)
    await state.set_state(AdStates.waiting_media)
    await message.answer(
        "✅ **To'lov cheki qabul qilindi!**\n\n"
        "📸 **Endi akkaunt rasmini yuboring**\n\n"
        "Bu rasm e'londa ko'rinadi.",
        parse_mode="Markdown"
    )

@dp.message(AdStates.waiting_media)
async def process_media(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
        file_size = message.photo[-1].file_size
    elif message.video:
        file_id = message.video.file_id
        media_type = "video"
        file_size = message.video.file_size
    else:
        await message.answer("❌ Iltimos, akkaunt rasmini (rasm yoki video) yuboring!")
        return
    
    if media_type == "photo" and file_size > 20 * 1024 * 1024:
        await message.answer("❌ Rasm hajmi 20MB dan oshmasligi kerak!")
        return
    if media_type == "video" and file_size > 50 * 1024 * 1024:
        await message.answer("❌ Video hajmi 50MB dan oshmasligi kerak!")
        return
    
    await state.update_data(media_file_id=file_id, media_type=media_type)
    await state.set_state(AdStates.waiting_type)
    await message.answer(
        "📋 **E'lon turini tanlang:**",
        reply_markup=ad_type_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("ad_type_"))
async def process_ad_type(callback: CallbackQuery, state: FSMContext):
    ad_type = callback.data.split("_")[2]
    await state.update_data(ad_type=ad_type)
    await state.set_state(AdStates.waiting_platform)
    await callback.message.edit_text(
        "🎮 **Platformani tanlang:**",
        reply_markup=platform_kb()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("platform_"))
async def process_platform(callback: CallbackQuery, state: FSMContext):
    platform = callback.data.split("_")[1]
    platform_names = {
        "android": "Android",
        "iphone": "iPhone",
        "konami": "Konami ID"
    }
    await state.update_data(platform=platform_names.get(platform, platform))
    await state.set_state(AdStates.waiting_rating)
    await callback.message.edit_text(
        "⭐ **Overall ratingni kiriting** (0-100):\n\n"
        "Faqat son kiriting, masalan: `95`",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(AdStates.waiting_rating)
async def process_rating(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting (0-100)")
        return
    
    rating = int(message.text)
    if rating < 0 or rating > 100:
        await message.answer("❌ Rating 0 dan 100 gacha bo'lishi kerak!")
        return
    
    await state.update_data(rating=rating)
    await state.set_state(AdStates.waiting_players)
    await message.answer(
        "👑 **Top playerlarni yozing:**\n\n"
        "Masalan: `Messi, Neymar, Ronaldinho, Mbappe`",
        parse_mode="Markdown"
    )

@dp.message(AdStates.waiting_players)
async def process_players(message: Message, state: FSMContext):
    players = message.text.strip()
    if not players:
        await message.answer("❌ Iltimos, playerlarni kiriting!")
        return
    
    await state.update_data(players=players)
    await state.set_state(AdStates.waiting_price)
    await message.answer(
        "💰 **Narxni kiriting** (so'mda):\n\n"
        "Faqat son kiriting, masalan: `350000`",
        parse_mode="Markdown"
    )

@dp.message(AdStates.waiting_price)
async def process_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting!")
        return
    
    price = int(message.text)
    if price < 1000:
        await message.answer("❌ Narx 1000 so'mdan kam bo'lmasligi kerak!")
        return
    
    await state.update_data(price=price)
    await state.set_state(AdStates.waiting_description)
    await message.answer(
        "📝 **Qo'shimcha ma'lumot:**\n\n"
        "Agar qo'shimcha ma'lumot bo'lmasa, '⏭ O'tkazib yuborish' tugmasini bosing.",
        reply_markup=cancel_kb()
    )

@dp.message(AdStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text
    if description == "⏭ O'tkazib yuborish":
        description = None
    elif description == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Amal bekor qilindi", reply_markup=main_menu())
        return
    
    data = await state.get_data()
    data["description"] = description
    
    username = get_user_link(message.from_user)
    user_id = message.from_user.id
    
    ad_text = create_ad_text(data, username, user_id)
    
    media_file_id = data.get("media_file_id")
    media_type = data.get("media_type")
    payment_check_id = data.get("payment_check_id")
    tariff = data.get("tariff", "standard")
    
    # Send preview to user
    try:
        if media_type == "photo":
            await message.answer_photo(media_file_id, caption=ad_text, parse_mode="Markdown")
        else:
            await message.answer_video(media_file_id, caption=ad_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending ad: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        await state.clear()
        return
    
    # Prepare for admin
    tariff_text = "⭐ VIP" if tariff == 'vip' else "📢 ODDIY"
    ad_type_text = "SOTAMAN" if data.get('ad_type') == 'sell' else "SOTIB OLAMAN"
    
    admin_text = (
        "🆕 **YANGI E'LON**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Foydalanuvchi:** {username}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"🏷 **Tarif:** {tariff_text}\n"
        f"📋 **Tur:** {ad_type_text}\n"
        f"💳 **To'lov cheki:** ✅ Qabul qilindi\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{ad_text}"
    )
    
    ad_id = int(datetime.now().timestamp())
    
    # Send to admin with both images
    if ADMIN_ID:
        try:
            # Send payment check first
            await bot.send_photo(
                ADMIN_ID,
                payment_check_id,
                caption="💳 **To'lov cheki**",
                parse_mode="Markdown"
            )
            
            # Then send ad with media
            if media_type == "photo":
                await bot.send_photo(
                    ADMIN_ID,
                    media_file_id,
                    caption=admin_text,
                    reply_markup=admin_ad_kb(ad_id),
                    parse_mode="Markdown"
                )
            else:
                await bot.send_video(
                    ADMIN_ID,
                    media_file_id,
                    caption=admin_text,
                    reply_markup=admin_ad_kb(ad_id),
                    parse_mode="Markdown"
                )
            
            await message.answer(
                "✅ **E'loningiz admin tekshiruviga yuborildi!**\n\n"
                "📌 Admin to'lov chekingizni tekshiradi.\n"
                "✅ Tasdiqlangandan so'ng kanalda chiqariladi.\n"
                "⏳ Iltimos, biroz kuting.",
                reply_markup=main_menu(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending to admin: {e}")
            await message.answer("❌ Admin yuborishda xatolik! Iltimos, qaytadan urinib ko'ring.")
    else:
        logger.warning("ADMIN_ID not set!")
        await message.answer("❌ Admin topilmadi! Iltimos, bot egasiga murojaat qiling.")
    
    # Store pending ad
    if not hasattr(dp, 'pending_ads'):
        dp.pending_ads = {}
    
    dp.pending_ads[ad_id] = {
        'data': data,
        'user_id': user_id,
        'username': username,
        'media_file_id': media_file_id,
        'media_type': media_type,
        'payment_check_id': payment_check_id,
        'ad_text': ad_text
    }
    
    await state.clear()

@dp.callback_query(F.data.startswith("approve_"))
async def approve_ad(callback: CallbackQuery):
    ad_id = int(callback.data.split("_")[1])
    
    if not hasattr(dp, 'pending_ads') or ad_id not in dp.pending_ads:
        await callback.answer("❌ E'lon topilmadi!")
        return
    
    ad_data = dp.pending_ads[ad_id]
    
    if CHANNEL_ID:
        try:
            channel_username = None
            try:
                chat = await bot.get_chat(CHANNEL_ID)
                if chat.username:
                    channel_username = f"@{chat.username}"
            except:
                pass
            
            channel_text = ad_data['ad_text']
            if channel_username:
                channel_text += f"\n\n📢 {channel_username}"
            
            if ad_data['media_type'] == "photo":
                await bot.send_photo(
                    CHANNEL_ID,
                    ad_data['media_file_id'],
                    caption=channel_text,
                    parse_mode="Markdown"
                )
            else:
                await bot.send_video(
                    CHANNEL_ID,
                    ad_data['media_file_id'],
                    caption=channel_text,
                    parse_mode="Markdown"
                )
            
            # Notify user
            try:
                await bot.send_message(
                    ad_data['user_id'],
                    "✅ **E'loningiz tasdiqlandi va kanalga joylashtirildi!** 🎉\n\n"
                    "📢 E'loningiz endi barcha foydalanuvchilarga ko'rinadi.\n"
                    "🤝 Yaxshi savdolar!",
                    parse_mode="Markdown"
                )
            except:
                pass
            
            await callback.message.edit_caption(
                f"{callback.message.caption}\n\n✅ **TASDIQLANDI!**",
                reply_markup=None,
                parse_mode="Markdown"
            )
            
            await callback.answer("✅ E'lon tasdiqlandi va kanalga jo'natildi!")
            
        except Exception as e:
            logger.error(f"Error sending to channel: {e}")
            await callback.answer("❌ Kanalga jo'natishda xatolik!")
    else:
        await callback.answer("❌ Kanal ID o'rnatilmagan!")
        await callback.message.edit_caption(
            f"{callback.message.caption}\n\n⚠️ **Kanal topilmadi!**",
            reply_markup=None,
            parse_mode="Markdown"
        )
    
    del dp.pending_ads[ad_id]

@dp.callback_query(F.data.startswith("reject_"))
async def reject_ad(callback: CallbackQuery):
    ad_id = int(callback.data.split("_")[1])
    
    if not hasattr(dp, 'pending_ads') or ad_id not in dp.pending_ads:
        await callback.answer("❌ E'lon topilmadi!")
        return
    
    ad_data = dp.pending_ads[ad_id]
    
    try:
        await bot.send_message(
            ad_data['user_id'],
            "❌ **E'loningiz rad etildi.**\n\n"
            "📌 Sababi: Admin tomonidan tekshiruvdan o'tmadi.\n"
            "💳 To'lov chekingiz tekshirilmadi yoki noto'g'ri.\n\n"
            "💡 Iltimos, e'loningizni qayta tekshirib ko'ring:\n"
            "• To'lov cheki to'g'rimi?\n"
            "• Rasm/video to'g'rimi?\n"
            "• Ma'lumotlar to'liqmi?\n\n"
            "Qayta e'lon berish uchun '📢 E'lon berish' tugmasini bosing.",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.message.edit_caption(
        f"{callback.message.caption}\n\n❌ **RAD ETILDI!**",
        reply_markup=None,
        parse_mode="Markdown"
    )
    
    await callback.answer("❌ E'lon rad etildi!")
    del dp.pending_ads[ad_id]

@dp.message(F.text == "📂 Mening e'lonlarim")
async def my_ads(message: Message):
    await message.answer(
        "📂 **Sizning e'lonlaringiz**\n\n"
        "📌 Hozircha e'lonlar mavjud emas.\n\n"
        "💡 E'lon berish uchun '📢 E'lon berish' tugmasini bosing.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "❓ Qo'llanma")
async def guide(message: Message):
    guide_text = (
        "📖 **QO'LLANMA**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 **Bot qanday ishlaydi?**\n"
        "Bot orqali siz eFootball akkauntlaringizni sotishingiz "
        "yoki boshqa foydalanuvchilardan sotib olishingiz mumkin.\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📢 **Qanday e'lon beriladi?**\n"
        "1️⃣ '📢 E'lon berish' tugmasini bosing\n"
        "2️⃣ Tarifni tanlang (1000 yoki 5000 so'm)\n"
        "3️⃣ To'lov chekini yuboring\n"
        "4️⃣ Akkaunt rasmini yuboring\n"
        "5️⃣ E'lon turini tanlang\n"
        "6️⃣ Platformani tanlang\n"
        "7️⃣ Overall ratingni kiriting\n"
        "8️⃣ Top playerlarni yozing\n"
        "9️⃣ Narxni kiriting\n"
        "🔟 Qo'shimcha ma'lumot (ixtiyoriy)\n"
        "1️⃣1️⃣ Admin tasdiqlaydi va kanalda chiqadi\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 **To'lov ma'lumotlari:**\n"
        "🏦 Karta: `9860166654505204`\n"
        "👤 Egasi: `Sunnatov_Shukurullo`\n"
        "📸 Chek yuborish majburiy!\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ **FAQ (Ko'p so'raladigan savollar)**\n"
        "• E'lon qancha vaqt kanalda qoladi? 7 kun\n"
        "• E'lonni o'chirish mumkinmi? Ha, admin yordamida\n"
        "• To'lov qaytariladimi? Yo'q, qaytarilmaydi\n"
        "• VIP e'lon nima? 30 kun, premium dizayn\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 **Admin bilan bog'lanish:** /admin\n\n"
        "⚽ **Yaxshi savdolar!**"
    )
    await message.answer(guide_text, parse_mode="Markdown", reply_markup=main_menu())

@dp.message(F.text == "💰 E'lon narxi")
async def ad_price(message: Message):
    price_text = (
        "💰 **E'LON NARXLARI**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📢 **ODDIY E'LON**\n"
        "💰 Narxi: 1000 so'm\n"
        "📅 7 kun kanalda\n"
        "📋 Standart ko'rinish\n\n"
        
        "⭐ **VIP E'LON**\n"
        "💰 Narxi: 5000 so'm\n"
        "📅 30 kun kanalda\n"
        "✨ Premium dizayn\n"
        "🔥 Yuqori ko'rinish\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "💳 **TO'LOV MA'LUMOTLARI**\n"
        "🏦 Karta: `9860166654505204`\n"
        "👤 Egasi: `Sunnatov_Shukurullo`\n\n"
        
        "📸 Chek yuborish orqali to'lovni tasdiqlang!\n\n"
        "📢 E'lon berish uchun '📢 E'lon berish' tugmasini bosing."
    )
    await message.answer(price_text, parse_mode="Markdown", reply_markup=main_menu())

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return
    
    pending_count = len(getattr(dp, 'pending_ads', {}))
    
    admin_text = (
        "👨‍💻 **ADMIN PANEL**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 **STATISTIKA**\n"
        f"⏳ Kutilayotgan e'lonlar: {pending_count}\n"
        f"👥 Foydalanuvchilar: 0\n"
        f"📢 Jami e'lonlar: 0\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔧 **BUYRUQLAR**\n"
        "• /stats - Statistika\n"
        "• /users - Foydalanuvchilar\n"
        "• /broadcast - Xabar yuborish"
    )
    await message.answer(admin_text, parse_mode="Markdown")

@dp.message(Command("stats"))
async def admin_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Faqat adminlar uchun!")
        return
    
    pending_count = len(getattr(dp, 'pending_ads', {}))
    
    stats = (
        "📊 **STATISTIKA**\n\n"
        f"⏳ Kutilayotgan e'lonlar: {pending_count}\n"
        f"👥 Foydalanuvchilar: 0\n"
        f"📢 E'lonlar: 0\n"
        f"💳 To'lovlar: 0"
    )
    await message.answer(stats, parse_mode="Markdown")

# ============ MAIN ============
async def main():
    logger.info("🚀 Bot ishga tushmoqda...")
    
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username}")
        
        if ADMIN_ID:
            logger.info(f"👑 Admin ID: {ADMIN_ID}")
        else:
            logger.warning("⚠️ ADMIN_ID o'rnatilmagan!")
        
        if CHANNEL_ID:
            logger.info(f"📢 Kanal ID: {CHANNEL_ID}")
        else:
            logger.warning("⚠️ CHANNEL_ID o'rnatilmagan!")
        
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")
        raise
    finally:
        await bot.session.close()
        logger.info("👋 Bot to'xtatildi")

if __name__ == "__main__":
    asyncio.run(main())