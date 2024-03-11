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
        ["cmd", "/k", " # Your server .jar or .bat here"],
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

    # Stop the server if it's running
    if subprocess_handle:
        subprocess_handle.stdin.write("stop\n")
        subprocess_handle.stdin.flush()

        time.sleep(5)  # Allow time for server data saving

        subprocess_handle.stdin.close()  # No more commands, close stdin

        await ctx.send("Server stopped.")
        subprocess_handle = None
    else:
        await ctx.send("No server found.")


@bot.command(name="restart")
async def restart(ctx):
    global subprocess_handle
    print(f"Attempting to restart. subprocess_handle: {subprocess_handle}")
    # Check for administrator permissions
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    # Stop the server if it's running
    if subprocess_handle:
        subprocess_handle.stdin.write("stop\n")
        subprocess_handle.stdin.flush()
        time.sleep(5)  # Allow time for server data saving
        subprocess_handle.stdin.close()  # No more commands, close stdin
        subprocess_handle = None
        await ctx.send("Server stopped, restarting now...")
        print("Server stopped.")
    else:
        await ctx.send("No server found to restart, starting a new one...")

    # Restart the server
    await ctx.send("Server Attempting to restart!")
    subprocess_handle = subprocess.Popen(
        ["cmd", "/k", "# Your server .jar or .bat here"],
        stdin=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    print("Restarting the server.")
    time.sleep(5)  # Wait for server to initialize
    await ctx.send("Server restarted, loading world...")
    time.sleep(5)  # Further wait for server setup
    await ctx.send("Server up, standing by.")
    print("Server restarted.")


@bot.command(name="whitelist_add")
async def whitelist_add(ctx, user_name: str):
    global subprocess_handle
    # Check for administrator permissions
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    # Check if the server is running
    if subprocess_handle:
        # Send the whitelist add command to the server
        command = f"whitelist add {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        await ctx.send(f"User {user_name} has been added to the whitelist.")
    else:
        await ctx.send("Server is not running.")


@bot.command(name="whitelist_remove")
async def whitelist_remove(ctx, user_name: str):
    global subprocess_handle
    # Check for administrator permissions
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You do not have permission to use this command.")
        return

    # Check if the server is running
    if subprocess_handle:
        # Send the whitelist remove command to the server
        command = f"whitelist remove {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        await ctx.send(f"User {user_name} has been removed from the whitelist.")
    else:
        await ctx.send("Server is not running.")


@bot.command(name="ban")
async def ban(ctx, user_name: str):
    global subprocess_handle
    # Check perms again
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You do not have permissions to use this command.")
        return

    # Check if the server is running
    if subprocess_handle:
        # Send the ban command to the server
        command = f"ban {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        await ctx.send(f"{user_name} has been banned.")
    else:
        await ctx.send("Server is not running.")


@bot.command(name="unban")
async def unban(ctx, user_name: str):
    global subprocess_handle
    # Check perms again
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You do not have permissions to use this command.")
        return

    # Check if the server is running
    if subprocess_handle:
        # Send the ban command to the server
        command = f"pardon {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        await ctx.send(f"{user_name} has been unbanned.")
    else:
        await ctx.send("Server is not running.")


# Run the bot
bot.run("# Add your bot key here")
