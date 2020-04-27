# Smart Random Music Player

# Version: 2016-12-19 00:44
# Running in Python 2.7.12
# http://github.com/nielsx

'''

TODO list:
- change Excel writing to SQLite database

Bugs:
- the last song played is not writen in database

Diferences Python 2.7 & Python 3.5
- tkinter (Python 3.5) and Tkinter(Python 2.7)
- set_main_folder method, glob(path)
- messagebox

'''

############################# VARIABLES TO MODIFY

FOLDER_MUSIC = r"C:\z\Musica"

MINIMUM_TIME_LISTENING = 5 # in order to save in database (percentage)

PROGRAM_NAME_LONG = "Smart Random Music Player"
PROGRAM_NAME_SHORT = "SR Music Player"

############################# IMPORT PYTHON LIBRARIES

# Python 2.7:

import glob2 # (external library)
from Tkinter import *
import tkMessageBox as messagebox
import tkFileDialog as filedialog
from tkFileDialog import askopenfilename
from tkFileDialog  import askdirectory


# Python 3.5:
'''
import glob 
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
'''

import os
import time
from random import randint
import webbrowser
import getpass
import datetime

############################# IMPORT EXTERNAL LIBRARIES

# For Windows open C:\Windows\System32\cmd.exe as administrator

from pygame import mixer # write in cmd: pip install pygame

import xlrd # write in cmd: pip install xlutils
import xlwt
from xlrd import open_workbook
from xlutils.copy import copy

from mutagen.mp3 import MP3 # write in cmd: pip install mutagen

############################# SIMPLE BASIC METHODS

def log(s): print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S | ")+s)
def logError(e,s):
    log("")
    try: log("*** "+s+"\n\n"+str(e)+"\n")
    except:
        log("*** "+s+"\n\n")
        traceback.print_exc()

def from_cwd(file_name): return os.path.join(os.path.dirname(__file__),file_name) # join current directory and file

############################# MAIN METHODS

def set_main_folder(path):
    global list_songs, number_songs
    try:

        # Python 2.7:
        
        list_songs = glob2.glob(path+"\\**\\*.mp3")
        list_songs.extend(glob2.glob(path+"\\**\\*.wma"))
        list_songs.extend(glob2.glob(path+"\\**\\*.m4a"))
        list_songs.extend(glob2.glob(path+"\\**\\*.flac"))
        

        # Python 3.5:
        '''
        list_songs = glob.glob(path+"\\**\\*.mp3",recursive=True)
        list_songs.extend(glob.glob(path+"\\**\\*.wma",recursive=True))
        list_songs.extend(glob.glob(path+"\\**\\*.m4a",recursive=True))
        list_songs.extend(glob.glob(path+"\\**\\*.flac",recursive=True))
        '''

        number_songs = len(list_songs)
        log("")
        log("I have recognized "+str(number_songs)+" songs in:")
        log(path)
        log("")
        play_random_song()
        if(number_songs>0): l7.config(text = \
            os.path.basename(os.path.normpath(path))+" \\")
    except Exception as e:
        number_songs = 0
        log(path)
        logError(e,"It is not possible to load that folder")

def play_this_song(full_path, position):
    global start_time, \
            song_playing, song_playing_position, \
            last_song, last_position, \
            song_duration, \
            MINIMUM_TIME_LISTENING

    last_song = song_playing
    last_position = song_playing_position
    
    song_playing_position = position
    song_playing = os.path.basename(full_path)
    
    log("["+str(position+1)+"] "+song_playing)
    
    #os.startfile(full_path) # open with OS default music player
    
    song_duration = 1 # to avoid zero division later
    
    try:
        audio = MP3(full_path)
        song_duration = audio.info.length # float in seconds
    except Exception as e:
        logError(e,"It was not possible to get song duration")
    
    try:
        mixer.init()
        mixer.music.load(open(full_path,"rb"))
        mixer.music.play()
        l3.config(text = song_playing) # warning: modifying GUI
    except Exception as e:
        logError(e,"It was not possible to play the song")
        l3.config(text = "")   
        
    try_write_last_song_database()
    start_time = time.time()
            
def open_excel_to_read(number_listened_songs):
    
    book = xlrd.open_workbook(from_cwd("db1.xls"))
    first_sheet = book.sheet_by_index(0)
    excel_songs=[]
    
    for j in range(1, number_listened_songs+1):
        excel_songs.append(first_sheet.cell(j,4).value)

    return excel_songs
   
def try_write_last_song_database():
    global start_time, last_song, last_position, list_songs
    
    try:
        
        elapsed_time = time.time() - start_time
        listening_percentage = int(100.0*(elapsed_time/song_duration))
        if listening_percentage>100: listening_percentage = 100

        if(last_song!="" and listening_percentage > MINIMUM_TIME_LISTENING):

            file = open(from_cwd('db1.dat'), 'r')
            number_listened_songs = int(file.read())
            file.close()

            excel_songs = open_excel_to_read(number_listened_songs)

            rb = open_workbook(from_cwd("db1.xls"))
            wb = copy(rb)
            s = wb.get_sheet(0)
            data_to_save = \
            [
                int(time.time()), # unix epoch time
                getpass.getuser()+"-"+sys.platform, # user device
                (last_position+1), # id of song in that device, begins in 1 and
                                      # it is 0 is when user have selected a song
                listening_percentage, # precentage of elapsed time listening that song respect the duration of that song
                last_song, # name of song
            ]
            
            # Excel (((A1/60)/60)/24)+FECHA(1970,1,1) to read unix-epoch

            for j in range(0, len(data_to_save)):
                s.write(number_listened_songs+1,j,data_to_save[j])

            # preparando un histograma de frecuencias

            h = buscar_contar_repetidos(excel_songs)
            for i in range(0, len(h)):
                s.write(i+1,len(data_to_save)+5,h[i][1]) # number of repetittions of that song
                s.write(i+1,len(data_to_save)+6,h[i][0]) # song name
               
            # guardando libro Excel
            wb.save(from_cwd('db1.xls'))

            file = open(from_cwd("db1.dat"), "w")
            file.write(str(number_listened_songs+1))
            file.close()
            
    except Exception as e:
        logError(e,"It was not possible to save last song in database")
            
def play_random_song():
    global list_songs, song_playing, message_no_songs
    
    if len(list_songs)==0:
        messagebox.showinfo(PROGRAM_NAME_SHORT, message_no_songs)
    else:
        random_position = randint(0,len(list_songs))
        random_song = list_songs[random_position]
        play_this_song(random_song, random_position)

def buscar_contar_repetidos(a):
    b=[]
    for i in range(0,len(a)):
        num=1
        val=a[i]
        for j in range(0,len(a)):
            if(i==j):
                val=a[j]
                first_time=True
            if(i!=j and a[i]==a[j]
               ):
                num = num + 1
                first_time=False
        if(first_time):
            b.append([val,num])
    return b
    
############################# CALLBACKS (GUI METHODS/EVENTS)
    
def b1_event(): # real suffle
    play_random_song()

def b4_event(): # play again
    play_this_song(list_songs[song_playing_position], song_playing_position)
 
def b2_event(): # slect a song to play, gives '-1' as position
    path=askopenfilename()
    if path!="": play_this_song(path,-1)

def b5_event(): # open file location
    global list_songs, song_playing_position
    path = os.path.dirname(list_songs[song_playing_position])
    webbrowser.open_new(path)

def b3_event(): # go back
    global list_songs, last_position
    last_song_full_path = list_songs[last_position]
    play_this_song(last_song_full_path, last_position)
    
def b7_event(): # open file location
    path=askdirectory()
    if path!="": set_main_folder(path)
    
'''
def right_clic1(event): # open file location
    path=askdirectory()
    if path!="": set_main_folder(path)
'''
    
def link_event1(event): # link to web of about/author
    webbrowser.open_new(r"https://github.com/nielsx?tab=repositories")

def link_event2(event): # enter mouse
    global start_time, song_playing
    if(not is_paused and song_playing!=""):
        elapsed_time = int(time.time() - start_time)
        m,s=divmod(elapsed_time, 60)
        listening_percentage = int(100.0*elapsed_time/song_duration)
        if listening_percentage>100: listening_percentage = 100
        l5.config(text = '{:02.0f}'.format(m)+":"+'{:02.0f}'.format(s))
        l6.config(text = str(listening_percentage)+"%")

def link_event3(event): # leave mouse
    global song_playing
    if(not is_paused and song_playing!=""):
        l5.config(text = "")
        l6.config(text = "")

def on_closing(): # close
    global song_playing, song_playing_position
    if messagebox.askokcancel(PROGRAM_NAME_SHORT, "Do you want to quit?"):
        try:
            mixer.music.stop()
            last_song = song_playing
            last_position = song_playing_position
            try_write_last_song_database()
            #messagebox.showinfo(PROGRAM_NAME_SHORT, "debug")
        except Exception as e: logError(e,"")
        root.destroy()

def b6_event(): # pause
    global is_paused, paused_time, start_time
    if is_paused:
        mixer.music.unpause()
        is_paused = not is_paused
        start_time = start_time + (time.time()-paused_time)
        l3.config(text = song_playing) # warning: modifying GUI
    else:
        mixer.music.pause()
        is_paused = not is_paused
        paused_time = time.time()
        l3.config(text = "[ P A U S E D ]") # warning: modifying GUI

def key_event1(event):
    play_random_song()

def key_event2(event):
    play_random_song()
    
############################# GRAPHICAL USER INTERFACE

root = Tk()
#root.wm_attributes("-topmost", 1) # always on top
root.wm_title(PROGRAM_NAME_SHORT)
root.resizable(width=False, height=False)
root.bind("<Enter>", link_event2)
root.bind("<Leave>", link_event3)
root.bind("<Key-space>", key_event1)
root.bind("<Return>", key_event2)
#root.bind("<Button-3>", right_clic1)
root.protocol("WM_DELETE_WINDOW", on_closing)

############# HEADER

headerFrame1 = Frame(root)
headerFrame1.pack()

l7 = Label(headerFrame1, text="")
l7.pack(side=LEFT)

l3 = Label(headerFrame1, text=PROGRAM_NAME_LONG)
l3.pack(side=TOP)

############# BUTTONS

b1 = Button(root, text="P L A Y    N E X T    R A N D O M    S O N G", command=b1_event)
b1.config( height = 2, width = 40, bg="grey", fg="white");
b1.pack()

btnFrame1 = Frame(root)
btnFrame1.pack()

b3 = Button(btnFrame1, text="G O    B A C K", command=b3_event)
b3.config( height = 1, width = 12 );
b3.pack(side=LEFT)

b4 = Button(btnFrame1, text="P L A Y    A G A I N", command=b4_event)
b4.config( height = 1, width = 16 );
b4.pack(side=LEFT)

b6 = Button(btnFrame1, text="P A U S E", command=b6_event)
b6.config( height = 1, width = 9 );
b6.pack(side=LEFT)

btnFrame2 = Frame(root)
btnFrame2.pack()

b2 = Button(btnFrame2, text="SELECT FILE", command=b2_event)
b2.config( height = 1, width = 10);
b2.pack(side=LEFT)

b7 = Button(btnFrame2, text="SET FOLDER", command=b7_event)
b7.config( height = 1, width = 10, bg="grey", fg="white" );
b7.pack(side=LEFT)

b5 = Button(btnFrame2, text="OPEN FILE LOCATION", command=b5_event)
b5.config( height = 1, width = 17 );
b5.pack(side=LEFT)

############# FOOTER

footerFrame = Frame(root)
footerFrame.pack()

l5 = Label(footerFrame, text="")
l5.pack(side=LEFT)

Label(footerFrame, text="Developed by:").pack(side=LEFT)

l4 = Label(footerFrame, text="github.com/nielsx", fg="blue", cursor="hand2")
l4.bind("<Button-1>", link_event1)
l4.pack(side=LEFT)

l6 = Label(footerFrame, text="")
l6.pack(side=LEFT)

############################# INITIALIZATION OF VARIABLES

message_no_songs = "There are no songs in the current folder,\n\n" +\
                   "choose another one pressing [SET FOLDER]."

list_songs = []

start_time = time.time()
elapsed_time = 0
last_position = 0 # song id based on recursive list of main folder
last_song = ""
song_playing_position = 0 # song id based on recursive list of main folder
song_playing = ""
song_duration = 0

paused_time = 0
is_paused = False

############################# INITIAL ROUTINE

try:
    
    log(PROGRAM_NAME_LONG)
    log("Hello "+getpass.getuser()+", I am a different music player,")
    log("and I will improve your music experience here.\n")
    
    set_main_folder(FOLDER_MUSIC) # contains  play_random_song()

except Exception as e:
    logError(e,"Some problems in the initial routine")

mainloop() # lounch the GUI
