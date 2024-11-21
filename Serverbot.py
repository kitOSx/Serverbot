import discord
from discord import app_commands
import os
import subprocess
import tomllib
import sys
import asyncio
import datetime

import shutil
import tempfile
import zipfile

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

create_backups = config['create_backups']
backup_time = config['backup_time']
to_save = config['to_save']
backup_folder = config['backup_folder']
backup_on_start = config['make_backup_on_start']
create_restarts = config['create_restarts']
restart_time = config['restart_after_time']



#embed colors
hex_red=0xFF0000
hex_green=0x0AC700
hex_yellow=0xFFF000 # I also like -> 0xf4c50b



# Global variable to store the subprocess handle for server management
subprocess_handle = None




#Just in case no heap sizes are given. Use Minecraft's Recommended default sizes.
if not min_heap_size:
    min_heap_size = "1024M"
if not max_heap_size:
    max_heap_size = "1024M"


#juicy platform control <3
if sys.platform == 'win32':
    platform_command = ['cmd', '/k', f'java -Xms{min_heap_size} -Xmx{max_heap_size} -jar {server_jar} nogui']
else:
    platform_command = ['java', f'-Xmx{max_heap_size}', f'-Xms{min_heap_size}', '-jar', f'{server_jar}', 'nogui']





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



def backup_files(paths, backup_folder=None):
    temp_dir = tempfile.mkdtemp()
    try:
        # Create backup folder if one is not specified.
        if backup_folder is None:
            backup_folder = os.path.join(os.getcwd(), 'backups')

        os.makedirs(backup_folder, exist_ok=True)
        for path in paths:
            if os.path.exists(path):
                base_name = os.path.basename(path)
                dest_path = os.path.join(temp_dir, base_name)

                if os.path.isdir(path):
                    shutil.copytree(path, dest_path)
                else:
                    shutil.copy2(path, dest_path)

        # Create timestamped ZIP archive.
        timestamp = datetime.datetime.now().strftime("%m%d%Y_%I%M%S") #Murica.
        zip_filename = f"backup_{timestamp}.zip"
        zip_path = os.path.join(backup_folder, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    file_path = os.path.join(root, f)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname=arcname)
        return zip_path

    finally:
        # Always clean up the temporary directory
        print("Cleaning up...")
        shutil.rmtree(temp_dir, ignore_errors=True)


async def scheduled_backup(log_channel):
    global subprocess_handle
    flg = 0

    while True:
        if not subprocess_handle:
            break # When we type /stop, we want this to also stop. We have to wait for the timer still with this method, but it works and doesn't make more backups.
        else:
            if backup_on_start == False and flg == 0: # Do NOT touch flg.
                pass
            else:
                print("\n-=-=-=-=-=-=-=-=-=-=-=-=- ...Starting Backup... -=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
                print(f'Stopping subprocess_handle: "{subprocess_handle}"')
                subprocess_handle.stdin.write("stop\n")
                subprocess_handle.stdin.flush()

                await asyncio.sleep(5)
                subprocess_handle.stdin.close()

                print("Saving chunks...")
                sb_wait_embed = discord.Embed(title="MC Server Status", description='Server saving chunks...', colour=hex_yellow, timestamp=datetime.datetime.now(datetime.timezone.utc))
                sb_waiting_msg = await log_channel.send(embed=sb_wait_embed)
                await asyncio.to_thread(subprocess_handle.wait)

                sb_stop_embed = discord.Embed(title="MC Server Status", description="Server has stopped! - Making a backup...", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
                await sb_waiting_msg.edit(content='', embed=sb_stop_embed)
                subprocess_handle = None
                print("Server Offline.")

                # Make and save backup.
                backup_zip_path = backup_files(to_save, './backups')
                print(f"Backup created: {backup_zip_path}")

                # Start server again
                subprocess_handle = subprocess.Popen(
                    platform_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True
                )
                print("Starting server...")
                await asyncio.sleep(10)
                sb_start_embed = discord.Embed(title="MC Server Status", description='Server has been started and is Online!', colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
                await log_channel.send(embed=sb_start_embed)
                print("Server Online!")
                print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n")

            sleepy_time = backup_time * 60 * 60
            await asyncio.sleep(sleepy_time) # After X-hrs later, do this whole thing again.
            flg = 1






async def scheduled_restarts(log_channel):
    global subprocess_handle
    flg = 0
    while True:
        if not subprocess_handle:
            break
        else:
            if flg == 0:
                pass # Force the bot to wait the timer before restarting.
            else:
                print("\n-=-=-=-=-=-=-=-=-=-=-=-=- ...Restarting Server... -=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
                print(f'Stopping subprocess_handle: "{subprocess_handle}"')
                subprocess_handle.stdin.write("stop\n")
                subprocess_handle.stdin.flush()

                await asyncio.sleep(5)
                subprocess_handle.stdin.close()

                print("Saving chunks...")
                sr_wait_embed = discord.Embed(title="MC Server Status", description='Server saving chunks...', colour=hex_yellow, timestamp=datetime.datetime.now(datetime.timezone.utc))
                sr_waiting_msg = await log_channel.send(embed=sr_wait_embed)
                await asyncio.to_thread(subprocess_handle.wait)

                sr_stop_embed = discord.Embed(title="MC Server Status", description="Server has stopped! - Restarting Server...", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
                await sr_waiting_msg.edit(content='', embed=sr_stop_embed)
                subprocess_handle = None
                print("Server Offline.")

                # Start server again
                subprocess_handle = subprocess.Popen(
                    platform_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True
                )
                print("Starting server...")
                await asyncio.sleep(10)
                sr_start_embed = discord.Embed(title="MC Server Status", description='Server has been restarted and is Online!', colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
                await log_channel.send(embed=sr_start_embed)
                print("Server restarted!")
                print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n")

            restart_timer = restart_time * 60 * 60
            await asyncio.sleep(restart_timer)
            flg=1




@client.event
async def on_ready():
    clear()
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    print('Registered Commands:')
    for command in client.tree.get_commands():
        print(f"- {command.name}: {command.description}")
    print('\n')










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

    if subprocess_handle:
        await interaction.response.send_message('Server is already Online.', ephemeral=True, delete_after=10)
    else:
        # Attempt to run the server
        await interaction.response.send_message("Attempting to start server!", ephemeral=True)
        subprocess_handle = subprocess.Popen(
            platform_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        print("Running 'start' command.")
        await asyncio.sleep(10) # Wait for server to initialize and setup.
        start_embed = discord.Embed(title="MC Server Status", description='Server has been started and is Online!', colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=start_embed)
        print("Server Online!")
        if create_backups == True:
            client.loop.create_task(scheduled_backup(log_channel))
        if create_restarts == True:
            client.loop.create_task(scheduled_restarts(log_channel))



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

        print("Saving chunks...")
        wait_embed = discord.Embed(title="MC Server Status", description='Server saving chunks...', colour=hex_yellow, timestamp=datetime.datetime.now(datetime.timezone.utc))
        waiting_msg = await log_channel.send(embed=wait_embed)
        await asyncio.to_thread(subprocess_handle.wait) #wait for all chunks to be saved first. (to avoid chunk errors and chunks being missplaced)

        stop_embed = discord.Embed(title="MC Server Status", description="Server has stopped!", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await waiting_msg.edit(content='', embed=stop_embed)
        subprocess_handle = None
        print("Server Offline.")
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
        print("Saving chunks...")
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
        stdout=subprocess.PIPE,
        text=True
    )
    print("Restarting the server.")
    await asyncio.sleep(10)
    if not stop_msg:
        restart_embed = discord.Embed(title="MC Server Status", description="Server has been started and is Online!", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=restart_embed)
        print("Server restarted and Online!")
    else:
        restart_embed = discord.Embed(title="MC Server Status", description="Server restarted!", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await stop_msg.edit(content='', embed=restart_embed)
        print("Server restarted and Online!")



@client.tree.command(description="Add user to MC server whitelist.")
async def whitelist_add(interaction: discord.Interaction, user_name: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
    global subprocess_handle
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
async def ban(interaction: discord.Interaction, user_name: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
    global subprocess_handle
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


@client.tree.command(description="Lists users on the server.")
async def mclist(interaction: discord.Interaction):
    global subprocess_handle

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    if subprocess_handle:
        await interaction.response.defer()
        command = "list\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()

        # Read multiple lines of output printed to terminal.
        outputs = []
        while True:
            output = subprocess_handle.stdout.readline()
            if not output:
                break
            outputs.append(output.strip())

            # Look for the specific "players online" line.
            if "players online" in output.lower():
                break

        # Find the line with the list of users.
        user_list_line = next((line for line in outputs if "players online" in line.lower()), "No users found")

        # Extract the relevant information.
        if "players online:" in user_list_line:
            parts = user_list_line.split("players online:")
            player_count = parts[0].split("There are")[1].strip().split(" of ")[0]
            max_players = parts[0].split("max of")[1].strip().split(" ")[0]
            players = parts[1].strip()

            #Make it pretty.
            description = (
                "📊 - **Player Stats**\n"
                f"Currently Online: **{player_count}**\n"
                f"Max Players: **{max_players}**\n\n"
                "👥 - **Online Players**\n"
                f"```{players if players else 'No players online'}```"
            )
        else:
            description = "❌ Unable to fetch player list ❌"

        lst_embed = discord.Embed(title="List of Online Players", description=description, colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        lst_embed.set_footer(text="Last Updated")

        await interaction.followup.send(embed=lst_embed)
    else:
        err_embed = discord.Embed(title="❌ Server Offline ❌", description="The Minecraft server is currently not running.", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        err_embed.set_footer(text="Last Checked")
        await interaction.response.send_message(embed=err_embed, ephemeral=True)


@client.tree.command(description="Adds player to operator list.")
async def op(interaction: discord.Interaction, user_name: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
    global subprocess_handle
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    if subprocess_handle:
        await interaction.response.send_message(f'Adding "{user_name}" to OP list...', ephemeral=True)
        # Send the op command to the server
        command = f"op {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        mc_pardon_embed = discord.Embed(title="OP", description=f"{user_name} has been set as an operator.", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=mc_pardon_embed)
    else:
        await interaction.response.send_message('Server Offline.', ephemeral=True)
        err_embed = discord.Embed(title="MC Server Status", description='Server is not running.', colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=op_embed)


@client.tree.command(description="Removes player to operator list.")
async def deop(interaction: discord.Interaction, user_name: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)
    global subprocess_handle
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True)
        return

    if subprocess_handle:
        await interaction.response.send_message(f'Removing "{user_name}" from OP list...', ephemeral=True)
        command = f"deop {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        mc_pardon_embed = discord.Embed(title="DeOP", description=f"{user_name} has been removed as an operator.", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=mc_pardon_embed)
    else:
        await interaction.response.send_message('Server Offline.', ephemeral=True)
        err_embed = discord.Embed(title="MC Server Status", description='Server is not running.', colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=op_embed)



# https://www.digminecraft.com/lists/color_list_pc.php
@client.tree.command(description="Sends messages to the the MC server.")
async def say(interaction: discord.Interaction, msg: str):
    if not logging_channel_id:
        log_channel = interaction.channel
    else:
        log_channel = client.get_channel(logging_channel_id)

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True, delete_after=10)
        return

    if subprocess_handle:
        await interaction.response.send_message(f'Message: {msg}\nHas been sent to the server!', ephemeral=True, delete_after=10)
        command = f"say {msg}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
    else:
        await interaction.response.send_message('Server Offline.', ephemeral=True)
        err_embed = discord.Embed(title="MC Server Status", description='Server is not running.', colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=op_embed)

# Run the bot
client.run(TOKEN, reconnect=True)
