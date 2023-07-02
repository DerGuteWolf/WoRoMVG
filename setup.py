import io
import discord
from discord import client
from discord import ui
from discord.ext import commands,tasks
import discord.ext.commands 
import discord.utils

import time
import asyncio
from typing import Optional

from mvg import MvgApi

import googlemaps
from googlemaps.maps import StaticMapMarker
from googlemaps.maps import StaticMapPath

from datetime import datetime
from pytz import timezone

import os

gmaps_key = os.getenv('GMAPS_KEY')
bot_token = os.getenv('BOT_TOKEN')

berlin = timezone('Europe/Berlin')


gmaps = googlemaps.Client(key=gmaps_key)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

stations = []

@tasks.loop(seconds=30)
async def status_task():
    print('Status')
    await bot.change_presence(activity=discord.Game(name="Ersteller DerGuteWolf"))
    await asyncio.sleep(10)
    await bot.change_presence(activity=discord.Game(name="Abfrage z.B. $abfahrt 10 Pasing"))
    await asyncio.sleep(10)
    await bot.change_presence(activity=discord.Game(name="Oder Formular mit $abfahrtF"))



@bot.event
async def on_command_error(ctx, error):
    print(f'error: { error }')
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Nicht genügend Parameter')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('Keine Berechtigung')
    else:
        await ctx.send('Irgendwas ist schief gegangen')

class MVGFormular(ui.Modal, title='Abfrage von MVG Abfahrten'):
    station = ui.TextInput(label='Haltestelle', required=True)
    offset = ui.TextInput(label='Minuten bis zur Abfahrt', style=discord.TextStyle.short, required=False, default='0')

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        result = await abfahrt_interal(station=self.station.value, offset=int(self.offset.value) if self.offset.value.isdigit() else 0)
        if result == None:
            await interaction.followup.send(f'Die Haltestelle "{ self.station.value }" kenne ich nicht!', ephemeral=True)
            return
        await interaction.followup.send(file=result[0], embed=result[1])

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(f'error: { error }')
        #await interaction.response.send_message('Irgendwas ist schief gegangen', ephemeral=True)

class MVGFormularButton(ui.View):
    @ui.button(label='Zeige Formular zur Abfrage von MVG Abfahrten', style=discord.ButtonStyle.red)
    async def zeigeFormular(self, interaction: discord.Interaction, button: discord.ui.Button):
        formular = MVGFormular()
        await interaction.response.send_modal(formular)
        formular.message = await interaction.original_response()

@bot.command(description='Zeigt Formular mit Button zur Abfrage von MVG Abfahrten')
async def abfahrtF(ctx: commands.Context):
    view = MVGFormularButton()
    await ctx.send(view=view)    

@bot.command(description='Zeigt MVG Abfahrten')
async def abfahrt(ctx: commands.Context, offset: Optional[int], *, station: str):
    if offset == None:
        offset = 0
    print(f'abfahrt (offset { offset }): { station }')
    result = await abfahrt_interal(station=station, offset=offset)
    if result == None:
        await ctx.send(f'Die Haltestelle "{ station }" kenne ich nicht!')
        return
    await ctx.send(file=result[0], embed=result[1])

async def abfahrt_interal(station: str, offset: int):    
    stationInfo = await MvgApi.station_async(station)
    if stationInfo == None:        
        return
    global stations
    if len(stations) == 0:
      stations = await MvgApi.stations_async() 
    stationInfo = next(x for x in stations if x['id'] == stationInfo['id'])
    output = b''
    for chunk in gmaps.static_map(
        size=(400, 400),
        zoom=14,
        center=(stationInfo['latitude'], stationInfo['longitude']),
        maptype="roadmap",
        format="png"
    ):
        output += chunk
    file = discord.File(fp=io.BytesIO(output), filename='staticmap.png')
    departures = await MvgApi.departures_async(stationInfo['id'])
    embed = discord.Embed(description=f"Abfahrten von { stationInfo['name'] }:", colour = 0xFFB6C1)
    embed.set_image(url="attachment://staticmap.png")
    for departure in departures:
        embed.add_field(name=f"{ '{:%H:%M}'.format(datetime.fromtimestamp( departure['time']), tz=berlin ) }", value=f"{ departure['type'] } { departure['line'] } nach { departure['destination'] }", inline=True)
    return (file, embed)  

print("start")

@bot.event
async def on_ready():
    status_task.start()
    
bot.run(bot_token)

