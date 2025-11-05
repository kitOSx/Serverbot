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
  - [x] Fix the damn injection exploit I hate you Scott for finding it
        - Some mods cause minecrafts user input sterilization to break. This will cause issues with the /say command. Be warned.

# Being worked on currently 
  - I have a /somewhat/ functional web gui set up based around Flask. It is not working as intended, but I am very close. Here are some of the things that will be added with the GUI (hopefully); 
      - Configuration changes can be done through the webgui instead of having to manually edit settings in the config file itself, i.e. Allocation, tokens, server.jar/world folder location, etc. 
      - You will be able to add your own commands through the interface. This allows you to add commands from vanilla, mods, server pluggins or other server mod loaders.
      - Working on getting graphs working for memory usage based on what you have allocated.
      - Figure out what the code I wrote months ago for this gui even is supposed to do...
        
  - I understand bad actors could use this tool to do harm to your server, and at worst your PC. Testing showed originally that users could bypass admin restrictions and gain OP on servers running certain chat addons,
    most likely insecure input handling by the chat addon, allowing newline/control-character or some instances, JSON injection; Allowing users to escalate privlages. Out of the many I have tried, none of the mods I've tried       had this issue. I know its not the bot - the bot sends the same exact thing you type to the java process to be used, so any way you try to get around the safeguards will fail due to how the original input sterilization
    works in chat. I will be working on a proper sanitizer to prevent this from occurring, in the future. 

__ __

<br>

# Special thanks
@therealOri for major contributions. 
