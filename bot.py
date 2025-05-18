import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime, timedelta
import os
import asyncio
import dotenv
import random

dotenv.load_dotenv()

CONFIG_FILE = "config.json"
ACTIVITY_DATA_FILE = "activity_data.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file {CONFIG_FILE} not found")
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def load_activity_data():
    if not os.path.exists(ACTIVITY_DATA_FILE):
        with open(ACTIVITY_DATA_FILE, "w") as f:
            json.dump({"last_check": 0, "dead_chat_pings": 0}, f)
    with open(ACTIVITY_DATA_FILE, "r") as f:
        return json.load(f)

def increment_activity_check():
    data = load_activity_data()
    data["last_check"] += 1
    with open(ACTIVITY_DATA_FILE, "w") as f:
        json.dump(data, f)
    return data["last_check"]

def increment_dead_chat_pings():
    data = load_activity_data()
    data["dead_chat_pings"] += 1
    with open(ACTIVITY_DATA_FILE, "w") as f:
        json.dump(data, f)
    return data["dead_chat_pings"]

config = load_config()

# Convert string IDs to integers for Discord.py
SERVER_ID = int(config["server_id"])
ACTIVITY_CHANNEL_ID = int(config["activity_channel_id"])
DEAD_CHAT_CHANNEL_ID = int(config["dead_chat_channel_id"])
ALLOWED_ROLES = [int(role_id) for role_id in config["allowed_roles"]]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

async def send_activity_check(author, guild, channel):
    check_number = increment_activity_check()
    now = datetime.utcnow()
    deadline = now + timedelta(days=2)
    timestamp = int(deadline.timestamp())

    embed = discord.Embed(
        title=f"<:reaper:1274745507389898773> Activity Check #{check_number}",
        description=(
            f"## 🕰️ Time Left: <t:{timestamp}:R>\n"
            f"## 📈 Goal: 10+ reactions\n"
            f"## ⁉️ Consequences:\n"
            f"- **Failure to react to this activity check <t:{timestamp}:R> may result in warnings, kicks, or bans for inactivity.**\n"
            f"- **Glory to {config['server_name']}**"
        ),
        color=discord.Color.red()
    )
    avatar_url = author.avatar.url if author.avatar else author.default_avatar.url
    embed.set_footer(text=f"Posted by {author}", icon_url=avatar_url)

    message = await channel.send("||@everyone||", embed=embed)
    await message.add_reaction("✅")

    failed_dms = []
    async for member in guild.fetch_members(limit=None):
        if member.bot:
            continue
        try:
            await member.send(
                f"📢 **Activity Check Alert #{check_number}!**\n"
                f"Please check the activity announcement in {channel.mention} on **{config['server_name']}**!\n"
                f"Deadline: <t:{timestamp}:R>\n\n"
                f"React with ✅ to confirm your activity!"
            )
            await asyncio.sleep(1)
        except discord.Forbidden:
            failed_dms.append(str(member))
        except Exception as e:
            print(f"Failed to DM {member.name}: {e}")

    return failed_dms

async def send_dead_chat_ping(author, guild, channel):
    ping_number = increment_dead_chat_pings()
    now = datetime.utcnow()
    review_time = now + timedelta(days=1)
    timestamp = int(review_time.timestamp())
    
    last_message = None
    async for msg in channel.history(limit=1):
        last_message = msg
    
    last_active = "No recent messages"
    if last_message:
        last_active = f"<t:{int(last_message.created_at.timestamp())}:R> by {last_message.author.mention}"

    embed = discord.Embed(
        title=f"☕️ Dead Chat Alert #{ping_number}!",
        description=(
            f"## 🔔 Activity review <t:{timestamp}:R>\n"
            f"### Let's bring this chat back to life!\n\n"
            f"📊 **Current Status**\n"
            f"- Last message: {last_active}\n"
            f"- Total members: {guild.member_count}\n\n"
            f"🎯 **Why be active?**\n"
            f"- Earn special roles and perks\n"
            f"- Get priority for events\n"
            f"- Build your reputation with staff\n\n"
            f"💬 **How to participate?**\n"
            f"- Start a conversation\n"
            f"- Reply to others\n"
            f"- Share your thoughts\n\n"
            f"⚠️ **Inactive members may face consequences**"
        ),
        color=discord.Color.orange()
    )
    
    prompts = [
        "What's your favorite movie/show right now?",
        "Share something interesting that happened to you today!",
        "What's your opinion on pineapple pizza?",
        "If you could have any superpower, what would it be?",
        "What's your go-to comfort food?"
    ]
    embed.add_field(name="💡 Conversation Starter", value=f"*{random.choice(prompts)}*", inline=False)
    
    avatar_url = author.avatar.url if author.avatar else author.default_avatar.url
    embed.set_footer(text=f"Initiated by {author}", icon_url=avatar_url)
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/892292745916481546.gif?size=96&quality=lossless")

    message = await channel.send("||@everyone||", embed=embed)
    await message.add_reaction("💬")
    await message.add_reaction("☕")

    failed_dms = []
    async for member in guild.fetch_members(limit=None):
        if member.bot:
            continue
        try:
            dm_embed = discord.Embed(
                title=f"👋 {guild.name} needs you!",
                description=(
                    f"Our chat in **{channel.mention}** could use some activity!\n\n"
                    f"**Why participate?**\n"
                    f"- Earn special roles and perks\n"
                    f"- Get noticed by staff\n"
                    f"- Help build our community\n\n"
                    f"Join the conversation now and help keep our server alive!\n"
                    f"[Jump to channel]({message.jump_url})"
                ),
                color=discord.Color.orange()
            )
            dm_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            await member.send(embed=dm_embed)
            await asyncio.sleep(1)
        except discord.Forbidden:
            failed_dms.append(str(member))
        except Exception as e:
            print(f"Failed to DM {member.name}: {e}")

    return failed_dms

def has_permission(interaction_or_context):
    if isinstance(interaction_or_context, discord.Interaction):
        user = interaction_or_context.user
    else:
        user = interaction_or_context.author
    
    user_roles = [role.id for role in user.roles]
    return any(role_id in ALLOWED_ROLES for role_id in user_roles)

@bot.tree.command(name="help", description="Displays all available commands.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Activity Manager Bot Commands",
        description="Here are all the commands you can use with the Activity Manager Bot! 🎉",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    
    commands_list = [
        ("📋 /help", "Shows this help message"),
        ("📢 /activity", "Launch an activity check (requires permission)"),
        ("☕️ /deadchat", "Ping inactive members and encourage activity (requires permission)"),
        ("📣 !activity", "Prefix version of /activity"),
        ("☕️ !deadchat", "Prefix version of /deadchat")
    ]
    
    for name, value in commands_list:
        embed.add_field(name=name, value=value, inline=False)
    
    avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
    embed.set_footer(text=f"Requested by {interaction.user}", icon_url=avatar_url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="activity", description="Sends an activity check message and DMs members.")
async def slash_activity(interaction: discord.Interaction):
    if not has_permission(interaction):
        await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    try:
        guild = bot.get_guild(SERVER_ID)
        if not guild:
            await interaction.followup.send("❌ Server not found! Please check the server ID in config.", ephemeral=True)
            return

        channel = guild.get_channel(ACTIVITY_CHANNEL_ID)
        if not channel:
            await interaction.followup.send("❌ Activity channel not found! Please check the channel ID in config.", ephemeral=True)
            return

        failed_dms = await send_activity_check(interaction.user, guild, channel)
        response = "✅ Activity check posted and DMs sent!"
        if failed_dms:
            response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
        await interaction.followup.send(response, ephemeral=True)
    except Exception as e:
        print(f"Error in activity command: {e}")
        await interaction.followup.send("❌ An error occurred while executing this command.", ephemeral=True)

@bot.tree.command(name="deadchat", description="Pings the dead chat and DMs members to encourage activity.")
async def slash_deadchat(interaction: discord.Interaction):
    if not has_permission(interaction):
        await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    try:
        guild = bot.get_guild(SERVER_ID)
        if not guild:
            await interaction.followup.send("❌ Server not found! Please check the server ID in config.", ephemeral=True)
            return

        channel = guild.get_channel(DEAD_CHAT_CHANNEL_ID)
        if not channel:
            await interaction.followup.send("❌ Dead chat channel not found! Please check the channel ID in config.", ephemeral=True)
            return

        failed_dms = await send_dead_chat_ping(interaction.user, guild, channel)
        response = "📣 Dead chat ping sent and DMs delivered!"
        if failed_dms:
            response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
        await interaction.followup.send(response, ephemeral=True)
    except Exception as e:
        print(f"Error in deadchat command: {e}")
        await interaction.followup.send("❌ An error occurred while executing this command.", ephemeral=True)

@bot.command(name="help")
async def prefix_help(ctx):
    embed = discord.Embed(
        title="📜 Activity Manager Bot Commands",
        description="Here are all the commands you can use with the Activity Manager Bot! 🎉",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    
    commands_list = [
        ("📋 !help", "Shows this help message"),
        ("📢 !activity", "Launch an activity check (requires permission)"),
        ("☕️ !deadchat", "Ping inactive members and encourage activity (requires permission)"),
        ("📣 /activity", "Slash command version of !activity"),
        ("☕️ /deadchat", "Slash command version of !deadchat")
    ]
    
    for name, value in commands_list:
        embed.add_field(name=name, value=value, inline=False)
    
    avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=avatar_url)
    await ctx.send(embed=embed)

@bot.command(name="activity")
async def prefix_activity(ctx):
    if not has_permission(ctx):
        await ctx.send("🚫 You don't have permission to use this command!")
        return

    try:
        guild = bot.get_guild(SERVER_ID)
        if not guild:
            await ctx.send("❌ Server not found! Please check the server ID in config.")
            return

        channel = guild.get_channel(ACTIVITY_CHANNEL_ID)
        if not channel:
            await ctx.send("❌ Activity channel not found! Please check the channel ID in config.")
            return

        failed_dms = await send_activity_check(ctx.author, guild, channel)
        response = "✅ Activity check posted and DMs sent!"
        if failed_dms:
            response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
        await ctx.send(response)
    except Exception as e:
        print(f"Error in activity command: {e}")
        await ctx.send("❌ An error occurred while executing this command.")

@bot.command(name="deadchat")
async def prefix_deadchat(ctx):
    if not has_permission(ctx):
        await ctx.send("🚫 You don't have permission to use this command!")
        return

    try:
        guild = bot.get_guild(SERVER_ID)
        if not guild:
            await ctx.send("❌ Server not found! Please check the server ID in config.")
            return

        channel = guild.get_channel(DEAD_CHAT_CHANNEL_ID)
        if not channel:
            await ctx.send("❌ Dead chat channel not found! Please check the channel ID in config.")
            return

        failed_dms = await send_dead_chat_ping(ctx.author, guild, channel)
        response = "📣 Dead chat ping sent and DMs delivered!"
        if failed_dms:
            response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
        await ctx.send(response)
    except Exception as e:
        print(f"Error in deadchat command: {e}")
        await ctx.send("❌ An error occurred while executing this command.")

bot.run(os.getenv("TOKEN"))