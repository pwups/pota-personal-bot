import discord
from discord.ext import commands
from keep_alive import keep_alive
import os
from discord.ui import View, Button
from dotenv import load_dotenv
from datetime import date, timedelta
import json

# Load .env variables
load_dotenv()

# Load config.json
with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1319396490543890482
LAUGHBOARD_CHANNEL_ID = 1371776724269797397
TARGET_EMOJI = "😆"
THRESHOLD = 2
CHANNEL_ID = int(config["CHANNEL_ID"])

# XP and streak tracking
highest_score_hash = {}
current_score_hash = {}

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='p?', intents=intents)

RED = discord.Color.from_str("#ED5858")
WHITE = discord.Color.from_str("#FFFFFF")

# sticky_messages[channel_id] = {"text": str, "last_message": discord.Message}
sticky_messages = {}

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sticky(ctx, *, message: str):
    sticky_messages[ctx.channel.id] = {"text": message, "last_message": None}
    await ctx.send(f"sticky message set for this channel:\n> {message}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def removesticky(ctx):
    if ctx.channel.id in sticky_messages:
        last_msg = sticky_messages[ctx.channel.id].get("last_message")
        if last_msg:
            try:
                await last_msg.delete()
            except:
                pass
        del sticky_messages[ctx.channel.id]
        await ctx.send("sticky message removed from this channel!")
    else:
        await ctx.send("no sticky message is set for this channel")

@bot.command()
async def calc(ctx, *, expression: str):
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        await ctx.send(f"**`{result}`**")
    except Exception as e:
        await ctx.send(f"Error: `{e}`")

@bot.command()
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
async def currentstreak(ctx):
    user_id = str(ctx.author.id)
    if user_id in current_score_hash:
        await ctx.send(f"> <@{ctx.author.id}>'s current streak is **{current_score_hash[user_id][0]}** days <:003_:1371441152351404074>")
    else:
        await ctx.send("You don't have a streak yet.")

@bot.command()
async def personalbest(ctx):
    user_id = str(ctx.author.id)
    if user_id in highest_score_hash:
        await ctx.send(f"> <@{ctx.author.id}>'s highest streak is **{highest_score_hash[user_id][0]}** days <:tiktok_cool:1371440776483176550>")
    else:
        await ctx.send("You don't have a best streak yet.")

@bot.command()
async def lbstreak(ctx):
    sorted_scores = sorted(highest_score_hash.items(), key=lambda x: x[1][0], reverse=True)
    leaderboard_msg = ""
    counter = 1
    for user_id, (score, user) in sorted_scores:
        leaderboard_msg += f"{counter}. {user}: **{score}** days <:kassy:1372204371462455420>\n"
        counter += 1
    await ctx.send(leaderboard_msg)

@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        channel = discord.utils.get(after.guild.text_channels, name="－－mail")
        if channel:
            embed = discord.Embed(
                description=f"_ _\n_ _⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀﹒﹒ —  {after.mention}  ♡\n_ _⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀<:bow_red:1371440730597363715>  __boosted__ **/pota**\n_ _⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀` check `﹕⠀*[perks](https://discord.com/channels/1319396490543890482/1371318261509263460)*\n_ _",
                color=0xd63737
            )
            embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) != TARGET_EMOJI:
        return

    if payload.channel_id == LAUGHBOARD_CHANNEL_ID:
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    reaction = discord.utils.get(message.reactions, emoji=TARGET_EMOJI)
    if not reaction:
        return

    count = reaction.count

    laughboard_channel = guild.get_channel(LAUGHBOARD_CHANNEL_ID)
    if not laughboard_channel:
        return

    async for msg in laughboard_channel.history(limit=100):
        if msg.embeds and msg.embeds[0].timestamp == message.created_at:
            embed = msg.embeds[0]
            embed.set_footer(text=f"{count} {TARGET_EMOJI} reactions")
            await msg.edit(content=f"{count} {TARGET_EMOJI} reactions", embed=embed)
            return

    if count == THRESHOLD:
        embed = discord.Embed(
            description=message.content,
            color=WHITE,
            timestamp=message.created_at
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="jump to message", value=f"[click here ! !]({message.jump_url})", inline=False)
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await laughboard_channel.send(content=f"{THRESHOLD} {TARGET_EMOJI} reactions", embed=embed)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    # Sticky Message Logic
    data = sticky_messages.get(message.channel.id)
    if data:
        try:
            if data.get("last_message"):
                try:
                    await data["last_message"].delete()
                except:
                    pass
            new_msg = await message.channel.send(data["text"])
            sticky_messages[message.channel.id]["last_message"] = new_msg
        except discord.Forbidden:
            print(f"Missing permission to send sticky message in {message.channel.name}")

    # Streak Tracking Logic
    if message.channel.id == CHANNEL_ID:
        user = str(message.author)
        user_id = str(message.author.id)
        user_message = str(message.content)
        channel = str(message.channel.name)
        message_day = date.today()
        day_t = timedelta(1)
        yesterday_date = message_day - day_t
        print(f"{user_id}: {user_message} ({channel}) / {message_day}")

        if user_id not in highest_score_hash and user_id not in current_score_hash:
            highest_score_hash[user_id] = [1, user]
            current_score_hash[user_id] = [1, message_day]

        elif current_score_hash[user_id][1] == yesterday_date:
            current_score_hash[user_id][0] += 1
            current_score_hash[user_id][1] = message_day
            if highest_score_hash[user_id][0] <= current_score_hash[user_id][0]:
                highest_score_hash[user_id][0] = current_score_hash[user_id][0]
                highest_score_hash[user_id][1] = user

        elif (
            current_score_hash[user_id][1] != yesterday_date
            and current_score_hash[user_id][1] != date.today()
        ):
            if highest_score_hash[user_id][0] <= current_score_hash[user_id][0]:
                highest_score_hash[user_id][0] = current_score_hash[user_id][0]
                highest_score_hash[user_id][1] = user
            current_score_hash[user_id][0] = 1
            current_score_hash[user_id][1] = message_day

        print(f"highest {highest_score_hash}, current {current_score_hash}")

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="over /pota ୱଭ")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)
    print(f'Logged in as {bot.user.name}')

keep_alive()
bot.run(TOKEN)
