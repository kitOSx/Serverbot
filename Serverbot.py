import discord
from discord import app_commands
import os
import subprocess
import configparser
import sys
import asyncio
import datetime
import shutil
import tempfile
import zipfile
import ast

def clear():
    os.system("cls||clear") #cls for windows clear for linux/unix.


config = configparser.ConfigParser()
config.read('config.ini')


TOKEN = config['Bot']["token"]
guild_id = config.getint('Bot', 'discord_guild')
GUILD = discord.Object(id=guild_id)
logging_channel_id = config.getint('Bot', 'logging_channel')


server_jar = config['Server']["server_jar"]
min_heap_size = config['Server']["min_heap_size"]
max_heap_size = config['Server']["max_heap_size"]
create_backups = config.getboolean('Server', 'create_backups')
backup_on_start = config.getboolean('Server', 'make_backup_on_start')
backup_time = config.getint('Server', 'backup_time')
to_save = ast.literal_eval(config['Server']['to_save']) #ast will make the string "['a', 'b', 'c', 'd']" into a list. ['a', 'b', 'c', 'd']
backup_folder = config['Server']['backup_folder']
create_restarts = config.getboolean('Server', 'create_restarts')
restart_time = config.getint('Server', 'restart_after_time')



#embed colors
hex_red=0xFF0000
hex_green=0x0AC700
hex_yellow=0xFFF000 # I also like -> 0xf4c50b
hex_purple=0x8321EA



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



async def async_timer(total_time, warn_minutes=None, svr_msg=None):
    global subprocess_handle
    if warn_minutes is None:
        warn_minutes = []

    warn_minutes = sorted(warn_minutes, reverse=True)
    for warn_min in warn_minutes:
        warn_seconds = warn_min * 60
        if warn_seconds < total_time:
            await asyncio.sleep(total_time - warn_seconds)
            timer_warning = svr_msg + f'§6{warn_min}§r minutes.'
            tw_command = f"say {timer_warning}\n"
            subprocess_handle.stdin.write(tw_command)
            subprocess_handle.stdin.flush()

    # Wait remaining time before 10-second countdown. After we give the warning, it needs to keep counting and not skip straight to the 10s countdown.
    remaining_time = total_time - sum(m * 60 for m in warn_minutes if m * 60 < total_time)
    if remaining_time > 10:
        await asyncio.sleep(remaining_time - 10)

    timer_notice = f"§4[Notice!]:§r Server is restarting, will be back up shortly..."
    tn_command = f"say {timer_notice}\n"
    subprocess_handle.stdin.write(tn_command)
    subprocess_handle.stdin.flush()

    for i in range(10, 0, -1):
        await asyncio.sleep(1)
        count_down = f"§4{i}..."
        cd_command = f"say {count_down}\n"
        subprocess_handle.stdin.write(cd_command)
        subprocess_handle.stdin.flush()

    final_notice = f"§4Restarting..."
    fn_command = f"say {final_notice}\n"
    subprocess_handle.stdin.write(fn_command)
    subprocess_handle.stdin.flush()
    await asyncio.sleep(4)






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

                backup_zip_path = backup_files(to_save, './backups')
                print(f"Backup created: {backup_zip_path}")

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
            warning_message = f"§4[Warning!]:§r Server will create a backup and restart in: "
            await async_timer(total_time=sleepy_time, warn_minutes=[15], svr_msg=warning_message) # After X-hrs later, do this whole thing again.
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
            warning_message = f"§4[Warning!]:§r Server will restart in: "
            await async_timer(total_time=restart_timer, warn_minutes=[15], svr_msg=warning_message)
            flg=1





#Exiting Main Menu
async def exit(self, interaction):
    global subprocess_handle
    if subprocess_handle:
        await interaction.response.send_message("⚠️ Warning: Please shut down the server first!", ephemeral=True, delete_after=10)
    else:
        await interaction.response.send_message("Goodbye!", ephemeral=True, delete_after=10)
        await interaction.message.delete()
        self.stop()



async def offline_msg(interaction):
    err_embed = discord.Embed(title="❌ Server Offline ❌", description="I am not able to run this command while the server is offline.", colour=hex_red, timestamp=datetime.datetime.now(datetime.timezone.utc))
    err_embed.set_footer(text="Last Checked")
    await interaction.response.send_message(embed=err_embed, ephemeral=True, delete_after=10)



# Add new features here so it shows up when ready.
features = {"Start & Stop":"Starts & Stops the MC server.",
            "Restart":"Restarts the MC server manually.",
            "Backup":"Manually makes a backup of the server files.",
            "List":"Lists the players online in the server.",
            "Say":"Broadcast messages to the server.",
            "Whitelisting":"Add & Remove players from the MC server whitelist.",
            "Banning":"Ban & Unban players from the server.",
            "OP":"Give or Remove OP to/from players in the MC server."
}

@client.event
async def on_ready():
    clear()
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    print('Registered Features:')
    for feature, info in features.items():
        print(f"- {feature}: {info}")
    print('\n')






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

        ss_command = f"say §4[Warning!]§r A server OP is stopping the server.\nShutting down in...\n"
        subprocess_handle.stdin.write(ss_command)
        subprocess_handle.stdin.flush()
        for i in range(5, 0, -1):
            await asyncio.sleep(1)
            sscd_command = f"say §4{i}...\n"
            subprocess_handle.stdin.write(sscd_command)
            subprocess_handle.stdin.flush()
        await asyncio.sleep(4)


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
        await interaction.response.send_message('Server is already Offline.', ephemeral=True, delete_after=10) # these interaction responses are for dealing with when you used the command. So it completes instead of errors.



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

        rs_command = f"say §4[Warning!]§r A server OP is manually restarting the server.\nRestarting in...\n"
        subprocess_handle.stdin.write(rs_command)
        subprocess_handle.stdin.flush()
        for i in range(5, 0, -1):
            await asyncio.sleep(1)
            rscd_command = f"say §4{i}...\n"
            subprocess_handle.stdin.write(rscd_command)
            subprocess_handle.stdin.flush()
        await asyncio.sleep(4)

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
        await offline_msg(interaction) # "offline_msg()" is basically backup error handling in case it doesn't work the first time when using the buttons.



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
        await offline_msg(interaction)



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
        await offline_msg(interaction)



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
        # Send the unban command to the server
        command = f"pardon {user_name}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
        mc_pardon_embed = discord.Embed(title="MC Server Command", description=f"{user_name} has been unbanned.", colour=hex_green, timestamp=datetime.datetime.now(datetime.timezone.utc))
        await log_channel.send(embed=mc_pardon_embed)
    else:
        await offline_msg(interaction)



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
        await offline_msg(interaction)



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
        await offline_msg(interaction)



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
        await offline_msg(interaction)


# https://www.digminecraft.com/lists/color_list_pc.php
async def say(interaction: discord.Interaction, msg: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True, delete_after=10)
        return

    if subprocess_handle:
        await interaction.response.send_message(f'Message: {msg}\nHas been sent to the server!', ephemeral=True, delete_after=10)
        command = f"say {msg}\n"
        subprocess_handle.stdin.write(command)
        subprocess_handle.stdin.flush()
    else:
        await offline_msg(interaction)







# Modals
class mc_wlAdd(discord.ui.Modal, title='Minecraft User Whitelist.'):
    code = discord.ui.TextInput(
        label='MC Username to whitelist.',
        placeholder='Username here...',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        mc_username = self.code.value #this is what the user typed
        await whitelist_add(interaction, mc_username)


class mc_wlRemove(discord.ui.Modal, title='Minecraft User Whitelist.'):
    code = discord.ui.TextInput(
        label='MC Username to remove from whitelist.',
        placeholder='Username here...',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        mc_username = self.code.value
        await whitelist_remove(interaction, mc_username)


class mc_Ban(discord.ui.Modal, title='Minecraft User Banning.'):
    code = discord.ui.TextInput(
        label='MC Username to Ban from the server.',
        placeholder='Username here...',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        mc_username = self.code.value
        await ban(interaction, mc_username)


class mc_UnBan(discord.ui.Modal, title='Minecraft User Un-Banning.'):
    code = discord.ui.TextInput(
        label='MC Username to UnBan from the server.',
        placeholder='Username here...',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        mc_username = self.code.value
        await unban(interaction, mc_username)


class mc_OP(discord.ui.Modal, title='Minecraft User OP.'):
    code = discord.ui.TextInput(
        label='OP a user on the MC server.',
        placeholder='Username here...',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        mc_username = self.code.value
        await op(interaction, mc_username)


class mc_DeOP(discord.ui.Modal, title='Minecraft User De-OP.'):
    code = discord.ui.TextInput(
        label='De-OP a user on the MC server.',
        placeholder='Username here...',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        mc_username = self.code.value
        await deop(interaction, mc_username)


class mc_Say(discord.ui.Modal, title='Minecraft Sever Broadcast.'):
    code = discord.ui.TextInput(
        label='Boadcast a message to the MC server.',
        placeholder='Message here...',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        mc_message = self.code.value
        await say(interaction, mc_message)







# Buttons/Menus
class User_Management_Menu(discord.ui.View):
    def __init__(self, offline_msg, timeout=None):
        super().__init__(timeout=timeout)
        self.offline_msg = offline_msg

    @discord.ui.button(label='Whitelist', style=discord.ButtonStyle.blurple, emoji="✅")
    async def whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            wlAdd = mc_wlAdd()
            await interaction.response.send_modal(wlAdd)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)

    @discord.ui.button(label='De-whitelist', style=discord.ButtonStyle.blurple, emoji="❌")
    async def dewhitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            wlRemove = mc_wlRemove()
            await interaction.response.send_modal(wlRemove)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)


    @discord.ui.button(label='Ban', style=discord.ButtonStyle.blurple, emoji="🔨")
    async def mc_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            svr_ban = mc_Ban()
            await interaction.response.send_modal(svr_ban)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)


    @discord.ui.button(label='Unban', style=discord.ButtonStyle.blurple, emoji="🔧")
    async def mc_unban(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            svr_unban = mc_UnBan()
            await interaction.response.send_modal(svr_unban)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)

    @discord.ui.button(label='Op', style=discord.ButtonStyle.blurple, emoji="👤")
    async def op_a_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            svr_op = mc_OP()
            await interaction.response.send_modal(svr_op)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)


    @discord.ui.button(label='De-Op', style=discord.ButtonStyle.blurple, emoji="🚷")
    async def deop_a_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            svr_deop = mc_DeOP()
            await interaction.response.send_modal(svr_deop)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)

    @discord.ui.button(label='Back', style=discord.ButtonStyle.red, emoji="🚪")
    async def prev_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        timeout=None
        view = Main_Menu(timeout=timeout)
        view.edit_button_states()
        await interaction.response.edit_message(view=view)






class Main_Menu(discord.ui.View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)


    offline_msg="Server is Offline and can't run this command."
    button_states = {
        'Start': {
            'style': discord.ButtonStyle.green,
            'disabled': False
        },
        'Stop': {
            'style': discord.ButtonStyle.red,
            'disabled': True
        }
    }
    def edit_button_states(self):
        for item in self.children:
            if item.label in self.button_states:
                state = self.button_states[item.label]
                item.style = state['style']
                item.disabled = state['disabled']

    @discord.ui.button(label='Start', style=discord.ButtonStyle.green, emoji="▶️")
    async def start_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            await interaction.response.send_message('Server is already Online.', ephemeral=True, delete_after=10)
        else:
            self.button_states['Start']['style'] = discord.ButtonStyle.gray
            self.button_states['Start']['disabled'] = True
            self.button_states['Stop']['disabled'] = False

            self.edit_button_states()
            await interaction.message.edit(view=self)
            await start(interaction)


    @discord.ui.button(label='Stop', style=discord.ButtonStyle.red, emoji="🛑", disabled=True)
    async def stop_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            self.button_states['Start']['style'] = discord.ButtonStyle.green
            self.button_states['Start']['disabled'] = False
            self.button_states['Stop']['disabled'] = True

            self.edit_button_states()
            await interaction.message.edit(view=self)
            await stop(interaction)
        else:
            await interaction.response.send_message('Server is already Offline.', ephemeral=True, delete_after=10)


    @discord.ui.button(label='Restart', style=discord.ButtonStyle.green, emoji="🔁")
    async def restart_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await restart(interaction)


    @discord.ui.button(label='Backup', style=discord.ButtonStyle.grey, emoji="💾")
    async def backup_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            print("Creating Manual Backup...")
            backup_zip_path = backup_files(to_save, './backups')
            await interaction.response.send_message("Backup has been created and saved to `./backups`!", ephemeral=True, delete_after=10)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)


    @discord.ui.button(label='List', style=discord.ButtonStyle.blurple, emoji="📋")
    async def list_users(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            await mclist(interaction)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)


    @discord.ui.button(label='Say', style=discord.ButtonStyle.blurple, emoji="💬")
    async def server_say(self, interaction: discord.Interaction, button: discord.ui.Button):
        global subprocess_handle
        if subprocess_handle:
            svr_say = mc_Say()
            await interaction.response.send_modal(svr_say)
        else:
            await interaction.response.send_message(self.offline_msg, ephemeral=True, delete_after=10)


    @discord.ui.button(label='Player Pannel', style=discord.ButtonStyle.blurple, emoji="🛗")
    async def player_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        timeout=None
        view = User_Management_Menu(self.offline_msg, timeout=timeout)
        await interaction.response.edit_message(view=view)


    @discord.ui.button(label='Exit', style=discord.ButtonStyle.red, emoji="🚪")
    async def exit_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await exit(self, interaction)








@client.tree.command(description="Menu pannel for MC server actions!")
async def mc_menu(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sorry, you don't have permission to use this command.", ephemeral=True, delete_after=10)
        return

    timeout=None
    view=Main_Menu(timeout=timeout)
    description="""
__**Minecraft Server Control Pannel! - 🎮**__
> Manage your Minecraft server with ease using buttons!


__**Server Controls**__:
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

- **Start & Stop**: Starts and stops the server.
- **Restart**: Restarts the server.
- **Backup**: Makes a manual backup.
- **Player Pannel**: Lets you use commands for managing users in your server. (Whitelisting, OP, Bans, etc.)
- **Say**: Send/broadcast messages directly to the server chat.
- **List**: View online players and server info.

-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""
    menu_embed = discord.Embed(
        description=description,
        color=hex_purple,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    await interaction.response.send_message(embed=menu_embed, view=view)



# Run the bot
client.run(TOKEN, reconnect=True)
