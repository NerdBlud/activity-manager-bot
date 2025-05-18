import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime, timedelta
import os
import asyncio
import dotenv

dotenv.load_dotenv()

CONFIG_FILE = "config.json"
ACTIVITY_DATA_FILE = "activity_data.json"

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

def load_activity_data():
    if not os.path.exists(ACTIVITY_DATA_FILE):
        with open(ACTIVITY_DATA_FILE, "w") as f:
            json.dump({"last_check": 0}, f)
    with open(ACTIVITY_DATA_FILE, "r") as f:
        return json.load(f)

def increment_activity_check():
    data = load_activity_data()
    data["last_check"] += 1
    with open(ACTIVITY_DATA_FILE, "w") as f:
        json.dump(data, f)
    return data["last_check"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(e)

async def send_activity_check(author, guild, channel):
    check_number = increment_activity_check()
    now = datetime.utcnow()
    deadline = now + timedelta(days=2)
    timestamp = int(deadline.timestamp())
    embed = discord.Embed(
        title=f"<:reaper:1274745507389898773> Activity Check #{check_number}",
        description=(
            f"## 🕰️ Time Left: <t:{timestamp}:R>\n"
            f"## 📈 Goal: 10+\n"
            f"## ⁉️ Punishment:\n"
            f"- **Not clicking to this activity check <t:{timestamp}:R> will result in you getting either warned, kicked, or even banned for inactivity reasons. Glory to {config['server_name']}.**"
        ),
        color=discord.Color.red()
    )
    avatar_url = author.avatar.url if author.avatar else author.default_avatar.url
    embed.set_footer(text=f"Posted by {author}", icon_url=avatar_url)
    message = await channel.send("||@everyone||", embed=embed)
    await message.add_reaction("\u2705")
    failed_dms = []
    async for member in guild.fetch_members(limit=None):
        if member.bot:
            continue
        try:
            await member.send(
                f"📢 **Activity Check Alert #{check_number}!**\n"
                f"Please check the activity announcement in {channel.mention} on **{config['server_name']}**!\n"
                f"Deadline: <t:{timestamp}:R>"
            )
            await asyncio.sleep(1)
        except discord.Forbidden:
            failed_dms.append(str(member))
        except Exception as e:
            print(f"Failed to DM {member.name}: {e}")
    return failed_dms

async def send_dead_chat_ping(author, guild, channel):
    now = datetime.utcnow()
    timestamp = int((now + timedelta(days=1)).timestamp())
    embed = discord.Embed(
        title="☠️ Dead Chat Alert!",
        description=(
            f"## 🔔 <t:{timestamp}:R> until activity review\n"
            f"### Hey everyone, let's bring this chat back to life!\n\n"
            f"📣 **Why be active?**\n"
            f"- Level up with roles\n"
            f"- Special permissions & events\n"
            f"- Recognition from staff\n\n"
            f"📝 Stay active or risk being marked as inactive.\n"
            f"Let’s revive the server — your next message could help spark it! 💬"
        ),
        color=discord.Color.orange()
    )
    avatar_url = author.avatar.url if author.avatar else author.default_avatar.url
    embed.set_footer(text=f"Initiated by {author}", icon_url=avatar_url)
    message = await channel.send("||@everyone||", embed=embed)
    failed_dms = []
    async for member in guild.fetch_members(limit=None):
        if member.bot:
            continue
        try:
            await member.send(
                f"👋 Hey there!\n\n"
                f"Our chat in **{guild.name}** is feeling a bit quiet.\n"
                f"Now’s your chance to shine: talk, hang out, and get perks for activity!\n"
                f"You might unlock special roles, event access, or even mod favor.\n\n"
                f"Join us in {channel.mention} and make some noise! 🗣️"
            )
            await asyncio.sleep(1)
        except discord.Forbidden:
            failed_dms.append(str(member))
        except Exception as e:
            print(f"Failed to DM {member.name}: {e}")
    return failed_dms

@app_commands.command(name="help", description="Displays all available commands.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Activity Manager Bot Commands",
        description="Here are all the commands you can use with the Activity Manager Bot! 🎉",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    embed.set_image(url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fmedia.tenor.com%2F-Rq8B_yGAmsAAAAC%2Fanime-girl-red-eyes.gif")
    embed.add_field(name="📋 /help", value="Shows this help message (slash).", inline=False)
    embed.add_field(name="📃 !help", value="Shows this help message (prefix).", inline=False)
    embed.add_field(name="📢 /activity", value="Launch an activity check (slash).", inline=False)
    embed.add_field(name="📣 !activity", value="Launch an activity check (prefix).", inline=False)
    embed.add_field(name="☠️ /deadchat", value="Ping and DM for dead chat revival (slash).", inline=False)
    embed.add_field(name="💀 !deadchat", value="Ping and DM for dead chat revival (prefix).", inline=False)
    avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
    embed.set_footer(text=f"Requested by {interaction.user}", icon_url=avatar_url)
    await interaction.response.send_message(embed=embed)

@app_commands.command(name="activity", description="Sends an activity check message and DMs members.")
async def slash_activity(interaction: discord.Interaction):
    allowed_roles = config["allowed_roles"]
    has_role = any(role.id in allowed_roles for role in interaction.user.roles)
    if not has_role:
        await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)
        return
    guild = bot.get_guild(config["server_id"])
    channel = guild.get_channel(config["activity_channel_id"])
    failed_dms = await send_activity_check(interaction.user, guild, channel)
    response = "✅ Activity check posted and DMs sent!"
    if failed_dms:
        response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
    await interaction.response.send_message(response, ephemeral=True)

@app_commands.command(name="deadchat", description="Pings the dead chat and DMs members to encourage activity.")
async def slash_deadchat(interaction: discord.Interaction):
    allowed_roles = config["allowed_roles"]
    has_role = any(role.id in allowed_roles for role in interaction.user.roles)
    if not has_role:
        await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)
        return
    guild = bot.get_guild(config["server_id"])
    channel = guild.get_channel(config["dead_chat_channel_id"])
    failed_dms = await send_dead_chat_ping(interaction.user, guild, channel)
    response = "📣 Dead chat ping sent and DMs delivered!"
    if failed_dms:
        response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
    await interaction.response.send_message(response, ephemeral=True)

@bot.command(name="help", description="Displays all available commands.")
async def prefix_help(ctx):
    embed = discord.Embed(
        title="📜 Activity Manager Bot Commands",
        description="Here are all the commands you can use with the Activity Manager Bot! 🎉",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    embed.set_image(url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fmedia.tenor.com%2F-Rq8B_yGAmsAAAAC%2Fanime-girl-red-eyes.gif")
    embed.add_field(name="📃 /help", value="Shows this help message (slash).", inline=False)
    embed.add_field(name="📃 !help", value="Shows this help message (prefix).", inline=False)
    embed.add_field(name="📢 /activity", value="Launch an activity check (slash).", inline=False)
    embed.add_field(name="📣 !activity", value="Launch an activity check (prefix).", inline=False)
    embed.add_field(name="☠️ /deadchat", value="Ping and DM for dead chat revival (slash).", inline=False)
    embed.add_field(name="💀 !deadchat", value="Ping and DM for dead chat revival (prefix).", inline=False)
    avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=avatar_url)
    await ctx.send(embed=embed)

@bot.command(name="activity", description="Sends an activity check message and DMs members.")
async def prefix_activity(ctx):
    allowed_roles = config["allowed_roles"]
    has_role = any(role.id in allowed_roles for role in ctx.author.roles)
    if not has_role:
        await ctx.send("🚫 You don't have permission to use this command!")
        return
    guild = bot.get_guild(config["server_id"])
    channel = guild.get_channel(config["activity_channel_id"])
    failed_dms = await send_activity_check(ctx.author, guild, channel)
    response = "✅ Activity check posted and DMs sent!"
    if failed_dms:
        response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
    await ctx.send(response)

@bot.command(name="deadchat", description="Pings the dead chat and DMs members to encourage activity.")
async def prefix_deadchat(ctx):
    allowed_roles = config["allowed_roles"]
    has_role = any(role.id in allowed_roles for role in ctx.author.roles)
    if not has_role:
        await ctx.send("🚫 You don't have permission to use this command!")
        return
    guild = bot.get_guild(config["server_id"])
    channel = guild.get_channel(config["dead_chat_channel_id"])
    failed_dms = await send_dead_chat_ping(ctx.author, guild, channel)
    response = "📣 Dead chat ping sent and DMs delivered!"
    if failed_dms:
        response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
    await ctx.send(response)

bot.tree.add_command(slash_help)
bot.tree.add_command(slash_activity)
bot.tree.add_command(slash_deadchat)
bot.run(os.getenv("TOKEN"))
