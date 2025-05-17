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

ICON_FORUM_IDS = [
    1371835079684263936, 1371834983466930226, 1371835187456905236,
    1371835024588144731, 1372211755824189511, 1371835574960263288,
    1371835441010966558, 1371835499043491912, 1371835679213883472,
    1371835626646929489
]
LAYOUT_FORUM_ID = 1371835736705466408

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
async def say(ctx, *, message: str):
    await ctx.message.delete()  # Delete the command message to keep it clean (optional)
    await ctx.send(message)

@bot.command()
async def uploads(ctx):
    user = ctx.author
    guild = ctx.guild

    total_attachments = 0
    total_layouts = 0
    total_removed_uploads = deleted_uploads.get(user.id, 0)

    async def count_uploads_in_thread(thread):
    attachments = 0
    layouts = 0
    try:
        await thread.join()  # <-- Ensure the bot can read messages
        async for msg in thread.history(limit=None):
            if msg.author.id == user.id:
                attachments += len(msg.attachments)
                if "```" in msg.content:
                    layouts += 1
    except discord.Forbidden:
        pass
    return attachments, layouts

    for forum_id in ICON_FORUM_IDS:
        forum = guild.get_channel(forum_id)
        if forum:
            threads = [t async for t in forum.threads()]
            for thread in threads:
                att, _ = await count_uploads_in_thread(thread)
                total_attachments += att

    layout_forum = guild.get_channel(LAYOUT_FORUM_ID)
    if layout_forum:
        threads = await layout_forum.active_threads()
        for thread in threads:
            _, lo = await count_uploads_in_thread(thread)
            total_layouts += lo

    embed = discord.Embed(
        description=f"_ _\n             <a:01charmzheart:1371440749341839432>  **you have a total of:**  ⁺ ˖˚\n_ _         * ✦．  **{total_attachments}** icons uploaded  <a:redpurse:1371482936041279641>\n_ _          <:bow_red:1371440730597363715> **{total_layouts}** layouts uploaded  ︵ ｡˚  \n_ _         ◞⁺⊹．  **{total_removed_uploads}** deleted uploads  <a:01_redangry:1371440736238829711>\n-# _ _                 <a:010sparkle:1371482938373443695>  take breaks whenever, love\n_ _",
        color=RED,
        timestamp=discord.utils.utcnow()
    )
    embed.set_author(name=user.name, icon_url=guild.icon.url if guild.icon else None)
    embed.set_footer(text="your upload stats")
    await ctx.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.guild is None or message.author.bot:
        return

    has_attachment = len(message.attachments) > 0
    is_layout = "```" in message.content

    if has_attachment or is_layout:
        deleted_uploads[message.author.id] = deleted_uploads.get(message.author.id, 0) + 1

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
