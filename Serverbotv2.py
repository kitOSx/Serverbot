import discord
from discord.ext import commands
import os
import time
import subprocess

# Define the necessary intents with message capabilities enabled for guilds and processing commands
intents = discord.Intents.default()
intents.guild_messages = True
intents.message_content = True

# Create an instance of a bot with all intents enabled
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Global variable to store the subprocess handle for server management
subprocess_handle = None


@bot.command(name="start")
async def runfile(ctx):
    global subprocess_handle
    # Check if the user has administrator permissions
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    # Attempt to run the server
    await ctx.send("Server Attempting to start!")
    subprocess_handle = subprocess.Popen(
        ["cmd", "/k", "# You can put a directory to a .bat file that runs your server.jar with certain permissions or just run the server using java args."],
        stdin=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    print("Running the command.")
    time.sleep(5)  # Wait for server to initialize
    await ctx.send("Server started, loading world...")
    time.sleep(5)  # Further wait for server setup
    await ctx.send("Server up, standing by.")
    print("Server started.")


@bot.command(name="stop")
async def stop(ctx):
    global subprocess_handle
    print(f"Attempting to stop. subprocess_handle: {subprocess_handle}")
    # Check for administrator permissions
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    # Stop the server if it's running, I seriously dont think anything past this point works 
    if subprocess_handle:
        subprocess_handle.stdin.write("stop\n")
        subprocess_handle.stdin.flush()

        time.sleep(5)  # Allow time for server data saving

        subprocess_handle.stdin.close()  # No more commands, close stdin

        await ctx.send("Server stopped.")
        subprocess_handle = None
    else:
        await ctx.send("No server found.")


# Run the bot, I know this works lol 
bot.run("# Put your Discord Bot token here")
