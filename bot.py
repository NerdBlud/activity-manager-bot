import discord
from discord.ext import commands
import json
from datetime import datetime, timedelta
import os
import asyncio
from dotenv import load_dotenv
load_dotenv() 

with open("config.json", "r") as f:
    config = json.load(f)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  
bot = commands.Bot(command_prefix=["!", "/"], intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.hybrid_command(name="help", description="Displays all available commands.")
async def help(ctx):
    embed = discord.Embed(
        title="📜 Activity Manager Bot Commands",
        description="Here are all the commands you can use with the Activity Manager Bot! 🎉",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_image(url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fmedia.tenor.com%2F-Rq8B_yGAmsAAAAC%2Fanime-girl-red-eyes.gif&f=1&nofb=1&ipt=18697f376dd9e87cc462106576fc2f84dbcb58ca461133f49e0438f13a759812") 
    embed.add_field(
        name="📋 /help or !help",
        value="Shows this help message with all commands.",
        inline=False
    )
    embed.add_field(
        name="📢 /activity or !activity",
        value="Sends an activity check message to the specified channel and DMs all members. (Restricted to specific roles)",
        inline=False
    )
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="activity", description="Sends an activity check message and DMs members.")
async def activity(ctx):
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
    embed.set_footer(text=f"Posted by {ctx.author}", icon_url=ctx.author.avatar.url)

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

bot.run(os.getenv("TOKEN"))