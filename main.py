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

@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        channel = discord.utils.get(after.guild.text_channels, name="boosts")
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
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------ Vanity Roles feature is active ------")
def _has_keyword(status: discord.CustomActivity | None, keyword: str) -> bool:
    return bool(status and status.name and keyword.lower() in status.name.lower())

@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    # Ignore other servers the bot might share
    if after.guild.id != GUILD_ID:
        return

    role = after.guild.get_role(VANITY_ROLE_ID)
    if role is None:
        return  # Role ID is wrong or bot can’t see the role

    # Find any CustomActivity (the "set a status" in Discord)
    before_status = next((a for a in before.activities if isinstance(a, discord.CustomActivity)), None)
    after_status = next((a for a in after.activities if isinstance(a, discord.CustomActivity)), None)

    had_keyword = _has_keyword(before_status, VANITY_KEYWORD)
    has_keyword_now = _has_keyword(after_status, VANITY_KEYWORD)

    channel = after.guild.get_channel(ANNOUNCE_CHANNEL_ID)

    # ✅ Keyword added ➜ give role
    if has_keyword_now and not had_keyword:
        if role not in after.roles:
            try:
                await after.add_roles(role, reason="User added vanity keyword to status")
            except discord.Forbidden:
                print("[VanityRoles] Missing permissions to add role.")
            else:
                if channel:
                    embed = discord.Embed(
                        title="Vanity Role Assigned",
                        description=f"_ _　　　{after.mention}﹒ *repped* **{VANITY_KEYWORD} *!***\n_ _　　 ⤹ 　thanks for the *support* <:kassy:1372204371462455420>\n-# _ _　　　　　 ﹒　[check our perks!](https://discord.com/channels/1319396490543890482/1371318261509263460) 　﹒　    ⟡​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​",
                        color=RED
                    )
                    await channel.send(embed=embed)

    # ❌ Keyword removed ➜ remove role
    elif had_keyword and not has_keyword_now:
        if role in after.roles:
            try:
                await after.remove_roles(role, reason="User removed vanity keyword from status")
            except discord.Forbidden:
                print("[VanityRoles] Missing permissions to remove role.")
            else:
                if channel:
                    embed = discord.Embed(
                        title="Vanity Role Removed",
                        description=f"_ _　　　{after.mention}﹒ *removed* **{VANITY_KEYWORD} from their status *!***​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​",
                        color=WHITE
                    )
                    await channel.send(embed=embed)

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="over /pota ৎ୭")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)
    print(f'Logged in as {bot.user.name}')

keep_alive()
bot.run(TOKEN)
