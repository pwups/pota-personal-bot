import discord
from discord.ext import commands, pages
from keep_alive import keep_alive
import os
import json
from discord.ui import View, Button
import aiofiles
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

def load_levels():
    with open("levels.json", "r") as f:
        return json.load(f)

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1319396490543890482
laughboard_data = {}  # {original_message_id: laughboard_message_id}
LAUGHBOARD_CHANNEL_ID = 1371776724269797397
TARGET_EMOJI = "😆"
THRESHOLD = 2

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

XP_FILE = "xp_data.json"
if not os.path.exists(XP_FILE):
    with open(XP_FILE, "w") as f:
        json.dump({}, f)

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
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = await get_user_data(member.id, ctx.guild.id)
    path = await generate_card(member, data)

    file = discord.File(path, filename="rank.png")
    await ctx.send(file=file)
    os.remove(path)

@bot.command()
async def leaderboard(ctx):
    data = load_levels()
    if not data:
        return await ctx.send("> <:00_warning:1373921609601126441> no level data found.")

    # Sort by XP descending
    sorted_data = sorted(data.items(), key=lambda x: x[1]["xp"], reverse=True)
    entries_per_page = 10
    total_pages = (len(sorted_data) + entries_per_page - 1) // entries_per_page

    async def generate_embed(page):
        start = page * entries_per_page
        end = start + entries_per_page
        embed = discord.Embed(title="level leaderboard <a:1G4_star_red:1372168764392476693>", color=WHITE)
        for index, (user_id, stats) in enumerate(sorted_data[start:end], start=start + 1):
            user = ctx.guild.get_member(int(user_id))
            name = user.display_name if user else f"User ID {user_id}"
            embed.add_field(
                name=f"{index}. {name}",
                value=f"Level: {stats['level']} | XP: {stats['xp']}",
                inline=False
            )
        embed.set_footer(text=f"page {page + 1}/{total_pages}")
        return embed

    class LeaderboardView(View):
        def __init__(self):
            super().__init__(timeout=60)
            self.page = 0

        @discord.ui.button(label="previous", style=discord.ButtonStyle.red)
        async def previous(self, interaction: discord.Interaction, button: Button):
            if self.page > 0:
                self.page -= 1
                await interaction.response.edit_message(embed=await generate_embed(self.page), view=self)

        @discord.ui.button(label="next", style=discord.ButtonStyle.green)
        async def next(self, interaction: discord.Interaction, button: Button):
            if self.page < total_pages - 1:
                self.page += 1
                await interaction.response.edit_message(embed=await generate_embed(self.page), view=self)

    view = LeaderboardView()
    await ctx.send(embed=await generate_embed(0), view=view)

@bot.command()
async def leaderboard(ctx):
    try:
        with open("levels.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return await ctx.send("> <:00_warning:1373921609601126441> no xp data found.")

    # Sort users by XP
    sorted_users = sorted(data.items(), key=lambda x: x[1].get("xp", 0), reverse=True)

    entries = []
    for index, (user_id, stats) in enumerate(sorted_users):
        user = ctx.guild.get_member(int(user_id))
        name = user.name if user else f"<Unknown User {user_id}>"
        entries.append(f"{index+1}. {name} — {stats.get('xp', 0)} XP, Level {stats.get('level', 0)}")

    # Paginate with 10 entries per page
    pages_list = []
    for i in range(0, len(entries), 10):
        embed = discord.Embed(
            title="level leaderboard <a:1G4_star_red:1372168764392476693>",
            description="\n".join(entries[i:i+10]),
            color=RED
        )
        embed.set_footer(text=f"page {i // 10 + 1}/{(len(entries) - 1) // 10 + 1}")
        pages_list.append(embed)

    paginator = pages.Paginator(pages=pages_list, timeout=60.0)
    await paginator.respond(ctx.interaction if hasattr(ctx, "interaction") else ctx)

@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        channel = discord.utils.get(after.guild.text_channels, name="﹒mail")
        if channel:
            embed = discord.Embed(
                description=f"_ _\n_ _⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀﹒﹒ —  {after.mention}  ♡\n_ _⠀⠀⠀⠀⠀⠀⠀⠀⠀ <:bow_red:1371440730597363715>  __boosted__ **/pota**\n_ _⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀` check `﹕⠀*[perks](https://discord.com/channels/1319396490543890482/1371318261509263460)*\n_ _",
                color=0xd63737
            )
            embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return

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
            print(f"missing permission to send sticky message in {message.channel.name}")

    await add_xp(message.author.id, message.guild.id, 10)

@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) != "😆":
        return

    if payload.channel_id == 1371776724269797397:
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    reaction = discord.utils.get(message.reactions, emoji="😆")
    if not reaction:
        return

    count = reaction.count

    laughboard_channel = guild.get_channel(1371776724269797397)
    if not laughboard_channel:
        return

    async for msg in laughboard_channel.history(limit=100):
        if msg.embeds and msg.embeds[0].timestamp == message.created_at:
            embed = msg.embeds[0]
            embed.set_footer(text=f"{count} 😆 reactions")
            await msg.edit(content=f"{count} 😆 reactions", embed=embed)
            return

    if count == 2:
        embed = discord.Embed(
            description=message.content,
            color=WHITE,
            timestamp=message.created_at
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="jump to message", value=f"[click here ! !]({message.jump_url})", inline=False)
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await laughboard_channel.send(content="2 😆 reactions", embed=embed)

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="over /pota ৎ୭")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)
    print(f'Logged in as {bot.user.name}')

async def add_xp(user_id, guild_id, amount):
    async with aiofiles.open(XP_FILE, "r") as f:
        data = json.loads(await f.read())

    key = f"{guild_id}-{user_id}"
    user_data = data.get(key, {"xp": 0, "level": 1})
    user_data["xp"] += amount

    next_level_xp = user_data["level"] * 100
    if user_data["xp"] >= next_level_xp:
        user_data["xp"] -= next_level_xp
        user_data["level"] += 1

    data[key] = user_data

    async with aiofiles.open(XP_FILE, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return user_data

async def get_user_data(user_id, guild_id):
    async with aiofiles.open(XP_FILE, "r") as f:
        data = json.loads(await f.read())
    return data.get(f"{guild_id}-{user_id}", {"xp": 0, "level": 1})

async def generate_card(user, user_data):
    width, height = 600, 180
    card = Image.new("RGB", (width, height), "#1e1e1e")
    draw = ImageDraw.Draw(card)

    font = ImageFont.load_default()

    bar_xp = user_data["xp"]
    next_level_xp = user_data["level"] * 100
    bar_length = int((bar_xp / next_level_xp) * 400)

    draw.rectangle((150, 100, 150 + 400, 130), fill="#444")
    draw.rectangle((150, 100, 150 + bar_length, 130), fill="#00ff99")

    draw.text((150, 50), f"{user.name}", font=font, fill="white")
    draw.text((150, 140), f"Level {user_data['level']} | XP: {bar_xp}/{next_level_xp}", font=font, fill="white")

    avatar = user.avatar
    if avatar:
        avatar_bytes = await avatar.read()
        with open("temp_avatar.png", "wb") as f:
            f.write(avatar_bytes)
        pfp = Image.open("temp_avatar.png").resize((100, 100))
        card.paste(pfp, (30, 40))

    path = f"rankcard_{user.id}.png"
    card.save(path)
    return path

keep_alive()
bot.run(TOKEN)
