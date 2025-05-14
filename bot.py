import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime, timedelta
import os
import asyncio
import dotenv
dotenv.load_dotenv()

with open("config.json", "r") as f:
    config = json.load(f)

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

@app_commands.command(name="help", description="Displays all available commands.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Activity Manager Bot Commands",
        description="Here are all the commands you can use with the Activity Manager Bot! 🎉",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    embed.set_image(url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fmedia.tenor.com%2F-Rq8B_yGAmsAAAAC%2Fanime-girl-red-eyes.gif&f=1&nofb=1&ipt=18697f376dd9e87cc462106576fc2f84dbcb58ca461133f49e0438f13a759812")
    embed.add_field(
        name="📋 /help",
        value="Shows this help message with all commands (slash command).",
        inline=False
    )
    embed.add_field(
        name="📋 !help",
        value="Shows this help message with all commands (prefix command).",
        inline=False
    )
    embed.add_field(
        name="📢 /activity",
        value="Sends an activity check message to the specified channel and DMs all members. (Restricted to specific roles, slash command)",
        inline=False
    )
    embed.add_field(
        name="📢 !activity",
        value="Sends an activity check message to the specified channel and DMs all members. (Restricted to specific roles, prefix command)",
        inline=False
    )
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

    now = datetime.utcnow()
    deadline = now + timedelta(days=2)
    timestamp = int(deadline.timestamp())

    guild = bot.get_guild(config["server_id"])
    if not guild:
        await interaction.response.send_message("❌ Server not found! Check the `server_id` in config.json.", ephemeral=True)
        return

    channel = guild.get_channel(config["activity_channel_id"])
    if not channel:
        await interaction.response.send_message("❌ Activity channel not found! Check the `activity_channel_id` in config.json.", ephemeral=True)
        return


    embed = discord.Embed(
        title="<:reaper:1274745507389898773> Activity Check #2",
        description=(
            f"## 🕰️ Time Left: <t:{timestamp}:R>\n"
            f"## 📈 Goal: 10+\n"
            f"## ⁉️ Punishment:\n"
            f"- **Not clicking to this activity check <t:{timestamp}:R> will result in you getting either warned, kicked, or even banned for inactivity reasons. Glory to {config['server_name']}.**"
        ),
        color=discord.Color.red()
    )
    avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
    embed.set_footer(text=f"Posted by {interaction.user}", icon_url=avatar_url)

    await channel.send("||@everyone||", embed=embed)

    failed_dms = []
    for member in guild.members:
        if member.bot:
            continue
        try:
            await member.send(
                f"📢 **Activity Check Alert!**\n"
                f"Please check the activity announcement in {channel.mention} on **{config['server_name']}**!\n"
                f"Deadline: <t:{timestamp}:R>"
            )
            await asyncio.sleep(1)
        except discord.Forbidden:
            failed_dms.append(member.name)
        except Exception as e:
            print(f"Failed to DM {member.name}: {e}")

    response = "✅ Activity check posted and DMs sent!"
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
    embed.set_image(url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fmedia.tenor.com%2F-Rq8B_yGAmsAAAAC%2Fanime-girl-red-eyes.gif&f=1&nofb=1&ipt=18697f376dd9e87cc462106576fc2f84dbcb58ca461133f49e0438f13a759812")
    embed.add_field(
        name="📋 /help",
        value="Shows this help message with all commands (slash command).",
        inline=False
    )
    embed.add_field(
        name="📋 !help",
        value="Shows this help message with all commands (prefix command).",
        inline=False
    )
    embed.add_field(
        name="📢 /activity",
        value="Sends an activity check message to the specified channel and DMs all members. (Restricted to specific roles, slash command)",
        inline=False
    )
    embed.add_field(
        name="📢 !activity",
        value="Sends an activity check message to the specified channel and DMs all members. (Restricted to specific roles, prefix command)",
        inline=False
    )
    avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=avatar_url)
    await ctx.send(embed=embed)

@bot.command(name="activity", description="Sends an activity check message and DMs members.")
async def prefix_activity(ctx):
    allowed_roles = config["allowed_roles"]
    has_role = any(role.id in allowed_roles for role in ctx.author.roles)
    if not has_role:
        await ctx.send("🚫 You don't have permission to use this command!", ephemeral=True)
        return

    now = datetime.utcnow()
    deadline = now + timedelta(days=2)
    timestamp = int(deadline.timestamp())

    guild = bot.get_guild(config["server_id"])
    if not guild:
        await ctx.send("❌ Server not found! Check the `server_id` in config.json.", ephemeral=True)
        return

    channel = guild.get_channel(config["activity_channel_id"])
    if not channel:
        await ctx.send("❌ Activity channel not found! Check the `activity_channel_id` in config.json.", ephemeral=True)
        return

    embed = discord.Embed(
        title="<:reaper:1274745507389898773> Activity Check #2",
        description=(
            f"## 🕰️ Time Left: <t:{timestamp}:R>\n"
            f"## 📈 Goal: 10+\n"
            f"## ⁉️ Punishment:\n"
            f"- **Not clicking to this activity check <t:{timestamp}:R> will result in you getting either warned, kicked, or even banned for inactivity reasons. Glory to {config['server_name']}.**"
        ),
        color=discord.Color.red()
    )
    avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    embed.set_footer(text=f"Posted by {ctx.author}", icon_url=avatar_url)

    await channel.send("||@everyone||", embed=embed)

    failed_dms = []
    for member in guild.members:
        if member.bot:
            continue
        try:
            await member.send(
                f"📢 **Activity Check Alert!**\n"
                f"Please check the activity announcement in {channel.mention} on **{config['server_name']}**!\n"
                f"Deadline: <t:{timestamp}:R>"
            )
            await asyncio.sleep(1)
        except discord.Forbidden:
            failed_dms.append(member.name)
        except Exception as e:
            print(f"Failed to DM {member.name}: {e}")

    response = "✅ Activity check posted and DMs sent!"
    if failed_dms:
        response += f"\n⚠️ Failed to DM: {', '.join(failed_dms)}"
    await ctx.send(response, ephemeral=True)

bot.run(os.environ['TOKEN'])