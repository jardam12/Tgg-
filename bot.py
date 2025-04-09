import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import requests

API_TOKEN = '7920883534:AAH1RWCQdX64euCbyX5bvbD2K8PEUu-B4vM'
META_ACCESS_TOKEN = 'EAAGZC...REPLACE_THIS...ZDZD'
AD_ACCOUNT_ID = 'act_123456789012345'
PAGE_ID = '123456789012345'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_data = {}

main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Запустить рекламу"))

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я помогу запустить рекламу в Instagram. Нажми 'Запустить рекламу'.", reply_markup=main_kb)

@dp.message_handler(lambda msg: msg.text == "Запустить рекламу")
async def ask_link(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Введи ссылку, куда вести трафик:")

@dp.message_handler(lambda msg: 'http' in msg.text)
async def ask_budget(message: types.Message):
    user_data[message.from_user.id]['link'] = message.text
    await message.answer("Укажи бюджет в $:")

@dp.message_handler(lambda msg: msg.text.isdigit())
async def ask_gender(message: types.Message):
    user_data[message.from_user.id]['budget'] = int(message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Мужчины"), KeyboardButton("Женщины"), KeyboardButton("Все"))
    await message.answer("Выбери пол аудитории:", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in ["Мужчины", "Женщины", "Все"])
async def ask_age(message: types.Message):
    user_data[message.from_user.id]['gender'] = message.text
    await message.answer("Укажи возраст (например: 18-35):")

@dp.message_handler(lambda msg: '-' in msg.text and msg.text.replace('-', '').isdigit())
async def ask_country(message: types.Message):
    user_data[message.from_user.id]['age'] = message.text
    await message.answer("Укажи страну (например: Uzbekistan):")

@dp.message_handler(lambda msg: len(msg.text) >= 2)
async def launch_ad(message: types.Message):
    data = user_data.get(message.from_user.id, {})
    data['country'] = message.text

    try:
        headers = {
            'Authorization': f'Bearer {META_ACCESS_TOKEN}'
        }

        campaign_payload = {
            'name': 'Auto Campaign from Bot',
            'objective': 'LINK_CLICKS',
            'status': 'PAUSED',
            'special_ad_categories': []
        }
        campaign_resp = requests.post(f'https://graph.facebook.com/v18.0/{AD_ACCOUNT_ID}/campaigns',
                                      headers=headers, data=campaign_payload)
        campaign_id = campaign_resp.json().get('id')

        adset_payload = {
            'name': 'Auto Ad Set',
            'campaign_id': campaign_id,
            'daily_budget': int(data['budget']) * 100,
            'billing_event': 'IMPRESSIONS',
            'optimization_goal': 'LINK_CLICKS',
            'targeting': '{"geo_locations":{"countries":["' + data['country'] + '"]}, "age_min":' + data['age'].split('-')[0] + ', "age_max":' + data['age'].split('-')[1] + '}',
            'status': 'PAUSED'
        }
        adset_resp = requests.post(f'https://graph.facebook.com/v18.0/{AD_ACCOUNT_ID}/adsets',
                                   headers=headers, data=adset_payload)
        adset_id = adset_resp.json().get('id')

        creative_payload = {
            'name': 'Bot Creative',
            'object_story_spec': '{"link_data":{"link":"' + data['link'] + '","message":"Реклама от бота"},"page_id":"' + PAGE_ID + '"}'
        }
        creative_resp = requests.post(f'https://graph.facebook.com/v18.0/{AD_ACCOUNT_ID}/adcreatives',
                                      headers=headers, data=creative_payload)
        creative_id = creative_resp.json().get('id')

        ad_payload = {
            'name': 'Auto Ad',
            'adset_id': adset_id,
            'creative': '{"creative_id":"' + creative_id + '"}',
            'status': 'PAUSED'
        }
        ad_resp = requests.post(f'https://graph.facebook.com/v18.0/{AD_ACCOUNT_ID}/ads',
                                headers=headers, data=ad_payload)
        ad_id = ad_resp.json().get('id')

        await message.answer(f"Реклама создана!\nКампания: {campaign_id}\nAdSet: {adset_id}\nОбъявление: {ad_id}")
    except Exception as e:
        await message.answer(f"Ошибка запуска рекламы: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
