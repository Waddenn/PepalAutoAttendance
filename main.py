import json
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import locale
import time
from datetime import datetime
import os
import tkinter as tk
import base64
from Crypto.Cipher import AES
import threading
from PIL import Image, ImageTk
import subprocess
import math


locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

key = b'/B?E(H+MbQeThWmZq4t7w!z%C&F)J@Nc'
iv = b'9%XDU5V9nwyi%cc#'

driveretat = False
attempts = 0

target_folder = os.path.expanduser('~/Documents/PepalAutoAttendance')
target_logo = target_folder + "/login.png"
target_credentials = target_folder + '/save_credentials.txt'
target_loading = target_folder + "/loading-cube.gif"
target_chromedriver = target_folder + '/chromedriver.exe'
target_DB = target_folder + '/course_sessions.json'
target_pepal = target_folder + "/logo_pepal.png"

def update_gif_animation(ind):
    global gif_label, gif_image

    try:
        frame = gif_image[ind]
        gif_label.configure(image=frame)
        window.after(125, update_gif_animation, (ind + 1) % num_frames)
    except:
        pass

def display_gif_animation():
    global gif_label, gif_image, num_frames, logo_label
    logo_label.grid_forget()
    
    pil_image = Image.open(target_loading)
    
    num_frames = pil_image.n_frames

    new_width = 120
    new_height = 120

    gif_image = [ImageTk.PhotoImage(pil_image.copy().convert("RGBA").resize((new_width, new_height), Image.LANCZOS)) for frame in range(num_frames) if pil_image.seek(frame) is None]

    gif_label = tk.Label(window, image=gif_image[0], bg="#04050f")
    gif_label.grid(row=0, column=0, pady=(5,10))
    update_gif_animation(0)
    window.update()

def remove_gif_animation():
    global gif_label
    gif_label.grid_forget()
    logo_label.grid(row=0, column=0, pady=(30,30))

def encrypt_password(password):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_password = password.ljust((len(password) // 16 + 1) * 16)
    encrypted_password = cipher.encrypt(padded_password.encode('utf-8'))
    return base64.b64encode(encrypted_password).decode('utf-8')

def decrypt_password(encrypted_password):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_password = base64.b64decode(encrypted_password.encode('utf-8'))
    decrypted_password = cipher.decrypt(encrypted_password)
    return decrypted_password.decode('utf-8').rstrip()

is_closing = False

def close_driver():
    global is_closing
    is_closing = True
    if driveretat : 
        try : 
            driver.quit()
        except NoSuchElementException:
            pass

def on_closing():
    t = threading.Thread(target=close_driver)
    t.start()
    window.destroy() 
    exit() 

def initialize_driver():
    driver = None
    global driveretat
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        chrome_service = webdriver.chrome.service.Service(executable_path=(target_chromedriver))
        chrome_service.creation_flags = subprocess.CREATE_NO_WINDOW
        driver = webdriver.Chrome(service=chrome_service, options=options)
        driveretat = True
    except WebDriverException as chrome_exception:
        message_label.grid(row=3, column=0, pady=(15,0))
        print("Erreur lors de l'initialisation de Chrome : ", str(chrome_exception))
        try:
            options = Options()
            binary_location = os.environ.get('FIREFOX_BINARY_PATH')
            
            if not binary_location:
                binary_location = 'C:\\Program Files\\Mozilla Firefox\\firefox.exe'
                
                if not os.path.isfile(binary_location):
                    binary_location = 'C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe'
                    
                    if not os.path.isfile(binary_location):
                        raise FileNotFoundError("Le chemin vers le binaire Firefox n'a pas été trouvé.")
            
            options.binary_location = binary_location
            options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)
            driveretat = True
        except WebDriverException:
            update_message("Erreur lors de l'initialisation de Chrome et Firefox")
    return driver

def update_message(new_message):
    message_label.config(text=new_message)    
    window.update()

def update_attempts():
    global attempts
    attempts += 1

def main_thread():
    if not (username_entry.get() or password_entry.get()):
        login_button.config(state="disabled")
        message_label.grid(row=3, column=0, pady=(15,0))
        update_message("Veuillez entrer un mot de passe")
    else:
        login_button.config(state="disabled")
        display_gif_animation()
        threading.Thread(target=main).start()

def save_credentials():
    username = username_entry.get()
    password = encrypt_password(password_entry.get())
    with open(target_credentials, 'w') as save_credentials_file:
        save_credentials_file.write(f"username:{username}\npassword:{password}")

def load_credentials():
    if os.path.isfile(target_credentials):
        with open(target_credentials, 'r') as save_credentials_file:
            config = dict(line.strip().split(':') for line in save_credentials_file)
            return config["username"], decrypt_password(config["password"])
    else:
        return None, None

def connect_to_site(username, password):
    driver.get('http://www.pepal.eu')

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'username'))
    )

    driver.find_element(By.NAME, 'username').send_keys(username)
    password_field = driver.find_element(By.NAME, 'password')
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#gritter-item-1.gritter-red'))
        )

        update_message("La connexion a échoué :\n les identifiants sont incorrects")
    except TimeoutException:
        print("Login successful.")


def extract():
    panels = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.panel.panel-bordered.panel-primary.panel-line'))
    )

    if os.path.isfile(target_DB) and os.path.getsize(target_DB) > 0:
        with open(target_DB, 'r') as f:
            course_sessions = json.load(f)
    else:
        course_sessions = []

    for i in range(len(panels)):
        panel = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'div.panel.panel-bordered.panel-primary.panel-line:nth-child({i+1})'))
        )
        WebDriverWait(panel, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.panel-heading h3.panel-title'))
        )
        date_str = panel.find_element(By.CSS_SELECTOR, 'div.panel-heading h3.panel-title').text.split('du')[-1].strip()

        body_presences = panel.find_elements(By.CSS_SELECTOR, 'tbody[id="body_presences"]')
        if len(body_presences) == 0:
            return
        rows = panel.find_element(By.CSS_SELECTOR, 'tbody[id="body_presences"]').find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            time_str = row.find_element(By.TAG_NAME, 'td').text
            start_time_str, end_time_str = time_str.split('-')
            start_time = datetime.strptime(date_str + ' ' + start_time_str, '%A %d %B %Y %H:%M')
            end_time = datetime.strptime(date_str + ' ' + end_time_str, '%A %d %B %Y %H:%M')

            session_id = row.find_element(By.CSS_SELECTOR, 'a[href^="/presences/s/"]').get_attribute('href').split('/')[-1]

            session_info = {
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'session_id': session_id
            }
            
            if session_info not in course_sessions:
                course_sessions.append(session_info)
    
    with open(target_DB, 'w') as f:
        json.dump(course_sessions, f)


def get_next_or_current_session_id():
    with open(target_DB, 'r') as f:
        course_sessions = json.load(f)

    course_sessions.sort(key=lambda x: x['start_time'])

    now = datetime.now()

    for session in course_sessions:
        start_time = datetime.strptime(session['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(session['end_time'], '%Y-%m-%d %H:%M:%S')

        if start_time <= now <= end_time:
            return session['session_id'] 
        elif now < start_time:
            return session['session_id']  

    return None  

def is_session_in_progress(session):
    start_time = datetime.strptime(session['start_time'], '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(session['end_time'], '%Y-%m-%d %H:%M:%S')

    now = datetime.now()

    return start_time <= now <= end_time

def click_future_seances():
        driver.get('https://www.pepal.eu/presences')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'seances_view_future'))).click()
        time.sleep(1)

def seances():
    driver.get('https://www.pepal.eu/presences')


def check_site_status(session_id):
    global site_status
    try:
        driver.get(f"https://www.pepal.eu/presences/s/{session_id}")
        site_status=True
    except WebDriverException:
        update_message("Le site n'est pas accessible.")
        site_status=False

def attend_and_confirm_presence(session_id):
    global is_closing
    driver.get(f"https://www.pepal.eu/presences/s/{session_id}")

    with open(target_DB, 'r') as f:
        course_sessions = json.load(f)

    session = next((s for s in course_sessions if s['session_id'] == session_id), None)

    if session is None:
        print(f"No session found with ID {session_id}")
        return

    start_time = datetime.strptime(session['start_time'], '%Y-%m-%d %H:%M:%S')

    while not is_session_in_progress(session) and not is_closing:
        now = datetime.now()
        time_remaining = start_time - now
        hours, remainder = divmod(time_remaining.total_seconds(), 3600)
        minutes = math.ceil(remainder / 60)
        if hours > 0:
            update_message(f"Le cours commence dans : \n{int(hours)} heures et {int(minutes)} minutes.")
        elif minutes > 0:
            update_message(f"Le cours commence dans : \n{int(minutes)} minutes.")

        time_to_next_minute = 60 - now.second
        time.sleep(time_to_next_minute)

    waiting_start_time = datetime.now()
    try:
        WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'alert-success')]")))
        presence_element = driver.find_element(By.XPATH, "//div[contains(@class,'alert-success')]")
        presence_text = presence_element.text.strip()
        presence_text = presence_text.split("le ")
        presence_text[1] = "\n" + presence_text[1]
        update_message(presence_text[0] + "le " + presence_text[1])
        return
    except TimeoutException:
        while is_session_in_progress(session) and not is_closing:
            try:
                confirm_button = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.ID, 'set-presence'))
                )
                confirm_button.click()
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'alert-success')]")))
                presence_element = driver.find_element(By.XPATH, "//div[contains(@class,'alert-success')]")
                presence_text = presence_element.text.strip()
                presence_text = presence_text.split("le ")
                presence_text[1] = "\n" + presence_text[1]
                update_message(presence_text[0] + "le " + presence_text[1])
                return
            except TimeoutException:
                now = datetime.now()
                elapsed_time = now - waiting_start_time
                hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
                minutes = round(remainder / 60)
                check_site_status(session_id)
                if site_status :
                    update_message(f"Attente de l'ouverture de l'appel depuis\n({int(minutes)} minutes).")
                time.sleep(10)
        update_message("Le cours est terminé.")

DB_exite = True
print(target_folder)
def main():
    global driver, DB_exite
    update_message("")
    save_credentials()
    message_label.grid(row=3, column=0, pady=(15,0))
    driver = initialize_driver()
    connect_to_site(username_entry.get(), password_entry.get())
    if not os.path.isfile(target_DB) or os.path.getsize(target_DB) == 0:
        seances()
        extract()
        click_future_seances()
        extract()
        click_future_seances()
        DB_exite =  False
    session_id = get_next_or_current_session_id()
    if session_id:
        print(f"Next or current session id is {session_id}")

        with open(target_DB, 'r') as f:
            course_sessions = json.load(f)
        session = next((s for s in course_sessions if s['session_id'] == session_id), None)
        session_date = datetime.strptime(session['start_time'], '%Y-%m-%d %H:%M:%S').date()

        if session_date != datetime.now().date():
            click_future_seances()
        elif DB_exite:
            click_future_seances()
            click_future_seances()

        remove_gif_animation()
        attend_and_confirm_presence(session_id)
    else:
        update_message("Aucun cours n'a été trouvé !")
    login_button.config(state="normal")
    driver.quit()


username, password = load_credentials()

window = tk.Tk()
window.title("PepalAutoAttendance")
window.configure(bg="#04050f")
window.resizable(width=False, height=False)
window.geometry("350x300")

window.grid_columnconfigure(0, weight=1)


label_font = ("Segoe UI", 12, "bold")
entry_font = ("Segoe UI", 12, "bold")
button_font = ("Segoe UI", 12, "bold")


logo_img = tk.PhotoImage(file=target_pepal)

logo_label = tk.Label(window, image=logo_img, bg="#04050f")
logo_label.grid(row=0, column=0, pady=(30,30))

def focus_search_entry(event):
    username_entry.focus_set()

def focus_search_entry(event):
    password_entry.focus_set()

username_entry = tk.Entry(window, font=entry_font, width=20, bg="#04050f", justify='center')
username_entry.grid(row=1, column=0, ipady='5', pady=(0,20))
username_entry.config(fg="white")
username_entry.configure(insertbackground='white')

password_entry = tk.Entry(window, font=entry_font, show="*", width=20, bg="#04050f", justify='center')
password_entry.grid(row=2, column=0,ipady='5', pady=(0,0))
password_entry.config(fg="white")
password_entry.configure(insertbackground='white')

if os.path.isfile(target_credentials):
    password_entry.insert(0, password)
    username_entry.insert(0, username)

login_icon = Image.open(target_logo)

login_icon_resized = login_icon.resize((35, 35), Image.LANCZOS)
login_icon_photo = ImageTk.PhotoImage(login_icon_resized)

login_icon_big = login_icon.resize((int(35 * 1.1), int(35 * 1)), Image.LANCZOS)
login_icon_photo_big = ImageTk.PhotoImage(login_icon_big)

window.login_icon_photo = login_icon_photo
window.login_icon_photo_big = login_icon_photo_big

def on_enter(event):
    login_button.config(image=window.login_icon_photo_big)

def on_leave(event):
    login_button.config(image=window.login_icon_photo)


login_button = tk.Button(window, image=login_icon_photo, command=main_thread, font=button_font, bg="#04050f", fg="white", activebackground="#04050f", relief=tk.FLAT, activeforeground="white", borderwidth=0)
login_button.grid(row=2, column=0, pady=(0,0), padx=(250,0))

login_button.bind("<Enter>", on_enter)
login_button.bind("<Leave>", on_leave)

message_label = tk.Label(window, text="", font=label_font, fg="#ec6502", bg="#04050f")
message_label.config(font=(label_font[0], label_font[1]))
window.eval('tk::PlaceWindow %s center' % window.winfo_toplevel())

window.protocol("WM_DELETE_WINDOW", on_closing)

if (username_entry.get() or password_entry.get()) :
    login_button.config(state="normal")
else :
    login_button.config(state="disabled")


def on_entry_changed(event):
    if username_entry.get() and password_entry.get():
        login_button.config(state="normal")
    else:
        login_button.config(state="disabled")

username_entry.bind("<KeyRelease>", on_entry_changed)
password_entry.bind("<KeyRelease>", on_entry_changed)


window.mainloop()