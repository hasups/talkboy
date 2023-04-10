#by hasups@gmail.com 2023.04.04

import logging
import os
from flask import Flask, request
import openai
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
import json
import requests
from libretranslatepy import LibreTranslateAPI

import io
import random
from PIL import Image, PngImagePlugin
import base64

openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
sd_url = os.getenv("STABLE_DIFFUSION_URL")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)



app = Flask(__name__)

# Set route /callback with POST method will trigger this method.
@app.route('/callback', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'



bot = telegram.Bot(token=telegram_bot_token)
lt = LibreTranslateAPI("https://translate.argosopentech.com/")

def bot_chat(bot, update):
    out = openai.ChatCompletion.create(
        model ="gpt-3.5-turbo",
        messages=[{"role": "user", "content": update.message.text}],
        max_tokens=256,
        temperature=0.7
    )
    bot.send_message(chat_id=update.message.chat_id, text=out['choices'][0]['message']['content'].strip())


def bot_help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="/ai, /image, /tr, /fact, /fc, /help")


def ai_chat(bot, update, args):
    prompt_in = ' '.join(args)
    out = openai.ChatCompletion.create(
        model ="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_in}],
        max_tokens=256,
        temperature=0.7
    )
    bot.send_message(chat_id=update.message.chat_id, text=out['choices'][0]['message']['content'].strip())


def ai_image(bot, update, args):
    prompt_in = ' '.join(args)
    message = lt.translate(prompt_in, lt.detect(prompt_in)[0]['language'], 'en')
    out = openai.Image.create(
      prompt = message,
      n=1,
      size="512x512",
      response_format="url"
    )
    json_object = json.loads(str(out))
    bot.send_photo(chat_id=update.message.chat_id, photo=json_object['data'][0]['url'], caption=message)


def draw(bot, update, args):
    prompt_in = ' '.join(args)
    update.message.reply_text("Please Wait 10-15 Second")

    payload = {
        "prompt": prompt_in,
        "steps": 50,
        "save_images": True
    }
    #request = requests.post(url=f'{sd_url}/sdapi/v1/txt2img', json=payload)
    #r = request.json()
    update.message.reply_text(f'Done: {prompt_in}')
'''
    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

    tmp = f"/tmp/.{update.message.from_user.id}.png"
    image.save(tmp)
    bot.send_photo(chat_id=update.message.chat_id, photo=tmp, caption=prompt_in)
    os.remove(tmp)
'''


def bot_trans(bot, update, args):
    if len(args)==0:
        bot.send_message(chat_id=update.message.chat_id, text="/tr ko|en|vi|jp|zh|... text...")
    else:
        prompt_in = ' '.join(args[1:])
        message = lt.translate(prompt_in, lt.detect(prompt_in)[0]['language'], args[0])
        bot.send_message(chat_id=update.message.chat_id, text=message)


def fortune(bot, update):
    out = requests.get("http://yerkee.com/api/fortune")
    bot.send_message(chat_id=update.message.chat_id, text=out.json()['fortune'])


def fact(bot, update):
    out = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random", params={"language": "en"})
    bot.send_message(chat_id=update.message.chat_id, text=out.json()['text'])


dispatcher = Dispatcher(bot, None)
dispatcher.add_handler(MessageHandler(Filters.text, bot_chat))
dispatcher.add_handler(CommandHandler('help', bot_help))
dispatcher.add_handler(CommandHandler('ai', ai_chat, pass_args=True))
dispatcher.add_handler(CommandHandler('image', ai_image, pass_args=True))
dispatcher.add_handler(CommandHandler('draw', draw, pass_args=True))
dispatcher.add_handler(CommandHandler('tr', bot_trans, pass_args=True))
dispatcher.add_handler(CommandHandler('fc', fortune))
dispatcher.add_handler(CommandHandler('fact', fact))



if __name__ == "__main__":
    # Running server
    app.run(debug=True)
