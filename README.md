# Serverbot
My bot I use to control my minecraft server using Python through Discord.
If anyone actually stumbles upon this online and wants to use it for your own server, please make sure you run the .py script using either Command Prompt or Powershell as administrator.
If you use Linux, you probably already know what to do.
Be sure to add your own Bot key and directory to ensure it actually runs.

All so we can control it without having access to the computer running the server / having an admin on the server or having to SSH into the server.
__ __

<br>

# Whats new? 
- Multi world support and world instance loading.
- New command `/mc_world_load <path_to_server_folder>`
__ __
> You can now have multiple server folders all with their own world, mods, server properties, etc. By using `/mc_world_load` you can swap between them instead of having to manually mess with 
files, configs, and mods everytime you want to play on a different world/server. 

<br>
<br>

# Showcase
![github_serverbot_showcase](https://github.com/user-attachments/assets/0e5e8ae8-f1db-4390-a5a2-5c36af36cd1a)
__ __
> The menu doesn't update so **make sure** to stop the server and **exit** before loading a new instance and opening a new menu.

<br>
<br>

# TODO
  - [x] Fix button states when switching back to main panel menu. (keep track of button states)
  - [] Migrate/Rewrite bot to `Pycord` instead of using `discord.py`.
  - [] Somehow make discord and minecraft chat sync to add cross communication.
  - [] Fix the damn injection exploit I hate you Scott for finding it 
__ __

<br>

# Special thanks
@therealOri for major contributions. 
