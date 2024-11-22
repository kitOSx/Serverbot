# Serverbot
My bot I use to control my minecraft server using Python through Discord.
If anyone actually stumbles upon this online and wants to use it for your own server, please make sure you run the .py script using either Command Prompt or Powershell as administrator.
If you use Linux, you probably already know what to do.
Be sure to add your own Bot key and directory to ensure it actually runs.

All so we can control it without having access to the computer running the server / having an admin on the server or having to SSH into the server.
__ __

<br>

# Whats new? 
Added commands for providing and removing operator privlages, a command to list out current players.

# Commands
Use /start to start the server.

Use /stop to stop the server.

Use /restart to restart the server.

/whitelist_add (playername) to whitelist a player.

/whitelist_remove (playername) to remove a player from the whitelist.

/ban (playername) to ban a player.

/unban (playername) to unban a player.

/mclist to list players currently online, if any.

/op to give a player operator commands.

/deop to remove a player's operator commands. 

/say {msg} for sending messages to the server for serverwide broadcasts.
__ __

<br>
<br>

# TODO
  - [x] Add commands for scheduled restarts.
  - [x] Add a command for backups.
  - [x] Add a command for /say (for serverwide broadcasts.)
  - [] Somehow make discord and minecraft chat sync to add cross communication.
  - [x] Send/say messages to the server before updating or restarting. (15min warning and 10s countdown)
  - [x] Add system messages sent to the server when stopping, restarting, and making backups.

# Special thanks
@therealOri for major contributions. 
