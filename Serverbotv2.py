import discord
from discord import app_commands
import os
import subprocess
import tomllib
import sys
import asyncio
import datetime




def clear():
    os.system("cls||clear") #cls for windows clear for linux/unix.


#Load our config
with open('config.toml', 'rb') as fileObj:
    config = tomllib.load(fileObj) #dictionary/json




TOKEN = config["token"]
server_jar = config["server_jar"]
min_heap_size = config["min_heap_size"]
max_heap_size = config["max_heap_size"]
guild_id = config["discord_guild"]
GUILD = discord.Object(id=guild_id)
logging_channel_id = config["logging_channel"]


#embed colors
hex_red=0xFF0000
hex_green=0x0AC700
hex_yellow=0xFFF000 # I also like -> 0xf4c50b



# Global variable to store the subprocess handle for server management
subprocess_handle = None





#juicy platform control <3
if sys.platform == 'win32':
    platform_command = ['cmd', '/k', f'java -Xms{min_heap_size} -Xmx{max_heap_size} -jar {server_jar} nogui']
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
    # If you don't provide a channel ID for sending logs, it will just use the channel that you sent the command in.
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
    global subprocess_handle
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True) #ephemeral = only visible by the user that ran the command.
        return

    # Attempt to run the server
    await interaction.response.send_message("Attempting to start server!", ephemeral=True)
    subprocess_handle = subprocess.Popen(
        platform_command,
        stdin=subprocess.PIPE,
        text=True
    )
    print("Running 'start' command.")
    await asyncio.sleep(10) # Wait for server to initialize and setup.
    start_embed = discord.Embed(title="MC Server Status", description='Server has been started and is Online!', colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
    await log_channel.send(embed=start_embed)






@client.tree.command(description="Stop Minecraft Server.")
async def stop(interaction: discord.Interaction):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
    global subprocess_handle
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    # Stop the server if it's running
    if subprocess_handle:
        await interaction.response.send_message(f'Attempting to stop server.', ephemeral=True)
        print(f'Stopping subprocess_handle: "{subprocess_handle}"')
        subprocess_handle.stdin.write("stop\n")
        subprocess_handle.stdin.flush()

        await asyncio.sleep(5)  # Allow time for server data saving
        subprocess_handle.stdin.close()  # No more commands, close stdin

        wait_embed = discord.Embed(title="MC Server Status", description='Server saving chunks...', colour=hex_yellow, timestamp=datetime.datetime.now(datetime.timezone.utc))
        waiting_msg = await log_channel.send(embed=wait_embed)
        await asyncio.to_thread(subprocess_handle.wait) #wait for all chunks to be saved first. (to avoid chunk errors and chunks being missplaced)

        stop_embed = discord.Embed(title="MC Server Status", description="Server has stopped!", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await waiting_msg.edit(content='', embed=stop_embed)
        subprocess_handle = None
    else:
        await interaction.response.send_message('Server Offline.', ephemeral=True) # these interaction responses are for dealing with when you used the command. So it completes instead of errors.
        err_embed = discord.Embed(title="MC Server Status", description='Server is not running.', colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=err_embed)






@client.tree.command(description="Restarts Minecraft Server.")
async def restart(interaction: discord.Interaction):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
    global subprocess_handle
    channel = interaction.channel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    # Stop the server if it's running
    if subprocess_handle:
        await interaction.response.send_message("Attempting to restart server.", ephemeral=True)
        print(f'stopping subprocess_handle: "{subprocess_handle}"')
        subprocess_handle.stdin.write("stop\n")
        subprocess_handle.stdin.flush()
        await asyncio.sleep(5)
        subprocess_handle.stdin.close()
        wait_embed = discord.Embed(title="MC Server Status", description='Server saving chunks...', colour=hex_yellow, timestamp=datetime.datetime.now(datetime.timezone.utc))
        waiting_msg = await log_channel.send(embed=wait_embed)
        await asyncio.to_thread(subprocess_handle.wait)
        subprocess_handle = None


        stop_embed = discord.Embed(title="MC Server Status", description="Server stopped, restarting now...", colour=hex_yellow, timestamp=datetime.datetime.now(datetime.timezone.utc))
        stop_msg = await waiting_msg.edit(content='', embed=stop_embed)
        print("Server stopped.")
    else:
        stop_msg=None
        await interaction.response.send_message("No server found to restart, starting a new one...", ephemeral=True)

    # Restart the server
    subprocess_handle = subprocess.Popen(
        platform_command,
        stdin=subprocess.PIPE,
        text=True
    )
    print("Restarting the server.")
    await asyncio.sleep(10)
    print("Server restarted.")
    if not stop_msg:
        restart_embed = discord.Embed(title="MC Server Status", description="Server has been started and is Online!", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=restart_embed)
    else:
        restart_embed = discord.Embed(title="MC Server Status", description="Server restarted!", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await stop_msg.edit(content='', embed=restart_embed)






@client.tree.command(description="Add user to MC server whitelist.")
async def whitelist_add(interaction: discord.Interaction, user_name: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
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
        wla_embed = discord.Embed(title="MC Server Command", description=f"User {user_name} has been added to the whitelist.", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=wla_embed)
    else:
        await interaction.response.send_message('Server Offline.', ephemeral=True)
        err_embed = discord.Embed(title="MC Server Status", description='Server is not running.', colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=err_embed)





@client.tree.command(description="Remove user from MC server whitelist.")
async def whitelist_remove(interaction: discord.Interaction, user_name: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
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
        wlr_embed = discord.Embed(title="MC Server Command", description=f"User {user_name} has been removed from the whitelist.", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=wlr_embed)
    else:
        await interaction.response.send_message('Server Offline.', ephemeral=True)
        err_embed = discord.Embed(title="MC Server Status", description='Server is not running.', colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=err_embed)





@client.tree.command(description="Ban a user from the MC server.")
async def mcban(interaction: discord.Interaction, user_name: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
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
        mc_ban_embed = discord.Embed(title="MC Server Command", description=f"{user_name} has been banned.", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=mc_ban_embed)
    else:
        await interaction.response.send_message('Server Offline.', ephemeral=True)
        err_embed = discord.Embed(title="MC Server Status", description='Server is not running.', colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=err_embed)





@client.tree.command(description="Unban user from the MC server.")
async def unban(interaction: discord.Interaction, user_name: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
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
        mc_pardon_embed = discord.Embed(title="MC Server Command", description=f"{user_name} has been unbanned.", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=mc_pardon_embed)
    else:
        await interaction.response.send_message('Server Offline.', ephemeral=True)
        err_embed = discord.Embed(title="MC Server Status", description='Server is not running.', colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=err_embed)






# Run the bot
client.run(TOKEN, reconnect=True)
