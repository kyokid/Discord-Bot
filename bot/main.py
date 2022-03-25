import discord
import os
#import pynacl
#import dnspython
import server
from discord.ext import commands
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from requests import Session

bot = commands.Bot(command_prefix="$")
TOKEN = os.getenv("DISCORD_TOKEN")
base_img_url = 'https://s2.coinmarketcap.com/static/img/coins/64x64/'

@bot.command()
async def ping(ctx):
  await ctx.channel.send('pong')

# getting crypto data
def get_info(crypto):
  url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?convert=USD'
  parameters = {
    'symbol':f'{crypto}'
  }
  headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '395c0c64-1cb3-49cf-91c5-d2248c85b801',
  }
  session = Session()
  session.headers.update(headers)

  try:
    response = session.get(url, params=parameters)
    data = json.loads(response.text)
    coins_data = data['data']
    coin_data = next((data for data in coins_data if data['symbol'] == crypto.upper()), None)
    quote_usd = coin_data['quote']['USD']
    image_url = base_img_url + coin_data['id'] + '.png'
    d = dict()
    d[crypto] = round(quote_usd['price'], 4)
    d['name'] = coin_data['name']
    d['img_url'] = image_url
    d['mkc'] = quote_usd['market_cap']
    d['fdv'] = quote_usd['fully_diluted_market_cap']
    d['percent_change_1h'] = quote_usd['percent_change_1h']
    d['percent_change_24h'] = quote_usd['percent_change_24h']
    d['percent_change_7d'] = quote_usd['percent_change_7d']
    return d
  except (ConnectionError, Timeout, TooManyRedirects) as e:
    print(e)
  

def check(price_targets):
  try:
    return all(isinstance(int(x), int) for x in price_targets)
  except:
    return False

def get_price(crypto):
  d = get_info(crypto)
  return d[crypto]

def predict_base(coin, base = 'sol'):
  d_sol = get_info(base)
  d_coin = get_info(coin)
  current_price = d_coin[coin]
  market_cap = d_coin['mkc']
  fdv = d_coin['fdv']

  sol_mkc = d_sol['mkc']
  sol_fdv = d_sol['fdv']

  price = round((sol_mkc / market_cap) * current_price, 2)
  fdv_price = round((sol_fdv / fdv) * current_price, 2) if fdv != 0 else None
  return price, fdv_price

def predict_cap(coin):
  d = get_info(coin)
  current_price = d[coin]
  market_cap = d['mkc']
  fdv = d['fdv']

  price = round((1_000_000_000 / market_cap) * current_price, 2)
  price_500_cap = price / 2
  price_200_cap = price / 5
  price_100_cap = price_200_cap / 2
  price_50_cap = price_100_cap / 2
  fdv_price = round((2_000_000_000 / fdv) * current_price, 2)

  return price, fdv_price, price_500_cap, price_200_cap, price_100_cap, price_50_cap


# send discord message
async def send_message(message):
  await discord.utils.get(bot.get_all_channels(), name='channel-này-để-hold').send(message)

@bot.event
async def on_ready():
  print(f'You have logged in as {bot.user.name}({bot.user.id})')

@bot.command()
async def price(ctx, coin):
  coin_data = get_info(coin)
  
  embed = discord.Embed(title='Price from CoinMarketCap', colour = discord.Colour.blue())
  embed.set_author(name=coin_data['name'], url="https://coinmarketcap.com/currencies/bitcoin", icon_url=coin_data['img_url'])
  embed.add_field(name=coin, value=f'{get_price(coin)} USD')
  await ctx.channel.send(embed=embed)
#@bot.event
#async def on_message(message):
#  if message.author == bot.user:
#    return
#  if message.content.startswith('$price '):
#    crypto_to_be_checked = message.content.split('$price ', 1)[1].lower()
#    await message.channel.send(f'The current price of {crypto_to_be_checked} is {get_price(crypto_to_be_checked)} USD')
#
#  if message.content.startswith('$predict '):
#    content = message.content.split(' ')
#    crypto_to_be_checked = content[1].lower()
#    if (len(content) == 3):
#      price, fdv_price = predict_base(crypto_to_be_checked, content[2].lower())
#    else:
#      price, fdv_price = predict_base(crypto_to_be_checked)
#    
#    await message.channel.send(f'The predict for price of {crypto_to_be_checked} is {price} USD and FDV price is #{fdv_price}')
#
#  if message.content.startswith('$predict_low '):
#    content = message.content.split(' ')
#    crypto_to_be_checked = content[1].lower()
#    price, fdv_price, price_500_cap, price_200_cap, price_100_cap, price_50_cap = predict_cap(crypto_to_be_checked)
#    
#    await message.channel.send(f'\nPrediction for {crypto_to_be_checked}: \n- 1B Cap: {price} USD\n- 500M Cap: {price_500_cap} USD\n- 200M Cap: {price_200_cap} USD\n- 100M Cap: {price_100_cap} USD\n- 50M Cap: {price_50_cap} USD \n- FDV: {fdv_price} USD')

server.server()
bot.run(TOKEN)
