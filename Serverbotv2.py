import discord
from discord import app_commands
import os
import subprocess
import tomllib
import sys
import asyncio



def clear():
    os.system("cls||clear") #cls for windows clear for linux/unix.


#Load our config
with open('config.toml', 'rb') as fileObj:
    config = tomllib.load(fileObj) #dictionary/json




TOKEN = config["token"]
server_jar = config["server_jar"]
guild_id = config["discord_guild"]
GUILD = discord.Object(id=guild_id)


# Global variable to store the subprocess handle for server management
subprocess_handle = None





#juicy platform control <3
if sys.platform == 'win32':
    platform_command = ['cmd', '/k', f'{server_jar}']
else:
    #assuming server already exists and eula has been agreed too and server heap size stuff has been set up already, etc.
    platform_command = ['java', '-jar', f'{server_jar}', 'nogui']





# +++++++++++ Client Setup +++++++++++ #
class ServerBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild. | so you don't need to wait 2hrs+ for discord to register commands globally.
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=None)



intents = discord.Intents.default()
client = ServerBot(intents=intents) # "client" can be changed to anything, but you'll need to update everywhere else it has been used below.
# +++++++++++ Client Setup +++++++++++ #







@client.event
async def on_ready():
    clear()
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')







@client.tree.command(description='Start Minecraft Server.')
async def start(interaction: discord.Interaction):
    global subprocess_handle
    channel = interaction.channel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True) #ephemeral = only visible by the user that ran the command.
        return

    # Attempt to run the server
    await interaction.response.send_message("Server Attempting to start!")
    subprocess_handle = subprocess.Popen(
        platform_command,
        stdin=subprocess.PIPE,
        text=True
    )
    print("Running 'start' command.")
    await asyncio.sleep(5)  # Wait for server to initialize
    await channel.send("Server started, loading world...")
    await asyncio.sleep(5)  # Further wait for server setup
    await channel.send("Server up, standing by.")
    print("Server started!")






@client.tree.command(description="Stop Minecraft Server.")
async def stop(interaction: discord.Interaction):
    global subprocess_handle
    channel = interaction.channel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    # Stop the server if it's running
    if subprocess_handle:
        await interaction.response.send_message(f'Attempting to stop. subprocess_handle: "{subprocess_handle}"')
        subprocess_handle.stdin.write("stop\n")
        subprocess_handle.stdin.flush()

        await asyncio.sleep(5)  # Allow time for server data saving
        subprocess_handle.stdin.close()  # No more commands, close stdin
        await channel.send("Server saving chunks...")
        await asyncio.to_thread(subprocess_handle.wait) #wait for all chunks to be saved first. (to avoid chunk errors and chunks being missplaced)
        await channel.send("Server stopped!")
        subprocess_handle = None
    else:
        await channel.send("No server found.")






@client.tree.command(description="Restarts Minecraft Server.")
async def restart(interaction: discord.Interaction):
    global subprocess_handle
    channel = interaction.channel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    # Stop the server if it's running
    if subprocess_handle:
        await interaction.response.send_message(f"Attempting to restart. subprocess_handle: `{subprocess_handle}`")
        subprocess_handle.stdin.write("stop\n")
        subprocess_handle.stdin.flush()
        await asyncio.sleep(5)
        subprocess_handle.stdin.close()
        await channel.send("Server saving chunks...")
        await asyncio.to_thread(subprocess_handle.wait)
        subprocess_handle = None
        await channel.send("Server stopped, restarting now...")
        print("Server stopped.")
    else:
        await channel.send("No server found to restart, starting a new one...")

    # Restart the server
    await channel.send("Server Attempting to restart!")
    subprocess_handle = subprocess.Popen(
        platform_command,
        stdin=subprocess.PIPE,
        text=True
    )
    print("Restarting the server.")
    await asyncio.sleep(5)
    await channel.send("Server restarted, loading world...")
    await asyncio.sleep(5)
    await channel.send("Server up, standing by.")
    print("Server restarted.")





@client.tree.command(description="Add user to MC server whitelist.")
async def whitelist_add(interaction: discord.Interaction, user_name: str):
    global subprocess_handle
    channel = interaction.channel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    if subprocess_handle:
        await interaction.response.send_message(f'Adding "{user_name}" to whitelist...', ephemeral=True)
        # Send the whitelist add command to the server
        command = f"whitelist add {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        await channel.send(f"User {user_name} has been added to the whitelist.")
    else:
        await channel.send("Server is not running.")





@client.tree.command(description="Remove user from MC server whitelist.")
async def whitelist_remove(interaction: discord.Interaction, user_name: str):
    global subprocess_handle
    channel = interaction.channel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    if subprocess_handle:
        await interaction.response.send_message(f'Removing "{user_name}" from whitelist...', ephemeral=True)
        # Send the whitelist remove command to the server
        command = f"whitelist remove {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        await channel.send(f"User {user_name} has been removed from the whitelist.")
    else:
        await channel.send("Server is not running.")





@client.tree.command(description="Ban a user from the MC server.")
async def ban(interaction: discord.Interaction, user_name: str):
    global subprocess_handle
    channel = interaction.channel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    if subprocess_handle:
        await interaction.response.send_message(f'Banning "{user_name}" from server...', ephemeral=True)
        # Send the ban command to the server
        command = f"ban {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        await channel.send(f"{user_name} has been banned.")
    else:
        await channel.send("Server is not running.")





@client.tree.command(description="Unban user from the MC server.")
async def unban(interaction: discord.Interaction, user_name: str):
    global subprocess_handle
    channel = interaction.channel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    if subprocess_handle:
        await interaction.response.send_message(f'Unbanning "{user_name}" from server...', ephemeral=True)
        # Send the ban command to the server
        command = f"pardon {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        await channel.send(f"{user_name} has been unbanned.")
    else:
        await channel.send("Server is not running.")






# Run the bot
client.run(TOKEN, reconnect=True)
