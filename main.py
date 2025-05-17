import discord
from discord.ext import commands
from keep_alive import keep_alive
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1319396490543890482
VANITY_ROLE_ID = 1372213876887781487
ANNOUNCE_CHANNEL_ID = 1372210728378957865
VANITY_KEYWORD = "/pota"

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='p?', intents=intents)

ICON_FORUM_IDS = [1371687868690337843, 1371688017785258056]
LAYOUT_FORUM_ID = 1371835736705466408

upload_data = {
    "attachments": 0,
    "layouts": 0,
    "deleted_attachments": 0,
    "deleted_layouts": 0
}

# Store deleted uploads (in-memory)
deleted_uploads = {}

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
        # Delete last sticky message if it exists
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
async def uploads(ctx):
    embed = discord.Embed(
        title="Uploader Stats",
        description=(
            f"<a:01charmzheart:1371440749341839432> **total uploads**  ⁺ ˖˚\n"
            f"- imgs: `{upload_data['attachments']}`\n"
            f"- layouts: `{upload_data['layouts']}`\n\n"
            f"**<a:redpurse:1371482936041279641> **deleted uploads**  ◞⁺ ⊹．\n"
            f"- imgs: `{upload_data['deleted_attachments']}`\n"
            f"- layouts: `{upload_data['deleted_layouts']}`"
        ),
        color=RED,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed.set_footer(text="your upload stats")
    await ctx.send(embed=embed)
    except Exception as e:
           await ctx.send(f"Error: {e}")

@bot.command()
async def say(ctx, *, message: str):
    await ctx.message.delete()  # Delete the command message to keep it clean (optional)
    await ctx.send(message)

@bot.event
async def on_message(message):
    if message.channel.id in ICON_FORUM_IDS:
        if message.attachments:
            upload_data["attachments"] += 1
    elif message.channel.id == LAYOUT_FORUM_ID:
        if "```" in message.content:
            upload_data["layouts"] += 1
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.channel.id in ICON_FORUM_IDS:
        if message.attachments:
            upload_data["deleted_attachments"] += 1
    elif message.channel.id == LAYOUT_FORUM_ID:
        if "```" in message.content:
            upload_data["deleted_layouts"] += 1

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
            # Delete previous sticky message
            if data.get("last_message"):
                try:
                    await data["last_message"].delete()
                except:
                    pass
            # Send new sticky and save the message object
            new_msg = await message.channel.send(data["text"])
            sticky_messages[message.channel.id]["last_message"] = new_msg
        except discord.Forbidden:
            print(f"missing permission to send sticky message in {message.channel.name}")

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="over /pota ৎ୭")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)
    print(f'Logged in as {bot.user.name}')

keep_alive()
bot.run(TOKEN)
