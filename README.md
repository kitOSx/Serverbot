# Serverbot
My bot I use to control my minecraft server using Python through Discord.
If anyone actually stumbles upon this online and wants to use it for your own server, please make sure you run the .py script using either Command Prompt or Powershell as administrator.
If you use Linux, you probably already know what to do.
Be sure to add your own Bot key and directory to ensure it actually runs.

All so we can control it without having access to the computer running the server / having an admin on the server or having to SSH into the server.
__ __

<br>

# Whats new? 
- Updated main functionality to use buttons instead of `/commands`.
- Added `hex_purple` for purple embeds.
- Fixed some typos.
- Updated `on_ready()` event to show "Registered Features" Instead of "Registered Commands".
- Updated some error messages to show up as an `interaction.response` message instead of in the log channel for everyone to see.
- Added a `/mc_menu` command for accessing the control pannel.
- Added a `Backup` button for making backups manually.
- Added a way to handle button states when swapping between menus.
__ __

<br>
<br>

# Showcase
![github_serverbot_showcase](https://github.com/user-attachments/assets/7d075457-313a-4e4d-86ad-27065c2aa744)

__ __

<br>
<br>

# TODO
  - [x] Fix button states when switching back to main panel menu. (keep track of button states)
  - [] Migrate/Rewrite bot to `Pycord` instead of using `discord.py`.
  - [] Somehow make discord and minecraft chat sync to add cross communication.
__ __

<br>

# Special thanks
@therealOri for major contributions. 
