from tkinter import *
import numpy as np
from numpy import percentile
import os, imutils,  cv2, csv, shutil
from PIL import Image, ImageTk
from PIL import Image as im
from tkinter import filedialog
import os.path
from pathlib import Path
from scipy.spatial import distance
from tqdm import tqdm
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from math import log10, floor, pi
import numpy.polynomial.polynomial as poly
from datetime import date
import pyocr, pyocr.builders

"""
SOFIA Size of Oxidation Feature from Image Analysis
Allows the user to load an image and quickly crop, threshold, and detect edges to isolate lines for the purpose
of measuring scale thicknesses for internal and external oxidation.
Created by Padraig Stack for ORNL
Last modified August 24, 2021
"""

today = date.today()
today.strftime("%B %d")
#Initial fonts
if today.strftime("%B %d") == "April 1":
    font1 = ("Comic Sans MS", 15)
    font2 = ("Comic Sans MS", 13)
else:
    font1 = ("Helvetica", 16)
    font2 = ("Helvetica", 14)

class MainWindow:

 #Establish the main menu

    def __init__(self,main_menu): ##Initial Menu
        self.main_menu = main_menu
        self.main_menu.title("Main Menu")
        self.main_menu.configure(bg="gray69")
        
        Label(self.main_menu, text = "Please select the following menus to use", font = font1).grid(row = 0, columnspan = 2)
        self.external_oxidation_menu_btn = Button(self.main_menu, text="External Oxidation (CC Prep)", font = font1, bg="skyblue", command = self.external_oxidation_menu)
        self.external_oxidation_menu_btn.grid(row = 1, column = 0)
        Label(main_menu, text="This will let you calculate the shortest distance between select contours\nor prepare samples for the concavity calculator", font = font2).grid(row =1, column = 1, pady = (5,0), sticky="W")

        self.concavity_menu_btn = Button(self.main_menu, text="Concavity Calculation", font = font1, bg="slate blue", command = self.concavity_menu)
        self.concavity_menu_btn.grid(row = 2, column = 0)
        Label(main_menu, text="This will let you find concavity of the lower line. \nCompares thicknesses at concave and concave regions", font = font2).grid(row=2, column = 1, sticky="W", pady=(5,0))

        self.internal_oxidation_menu_btn = Button(self.main_menu, text="Internal Oxidation", font= font1, bg="purple2", command = self.internal_menu)
        self.internal_oxidation_menu_btn.grid(row=3, column=0)
        Label(main_menu, text="Prepare CSVs to measure internal oxidation\nAlso measures continuity in slices", font = font2).grid(row=3, column=1, sticky="W", pady=(5,0))
        
        exit_messages = ["Please don't leave, there's more corrosion to analyze", "I wouldn't leave if I were you. work is much worse", "Don't leave yet -- There's corrosion around that corner", "Go ahead and leave. See if I care.", "Are you sure you want to quit this great script?",
                        "You want to quit? Then, thou hast lost an eighth!", "This is no message! Page intentionally left blank"]
        i = np.random.randint(len(exit_messages)) #Adaptations of quit messages from DOOM, sorry if it is unprofessional

        self.exit_btn = Button(self.main_menu, text="Exit Program", font= font1, bg="tomato", command = lambda: (self.main_menu.destroy(), print(exit_messages[i])))
        self.exit_btn.grid(row=4, column=0, pady=(5,0))

    def reset_button(self): ##Resets the menu to start again
        if "cbtn" in dir(self):
            self.cbtn.destroy()
            del self.cbtn
        if "thresh_btn" in dir(self):
            self.thresh_btn.destroy()
            del self.thresh_btn
        if "edge_btn" in dir(self):
            self.edge_btn.destroy()
            del self.edge_btn
        if "save_csv_btn" in dir(self):
            self.save_csv_btn.destroy()
            del self.save_csv_btn
        if "crop_status" in dir(self):
            self.crop_status.grid_remove()
            del self.crop_status
        if "contour_status" in dir(self):
            self.contour_status.grid_remove()
            del self.contour_status
        if "save_name_label" in dir(self):
            self.save_name_label.grid_remove()
            del self.save_name_label
        if "scale_ratio" in dir(self):
            del self.scale_ratio
        if "scale_status" in dir(self):
            del self.scale_status
        if "thresh_status" in dir(self):
            self.thresh_status.grid_remove()
        self.status_path.configure(text="There is no loaded image", font=font2)
        self.status_path.update()

    def external_oxidation_menu(self): ##Creates the main menu for external oxidation image analysis
        self.in_or_ex = 1
        self.root = Toplevel()
        self.main_menu.withdraw()
        self.root.title("Auto Measurement")
        self.root.configure(bg="gray69")
        self.root.minsize(300,300)

        self.path_btn = Button(self.root, text="Please select the image you would like to use", font = font1, bg="OliveDrab1", command = self.select_image)
        self.path_btn.grid(row = 0, column = 0)
        self.status_path = Label(self.root, text="There is no loaded image", font = font2)
        self.status_path.grid(row = 0, column = 1)

        self.current_dir = os.getcwd()
        self.unworked_dir = self.current_dir+"/unworkedcsv/"
        check_dir = Path(self.unworked_dir)
        if check_dir.exists() is False:
            os.mkdir(self.unworked_dir)
            os.mkdir(self.current_dir+"/workedcsv")
        waiting_files = len(os.listdir(self.unworked_dir))//3
        if waiting_files > 0:
            self.short_dist_btn = Button(self.root, text="Calculate Shortest Distance", font = font1, bg="dodger blue", command = self.shortest_distance)
            self.short_dist_btn.grid(row=6, column=0, pady=(10,0))
            if waiting_files ==1:
                self.calculate_status = Label(self.root, text="There is "+str(waiting_files)+" image waiting for calculations", font = font2)
                self.calculate_status.grid(row =6, column = 1, sticky="W", pady=(10,0))
            else:
                self.calculate_status = Label(self.root, text="There are "+str(waiting_files)+" images waiting for calculations", font = font2)
                self.calculate_status.grid(row =6, column = 1, sticky="W", pady=(10,0))
            self.total_calculations_entry = Entry(self.root, font=font2)
            self.total_calculations_entry.insert(END, "500")
            self.total_calculations_entry.grid(row=7, column = 1)
            self.total_calculations_label = Label(self.root, text="The above determines the number of\nshortest distance calculations performed", font=font2)
            self.total_calculations_label.grid(row=8, column = 1, sticky="W")
            reverse_profiles = ["Bottom to Top", "Top to Bottom", "Both", "Vertical", "All of the Above"]
            self.reverse_profile = StringVar()
            self.reverse_profile.set(reverse_profiles[0])
            self.reverse_profile_drop = OptionMenu(self.root, self.reverse_profile, *reverse_profiles)
            self.reverse_profile_drop.config(bg="deep sky blue", font=font2)
            self.reverse_profile_drop.grid(row=7, column = 0)
            self.reverse_status = Label(self.root, font=font2, text="The droplist determines the direction \nthe shortest distance is calculated")
            self.reverse_status.grid(row=8, column =0)
            reverse_drop_list = self.root.nametowidget(self.reverse_profile_drop.menuname)
            reverse_drop_list.config(font=font2)

        self.reset_btn = Button(self.root, text="Reset", font=font1, bg="chocolate1", command=lambda:[self.reset_button()])
        self.reset_btn.grid(row=9, column=0, sticky="S", pady=10)
        self.return_btn = Button(self.root, text="Return to Main Menu", font = font1, bg="peach puff", command = lambda:[self.root.destroy(), self.main_menu.deiconify()])
        self.return_btn.grid(row = 9, column= 1, sticky="S", pady=10)

    def concavity_menu(self): ##Uses CSV data from internal/external measurements to measure concavities of the oxide interface
        self.cc_menu = Toplevel()
        self.main_menu.withdraw()
        self.cc_menu.title("Concavity Calculator")
        self.cc_menu.configure(bg="gray69")
        self.cc_menu.minsize(300,300)


        return_btn = Button(self.cc_menu, text="Return to Main Menu", font = font1, bg="peach puff", command = lambda:[self.cc_menu.destroy(), self.main_menu.deiconify()])
        return_btn.grid(row = 6, columnspan = 2)

        csv_select = Button(self.cc_menu, text="Select CSVs", font=font1, bg="deep sky blue", command = self.load_csv)
        csv_select.grid(row = 1, column = 0)
        self.cc_csv_status = Label(self.cc_menu, text="Select the csv you would like to use for calculations", font=font2)
        self.cc_csv_status.grid(row=1,column = 1)
    
    def internal_menu(self): ##Creates the main menu for internal oxidation image analysis
        self.in_or_ex = 0
        self.root = Toplevel()
        self.main_menu.withdraw()
        self.root.title("Internal Oxidation")
        self.root.configure(bg="gray69")
        self.root.minsize(300,300)

        path_btn = Button(self.root, text="Please select the image you would like to use", font = font1, bg="OliveDrab1", command = self.select_image)
        path_btn.grid(row = 0, column = 0)
        self.status_path = Label(self.root, text="There is no loaded image", font = font2)
        self.status_path.grid(row = 0, column = 1)

        self.current_dir = os.getcwd()
        worked_dir = self.current_dir+"/worked-internalcsv/"
        check_dir = Path(worked_dir)
        if check_dir.exists() is False:
            os.mkdir(worked_dir)
        
        reset_btn = Button(self.root, text="Reset", bg="chocolate1", font=font1, command=self.reset_button)
        reset_btn.grid(row=8, column=0, sticky="S", pady=10)
        return_btn = Button(self.root, text="Return to Main Menu", font = font1, bg="peach puff", command = lambda:[self.root.destroy(), self.main_menu.deiconify()])
        return_btn.grid(row = 8, column = 1, sticky="S", pady=10)

 #Internal and External functions
  #Image selection/property generation
    def select_image(self): ##Allows the user to select an image to analyse
        self.reset_button()
        self.path = filedialog.askopenfilename(filetypes = [("Image", ".bmp"), ("Image", ".tif"), ("Image", ".jpg"), ("Image", ".png")])
        if len(self.path) > 0:
            self.directory = os.path.dirname(self.path)
            self.filename = os.path.basename(self.path)
            self.orig_img = cv2.imread(self.path, 0)
            self.img_width = self.orig_img.shape[1]
            self.img_height = self.orig_img.shape[0]
            if self.img_width > self.img_height:
                self.image_ratio = self.img_width // 1000
            else:
                self.image_ratio = self.img_height // 1000
            if self.image_ratio == 0:
                self.image_ratio = int(1)
            self.scale_values()
            self.center_circle = int(self.image_ratio)
            self.label_text = int((self.image_ratio//2)+1)
            self.scale_bar = int(round_to_1(self.img_width)/10)
            image_area = self.img_width * self.img_height
            self.area_thresh = int(image_area * .00004)
            self.contour_buffer = int(self.image_ratio*3.125)
            self.crackbuffer = int(5)
            self.status_path.configure(text=("The current loaded image is: " + self.filename), font=font2)
            self.status_path.update()
            if "cbtn" not in dir(self):
                self.cbtn = Button(self.root, text="Crop the image", bg="PaleTurquoise1",  font=font1, command = self.crop_image)
                self.cbtn.grid(row = 1, column = 0)
        else:
            self.status_path.configure(text="You have not selected a new image, please select one", font=font2)
            self.status_path.update()
        
    def scale_values(self, pct=2): ##Recallable dynamic resolution function            
        monitor_width = self.root.winfo_screenwidth() #Obtains screen size for scaling purposes
        if pct != 2:
            if pct <= 0.3:
                modifier = 1
            elif pct <= 0.4:
                modifier = 0.8
            elif pct <= 0.5:
                modifier = 0.7
            elif pct <= 0.6:
                modifier = 0.6
            else:
                modifier = 0.5
        else:
            modifier = 1
        if self.in_or_ex == 1:
            if monitor_width >= 1920 and monitor_width < 2560: #Adjusts the image sizes based off monitor resolution  width (assumed 16:9)
                self.fullsize = int((75/self.image_ratio)*modifier)
                self.crop_resize = int((135/self.image_ratio)*modifier)
                self.croped_resize = int((165/self.image_ratio)*modifier)
                self.contour_resize = int((140/self.image_ratio)*modifier)
                self.thresh_width = int((165*self.image_ratio))
            elif monitor_width < 1920:
                self.fullsize = int((50/self.image_ratio)*modifier)
                self.crop_resize = int((90/self.image_ratio)*modifier)
                self.croped_resize = int((110/self.image_ratio)*modifier)
                self.contour_resize = int((80/self.image_ratio)*modifier)
                self.thresh_width = int(110*self.image_ratio)
            else:
                self.fullsize = int((100/self.image_ratio)*modifier)
                self.crop_resize = int((180/self.image_ratio)*modifier)
                self.croped_resize = int((220/self.image_ratio)*modifier)
                self.contour_resize = int((160/self.image_ratio)*modifier)
                self.thresh_width = int(220*self.image_ratio)
            self.vertical_check = int(4*self.image_ratio)
            self.edge_limit = int(25*self.image_ratio)
        else:
            if monitor_width >= 1920 and monitor_width < 2560: #Adjusts the image sizes based off monitor resolution  width (assumed 16:9)
                self.fullsize = int((70/self.image_ratio)*modifier)
                self.crop_resize = int((150/self.image_ratio)*modifier)
                self.croped_resize = int((150/self.image_ratio)*modifier)
                self.contour_resize = int((105/self.image_ratio)*modifier)
                self.thresh_width = int(150*self.image_ratio)
            elif monitor_width < 1920:
                self.fullsize = int((45/self.image_ratio)*modifier)
                self.crop_resize = int((100/self.image_ratio)*modifier)
                self.croped_resize = int((100/self.image_ratio)*modifier)
                self.contour_resize = int((70/self.image_ratio)*modifier)
                self.thresh_width = int(100*self.image_ratio)
            else:
                self.fullsize = int((90/self.image_ratio)*modifier)
                self.crop_resize = int((160/self.image_ratio)*modifier)
                self.croped_resize = int((200/self.image_ratio)*modifier)
                self.contour_resize = int((140/self.image_ratio)*modifier)
                self.thresh_width = int(200*self.image_ratio)
            self.vertical_check = int(2*self.image_ratio)
            self.edge_limit = int(3*self.image_ratio)

 #Crop menu and scale bar determining
    def crop_image(self): ##Creates a menu to crop the image. Also contains the feature to set a manual scale
        if "crop_menu" in dir(self):
            self.crop_menu.destroy()
        if "crop_close" in dir(self):
            del self.crop_close
        self.crop_menu = Toplevel()
        self.crop_menu.title=("Cropping Menu")
        self.crop_menu.configure(bg="gray69")
        self.crop_menu.minsize(300,300)

        Label(self.crop_menu, text=("The image you have loaded is "  +str(self.img_height) +" pixels tall"
        "\nAdjust the parameters until the entire scale is in the frame"), bg="thistle1", font=font2).grid(row = 0, columnspan = 2)

        orig_scale = self.orig_img.copy() #Creates a scale on the side of the image to help with cropping
        for i in range(self.img_height//self.scale_bar):
            cv2.putText(orig_scale, str(i*self.scale_bar), (0, (self.img_height-(i*self.scale_bar))), cv2.FONT_HERSHEY_SIMPLEX, (self.label_text+2), (255,255,255),(self.center_circle+3))
            cv2.putText(orig_scale, "____", (0, (self.img_height-(i*self.scale_bar))), cv2.FONT_HERSHEY_SIMPLEX, (self.label_text+2), (255,255,255),(self.center_circle))
        
        
        orig_resize = resize(orig_scale, self.fullsize) #Prepares and adds an image to the GUI
        resize_width = orig_resize.shape[1]
        resize_height =  orig_resize.shape[0]
        orig_resize = ImageTk.PhotoImage(Image.fromarray(orig_resize))
        self.crop_canvas = Canvas(self.crop_menu, width=resize_width, height=resize_height)
        self.crop_canvas.grid(row = 10, columnspan = 3)
        self.cropping_image= self.crop_canvas.create_image(0,0, image= orig_resize, anchor=NW)
        self.crop_canvas.update()

        Label(self.crop_menu, text="Lower Height", font= font2).grid(row = 2, column = 0, sticky = "E") #Entry for lower height
        self.lower_crop = Scale(self.crop_menu, from_=0, to=self.img_height, orient = HORIZONTAL, length=400, command= self.crop_update)
        self.lower_crop.set(0)
        self.lower_crop.grid(row = 2, column = 1, columnspan = 2, sticky = "W")

        Label(self.crop_menu, text="Upper Height", font= font2).grid(row = 1, column = 0, sticky = "E") #Entry for upper height
        self.upper_crop = Scale(self.crop_menu, from_=0, to=self.img_height, orient = HORIZONTAL, length=400, command= self.crop_update)
        self.upper_crop.set(self.img_height)
        self.upper_crop.grid(row = 1, column = 1, columnspan = 2, sticky = "W")

        if "scale_ratio" not in dir(self):
            ratio, ratio_text, bar_length = scale_reader(self.path)
            if ratio == "Error":
                self.scale_status = Label(self.crop_menu, text="The scale ratio was not determined automatically.\nPlease determine it using on of the buttons.Adjust crop if necessary", font=font2)
                self.scale_status.grid(row = 6, column = 0, columnspan = 2)
            elif ratio == "No_tool":
                self.scale_status = Label(self.crop_menu, text="The scale ratio was not determined automatically. You do not have to required tools installed.\nPlease determine it using on of the buttons.Adjust crop if necessary", font=font2)
                self.scale_status.grid(row = 6, column = 0, columnspan = 2)
            else:
                self.scale_status = Label(self.crop_menu, text="The scale ratio has been determined automatically! The scale bar text read was: "+str(ratio_text)+".\nYou can override scale length with the below entry. Adjust crop if necessary", font=font2)
                self.scale_status.grid(row = 6, column = 0, columnspan = 2)
                self.scale_ratio = ratio
                self.OCR_override_entry = Entry(self.crop_menu, font=font2)
                self.OCR_override_entry.insert(END, str(ratio_text))
                self.OCR_override_entry.grid(row = 7, column = 0)
                self.bar_length = bar_length
        else:
            self.scale_status = Label(self.crop_menu, text="The scale ratio from the previous image is currently being used.\nOverride using the other scale options. Adjust crop if necessary", font=font2)
            self.scale_status.grid(row=6, column = 0, columnspan = 2)
            scale_reader_redo_btn = Button(self.crop_menu, text="Redo Auto Scale Reader", bg="MediumOrchid2", font=font2, command = self.scale_reader_redo)
            scale_reader_redo_btn.grid(row = 7, column = 0)

        scale_reader_btn = Button(self.crop_menu, text="Scale Bar Selection", bg="lawn green", font=font2, command = lambda: self.scale_reader_manual(resize_width))
        scale_reader_btn.grid(row =7, column = 1)
        self.scale_manual_entry = Entry(self.crop_menu, font=font2)
        self.scale_manual_entry.insert(END, "Enter the scale ratio here")
        self.scale_manual_entry.grid(row = 6, column = 2, sticky="S")
        self.scale_entry_btn = Button(self.crop_menu, text="Use Value in Entry (px/um)", bg="dark orange", font=font2, command = self.set_scale_manual_entry)
        self.scale_entry_btn.grid(row=7, column=2)

    def crop_update(self, x): ##Reads the values of the crop sliders to update the image displayed in the crop menu
        self.lower_crop_val = int(float(self.img_height)-float(self.lower_crop.get()))
        self.upper_crop_val = int(float(self.img_height)-float(self.upper_crop.get()))

        self.crop = self.orig_img.copy()
        for i in range(self.img_height//self.scale_bar):
            cv2.putText(self.crop, str(i*self.scale_bar), (0, (self.img_height-(i*self.scale_bar))), cv2.FONT_HERSHEY_SIMPLEX, (self.label_text+2), (255,255,255),(self.center_circle+2))
            cv2.putText(self.crop, "____", (0, (self.img_height-(i*self.scale_bar))), cv2.FONT_HERSHEY_SIMPLEX, (self.label_text+2), (255,255,255),(self.center_circle))
        self.crop = self.crop[self.upper_crop_val:self.lower_crop_val, 0:self.img_width]

        crop_pct = (self.lower_crop_val - self.upper_crop_val)/self.img_height
        self.scale_values(crop_pct)

        self.crop_resize = resize(self.crop, int((75/self.image_ratio)))
        resize_width = self.crop_resize.shape[1]
        resize_height =  self.crop_resize.shape[0]
        self.crop_canvas.config(width=resize_width, height=resize_height)
        self.crop_resize = ImageTk.PhotoImage(Image.fromarray(self.crop_resize))
        self.crop_canvas.itemconfigure(self.cropping_image, image=self.crop_resize)
        self.crop_canvas.update()

        if "crop_close" not in dir(self):
            self.crop_close = Button(self.crop_menu, text = "Close and Continue", bg = "tomato", font= font2, command = self.crop_close_button)
            self.crop_close.grid(row = 9, column = 1)
            self.thresh_btn = Button(self.root, text="Adjust Thresholds", font = font1, bg="DeepSkyBlue2", command = self.threshold_image)
            self.thresh_btn.grid(row = 2, column = 0)
            self.crop_status = Label(self.root, text = "Crop has been updated", font = font1)
            self.crop_status.grid(row = 1, column = 1, sticky = "W")
    
    def crop_close_button(self):
        if "OCR_override_entry" in dir(self):
            self.scale_ratio = float(self.bar_length/int(self.OCR_override_entry.get()))
            del self.OCR_override_entry
            del self.bar_length
        self.crop_menu.destroy()

    def scale_reader_manual(self, resize_width): ##Manual method to determine a scale. Crops the full image to isolate the scale bar
        if "scale_menu" in dir(self):
            self.scale_menu.destroy()
        self.crop_menu.withdraw()
        self.scale_menu = Toplevel()
        self.scale_menu.title=("Scale Cropping Menu")
        self.scale_menu.configure(bg="gray69")
        self.scale_menu.minsize(resize_width, 300)
        
        Label(self.scale_menu, text=("Adjust the height until the scale bar is isolated"), bg="thistle1", font=font2).grid(row = 0, columnspan = 2)

        orig_scale = self.orig_img.copy() #Creates a scale on the side of the image to help with cropping  
        orig_resize = resize(orig_scale, self.fullsize) #Prepares and adds an image to the GUI
        resize_width = orig_resize.shape[1]
        resize_height =  orig_resize.shape[0]
        orig_resize = ImageTk.PhotoImage(Image.fromarray(orig_resize))
        self.scale_canvas = Canvas(self.scale_menu, width=resize_width, height=resize_height)
        self.scale_canvas.grid(row = 5, column = 1, columnspan = 2, pady=5)
        self.scale_crop_img = self.scale_canvas.create_image(0,0, image= orig_resize, anchor=NW)
        self.scale_canvas.update()
        

        Label(self.scale_menu, text="Lower Height", font= font2).grid(row = 2, column = 0, sticky = "E") #Entry for lower height
        self.y_lower_crop = Scale(self.scale_menu, from_=0, to=self.img_height, orient = HORIZONTAL, length=400, command= self.scale_update)
        self.y_lower_crop.set(0)
        self.y_lower_crop.grid(row = 2, column = 1, columnspan = 2, sticky = "W")

        Label(self.scale_menu, text="Upper Height", font= font2).grid(row = 1, column = 0, sticky = "E") #Entry for upper height
        self.y_upper_crop = Scale(self.scale_menu, from_=0, to=self.img_height, orient = HORIZONTAL, length=400, command= self.scale_update)
        self.y_upper_crop.set(self.img_height)
        self.y_upper_crop.grid(row = 1, column = 1, columnspan = 2, sticky = "W")

        Label(self.scale_menu, text="Left Boundary", font= font2).grid(row = 3, column = 0, sticky = "E") #Entry for lower height
        self.x_lower_crop = Scale(self.scale_menu, from_=0, to=self.img_width, orient = HORIZONTAL, length=400, command= self.scale_update)
        self.x_lower_crop.set(0)
        self.x_lower_crop.grid(row = 3, column = 1, columnspan = 2, sticky = "W")

        Label(self.scale_menu, text="Right Boundary", font= font2).grid(row = 4, column = 0, sticky = "E") #Entry for upper height
        self.x_upper_crop = Scale(self.scale_menu, from_=0, to=self.img_width, orient = HORIZONTAL, length=400, command= self.scale_update)
        self.x_upper_crop.set(self.img_width)
        self.x_upper_crop.grid(row = 4, column = 1, columnspan = 2, sticky = "W")

        scale_btn = Button(self.scale_menu, text="Done Cropping", bg="purple", font=font2, command = self.scale_select)
        scale_btn.grid(row = 6, column = 1)

        exit_btn = Button(self.scale_menu, text="Return to Crop Menu", bg="tomato", font=font2, command= lambda: (self.scale_menu.destroy(), self.crop_menu.deiconify()))
        exit_btn.grid(row=6, column = 2)

    def set_scale_manual_entry(self): ##Reads from an entry box to override the automatic or to avoid using the manual scale reading
        if float(self.scale_manual_entry.get()) != 0:
            self.scale_ratio = float(self.scale_manual_entry.get())
            self.scale_status.configure(text="The scale ratio has been determined by manual entry.\nContinue to crop the image for thresholds")
            self.scale_status.update()
    
    def scale_reader_redo(self): ##If the previous image you worked with is not in the same dimmensions as the new image you can redo the automatic scale reading
        ratio, ratio_text = scale_reader(self.path)
        if ratio == "Error":
            self.scale_status.configure(text="Scale ratio was not determined automatically. Using previous ratio.\nYou can override using an alternative method. Adjust crop if necessary")
            self.scale_status.update()
        else:
            self.scale_status.configure(text="The scale ratio has been re-determined automatically!\nThe scale bar text read was: "+str(ratio_text)+". You can override using buttons. Adjust crop if necessary")
            self.scale_status.update()
            self.scale_ratio = ratio

    def scale_update(self,x): ##Reads the values of the crop sliders to help measure the scale bar. Updates the image
        self.scale_lower_crop_val = int(float(self.img_height)-float(self.y_lower_crop.get()))
        self.scale_upper_crop_val = int(float(self.img_height)-float(self.y_upper_crop.get()))
        self.scale_left_val = int(self.x_lower_crop.get())
        self.scale_right_val = int(self.x_upper_crop.get())
        
        scale_crop = self.orig_img.copy()
        scale_crop = scale_crop[self.scale_upper_crop_val:self.scale_lower_crop_val, self.scale_left_val:self.scale_right_val]    
        scale_resize = resize(scale_crop, int((75/self.image_ratio)))
        resize_width = scale_resize.shape[1]
        resize_height =  scale_resize.shape[0]
        self.scale_canvas.config(width=resize_width, height = resize_height)
        self.scale_resize = ImageTk.PhotoImage(Image.fromarray(scale_resize))
        crop = self.orig_img[self.scale_upper_crop_val:self.scale_lower_crop_val, 0:self.img_width]

        self.scale_canvas.itemconfigure(self.scale_crop_img, image=self.scale_resize)
        self.scale_canvas.update()
    
    def scale_select(self): ##Creates a menu to select between two threhsolds to help the computer identify the scale bar
        if "scale_select_menu" in dir(self):
            self.scale_select_menu.destroy()
        self.scale_menu.withdraw()
        self.scale_select_menu = Toplevel()
        self.scale_select_menu.title("Scale Selection")
        self.scale_select_menu.configure(bg="gray69")

        scale_image = self.orig_img.copy()
        scale_image = scale_image[self.scale_upper_crop_val:self.scale_lower_crop_val, self.scale_left_val:self.scale_right_val]

        thresh_img_1 = cv2.inRange(scale_image, 200, 255)
        thresh_img_2 = cv2.inRange(scale_image, 0, 50)

        thresh_img_1_resize = resize(thresh_img_1, 75)
        thresh_img_1_resize = ImageTk.PhotoImage(Image.fromarray(thresh_img_1_resize))
        thresh_img_2_resize = resize(thresh_img_2, 75)
        thresh_img_2_resize = ImageTk.PhotoImage(Image.fromarray(thresh_img_2_resize))

        setting_1_btn = Button(self.scale_select_menu, image=thresh_img_1_resize, command = lambda: self.set_scale_threshold(thresh_img_1))
        setting_1_btn.image = thresh_img_1_resize
        setting_1_btn.grid(row =2, column = 0)
        setting_2_btn = Button(self.scale_select_menu, image=thresh_img_2_resize, command = lambda: self.set_scale_threshold(thresh_img_2))
        setting_2_btn.image = thresh_img_2_resize
        setting_2_btn.grid(row = 3, column = 0)

        if "scale_select_canvas" in dir(self):
            self.scale_select_canvas.destroy()
        if "set_scale_image" in dir(self):
            del self.set_scale_image

        self.scale_select_canvas = Canvas(self.scale_select_menu, width = scale_image.shape[1], height = scale_image.shape[0])
        self.scale_select_canvas.grid(row = 4, columnspan = 2)
        self.scale_select_canvas.update()
        self.scale_select_canvas.bind("<Button 1>", self.click_ratio)
        

        Label(self.scale_select_menu, text="Please click or enter the contour numbers\nof the edges of the scale bar:", font=font2).grid(row=5,column=0, sticky="E")
        self.scale_contour_input = Entry(self.scale_select_menu, font=font2)
        self.scale_contour_input.insert(END, "0")
        self.scale_contour_input.grid(row=5,column = 1, sticky="W")
        
        self.add_left_btn = Button(self.scale_select_menu, text="Add Contour as Left", bg="yellow", font=font2, command = self.add_left)
        self.add_left_btn.grid(row =6, column = 0)

        self.add_right_btn = Button(self.scale_select_menu, text="Add Contour as Right", bg="magenta2", font=font2, command = self.add_right)
        self.add_right_btn.grid(row =6, column = 1)
    
    def set_scale_threshold(self, image): ##Declares which of the two thresholds from the above menu that you want to work with for reading the scale bar
        image, self.scale_contours = self.label_center(image, 1)
        self.set_scale_img = ImageTk.PhotoImage(Image.fromarray(image))
        if "set_scale_image" not in dir(self):
            self.set_scale_image = self.scale_select_canvas.create_image(0,0, image = self.set_scale_img, anchor = NW)  
            self.scale_select_canvas.update()
        else:
            print("it tried")
            self.scale_select_canvas.itemconfigure(self.set_scale_image, image = self.set_scale_img)
            self.scale_select_canvas.update()
    
    def click_ratio(self, event): ##Uses the position of your mouse in the Tkinter canvas to figure out what contours on the image are closest to your mouse click
        mouse_x, mouse_y = event.x, event.y
        mouse_x = mouse_x
        mouse_y = mouse_y
        m_array = [(mouse_x, mouse_y)]

        near_contours = [(x,y) for x, y in self.click_tuple if (x in range(int(mouse_x - (self.image_ratio*20)), int(mouse_x + (self.image_ratio*20))) and y in range(int(mouse_y - (self.image_ratio*20)), int(mouse_y + (self.image_ratio*20))))]
        if len(near_contours) > 0:
            near_index = closest_node(m_array, near_contours)
            close_point = near_contours[near_index]
            contour_index = self.click_tuple.index(close_point)
            contour_number = self.click_index[contour_index]
            self.scale_contour_input.delete(0,"end")
            self.scale_contour_input.insert(END, contour_number)
    
    def label_center(self, threshedimage, scale = 0): ##Finds the coordinates for the first data point in all of the contours and if the area of the contour is above a certain size it will label the contour
        if scale == 0:
            threshedimage = cv2.copyMakeBorder(threshedimage, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
            threshedimage = cv2.medianBlur(threshedimage, 5)
            threshedimage = cv2.copyMakeBorder(threshedimage, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        cnts, _ = cv2.findContours(threshedimage, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        threshedimage = cv2.cvtColor(threshedimage, cv2.COLOR_GRAY2BGR)
        step = 0
        area_list = []
        area_number = []
        self.click_index = []
        if "click_tuple" in dir(self):
            del self.click_tuple
        for cnt in cnts:
            cx = cnt[0][0][0]
            cy = cnt[0][0][1]
            area = cv2.contourArea(cnt)
            b, _, _ = (threshedimage[(cy-1),(cx)])
            if b < 255:
                area_list.append(area)
                area_number.append(step)
                if scale == 0:
                    area_limit = self.area_thresh
                else:
                    area_limit = 0
                if area > area_limit:
                    cv2.circle(threshedimage, (cx, cy), (3*self.center_circle), (255, 0, 0), -1)
                    if cx < (3*(threshedimage.shape[1])/4):
                        if cy < ((threshedimage.shape[0])/4):
                            cv2.putText(threshedimage, (str(step)), (cx, cy+(2*int(self.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, (self.center_circle), (0,0,120),(self.center_circle+1))
                            cv2.putText(threshedimage, (str(step)), (cx, cy+(2*int(self.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (0,255,0),self.center_circle)
                        else:
                            cv2.putText(threshedimage, (str(step)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, (self.center_circle), (0,0,120),(self.center_circle+1))
                            cv2.putText(threshedimage, (str(step)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (0,255,0),self.center_circle)
                    else:
                        if cy < ((threshedimage.shape[0])/4):
                            cv2.putText(threshedimage, (str(step)), (cx-(3*int(self.scale_bar/10)), cy+(2*int(self.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, (self.center_circle), (0,0,120),(self.center_circle+1))
                            cv2.putText(threshedimage, (str(step)), (cx-(3*int(self.scale_bar/10)), cy+(2*int(self.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (0,255,0),self.center_circle)
                        else:
                            cv2.putText(threshedimage, (str(step)), (cx-(3*int(self.scale_bar/10)), cy), cv2.FONT_HERSHEY_SIMPLEX, (self.center_circle), (0,0,120),(self.center_circle+1))
                            cv2.putText(threshedimage, (str(step)), (cx-(3*int(self.scale_bar/10)), cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (0,255,0),self.center_circle)
                    contours_coord = (cx,cy),
                    if "click_tuple" not in dir(self):
                        self.click_tuple = (cx,cy),
                    else:
                        self.click_tuple = self.click_tuple + contours_coord
                    self.click_index.append(step)
            else:
                area_list.append(1)
                area_number.append(step)
            step += 1
            
        if len(cnts) >= 10:
            max_area_iter = 10
        elif len(cnts) >= 7:
            max_area_iter = 7
        elif len(cnts) >= 5:
            max_area_iter = 5
        else:
            max_area_iter = 1
        
        for i in range(max_area_iter):
            max_area = 1
            max_number = 0
            for j in range(len(area_list)):
                if area_list[j] > max_area:
                    max_area = area_list[j]
                    max_number = area_number[j]
            area_list[max_number] = 0
            cx = cnts[max_number][0][0][0]
            cy = cnts[max_number][0][0][1]
            cv2.circle(threshedimage, (cx, cy), self.center_circle+1, (135, 206, 235), -1)
            if cx < (3*(threshedimage.shape[1])/4):
                if cy < ((threshedimage.shape[0])/4):
                    cv2.putText(threshedimage, (str(max_number)), (cx, cy+(2*int(self.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, (self.center_circle), (255,192,0),(self.center_circle+1))
                else:
                    cv2.putText(threshedimage, (str(max_number)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, (self.center_circle), (255,192,0),(self.center_circle+1))
            else:
                if cy < ((threshedimage.shape[0])/4):
                    cv2.putText(threshedimage, (str(max_number)), (cx-(3*int(self.scale_bar/10)), cy+(2*int(self.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, (self.center_circle), (255,192,0),(self.center_circle+1))
                else:
                    cv2.putText(threshedimage, (str(max_number)), (cx-(3*int(self.scale_bar/10)), cy), cv2.FONT_HERSHEY_SIMPLEX, (self.center_circle), (255,192,0),(self.center_circle+1))
        return threshedimage, cnts

    def add_left(self): ##Used in the manual scale reader to determine the left side of the scale
        n_contour = self.scale_contours[int(self.scale_contour_input.get())]
        for d in range(len(n_contour)):
            XY_Coordinates = n_contour[d]
            currentx = int(XY_Coordinates[0][0])

            if "scale_leftmost" not in dir(self):
                self.scale_leftmost = currentx
            if currentx < self.scale_leftmost:
                self.scale_leftmost = currentx

        if ("scale_leftmost" in dir(self)) and ("scale_rightmost" in dir(self)):
            if "scale_compute_btn" not in dir(self):
                self.scale_compute_btn = Button(self.scale_select_menu, text="Calculate scale size", bg="lawn green", font=font2, command = self.scale_compute)
                self.scale_compute_btn.grid(row = 8, column = 1, sticky="W")
                self.scale_entry = Entry(self.scale_select_menu, font=font2)
                self.scale_entry.insert(END, "INSERT SCALE VALUE")
                self.scale_entry.grid(row = 8, column = 0, sticky="E")
                self.scale_warning.grid_remove()
        
        if "scale_warning" not in dir(self):
            self.scale_warning = Label(self.scale_select_menu, text="You have selected a left side, please select a right side")
            self.scale_warning.grid(row = 7, column = 1)
    
    def add_right(self): ##Used in the manual scale reader to determine the right side of the scale bar
        n_contour = self.scale_contours[int(self.scale_contour_input.get())]
        for d in range(len(n_contour)):
            XY_Coordinates = n_contour[d]
            currentx = int(XY_Coordinates[0][0])

            if "scale_rightmost" not in dir(self):
                self.scale_rightmost = currentx
            if currentx > self.scale_rightmost:
                self.scale_rightmost = currentx

        if ("scale_leftmost" in dir(self)) and ("scale_rightmost" in dir(self)):
            if "scale_compute_btn" not in dir(self):
                self.scale_compute_btn = Button(self.scale_select_menu, text="Calculate scale size", bg="lawn green", font=font2, command = self.scale_compute)
                self.scale_compute_btn.grid(row = 8, column = 1, sticky="W")
                self.scale_entry = Entry(self.scale_select_menu, font=font2)
                self.scale_entry.insert(END, "INSERT SCALE VALUE")
                self.scale_entry.grid(row = 8, column = 0, sticky="E")
                self.scale_warning.grid_remove()
        
        if "scale_warning" not in dir(self):
            self.scale_warning = Label(self.scale_select_menu, text="You have selected a right side, please select a left side")
            self.scale_warning.grid(row = 7, column = 1)
        
    def scale_compute(self): ##Measures the pixel length of the scale bar and divides it by the real length 
        if int(self.scale_entry.get()) != 0:
            self.scale_ratio = float((self.scale_rightmost - self.scale_leftmost) / int(self.scale_entry.get()))
            Label(self.scale_select_menu, text="Ratio has been saved!", font=font2).grid(row = 9, column = 1)
            self.scale_status.configure(text="The scale ratio has been determined by manual cropping\nContinue to crop the image for thresholds")
            self.scale_status.update()
            self.scale_return_btn = Button(self.scale_select_menu, text="Return to Cropping", bg="tomato", font=font1, command=lambda:[self.scale_select_menu.destroy(), self.scale_menu.destroy(), self.crop_menu.deiconify()])
            self.scale_return_btn.grid(row=10, column = 1)
            self.scale_compute_btn.destroy()
            del self.scale_compute_btn
            del self.scale_warning
            del self.scale_leftmost
            del self.scale_rightmost


 #Threshold settings    
    def threshold_image(self): ##Creates a menu to adjust the binary thresholds of the image
        if "thresh_menu" in dir(self):
            self.thresh_menu.destroy()
            del self.thresh_close_btn
            del self.thresh_add_btn
        if "thresh_panel_new" in dir(self):
            del self.thresh_panel_new
        if "thresh_panel_old" in dir(self):
            del self.thresh_panel_old

        self.contour_iterations = []
        self.thresh_menu = Toplevel()
        self.thresh_menu.title("Threshold Menu")
        self.thresh_menu.configure(bg="gray69") 
        Label(self.thresh_menu, text="Adjust the parameters until the desired section of the image is white\nThe following is a slice of the original image", font= font1).grid(row = 0, columnspan = 3)
        self.crop = self.orig_img.copy()
        self.crop = self.crop[self.upper_crop_val:self.lower_crop_val, 0:self.img_width]
        adj_crop_img = self.crop[0:self.crop.shape[0],0:self.thresh_width] #Takes a slice of the cropped image to use as a reference window
        adj_crop_img = resize(adj_crop_img, self.croped_resize)
        adj_crop_img = ImageTk.PhotoImage(Image.fromarray(adj_crop_img))
        adj_crop_image = Label(self.thresh_menu, text="Cropped Original", image = adj_crop_img)
        adj_crop_image.image = adj_crop_img
        adj_crop_image.grid(row=1, column=0)

        Label(self.thresh_menu, text="Please select the lower threshold value", font= font2).grid(row = 3, column = 0, sticky = "E") #Entry to adjust lower threshold
        self.low_slide = Scale(self.thresh_menu, from_=0, to=255, orient=HORIZONTAL, length=400, command= self.thresh_update)
        self.low_slide.set(60)
        self.low_slide.grid(row=3,column = 1, columnspan=2, sticky="W", pady=5)

        Label(self.thresh_menu, text = "Please select the higher threshold value", font= font2).grid(row=5, column = 0, sticky = "E") #Entry to adjust upper threshold
        self.up_slide = Scale(self.thresh_menu, from_=0, to=255, orient = HORIZONTAL, length=400, command= self.thresh_update)
        self.up_slide.set(195)
        self.up_slide.grid(row=5,column = 1, columnspan=2, sticky="W", pady=5)

        thresh_compare_btn = Button(self.thresh_menu, text="Set Comparison Image", bg="OliveDrab1", font= font2, command= self.thresh_compare)
        thresh_compare_btn.grid(row=7,column=1, sticky="W")
        
        if self.in_or_ex == 0:
            internal_threshold_btn = Button(self.thresh_menu, text="Set As Internal Threshold", bg="green", font=font2, command= lambda: self.set_internal_threshold(int(self.low_slide.get()),int(self.up_slide.get())))
            internal_threshold_btn.grid(row = 7, column =2, sticky="W")
            if "internal_threshold" not in dir(self):
                self.internal_threshold_label = Label(self.thresh_menu, text="Please select internal threshold",font= font2)
                self.internal_threshold_label.grid(row=8, column =2, sticky="W")
            else:
                self.internal_threshold_label = Label(self.thresh_menu, text=("The current settings are "+str(self.internal_threshold[0]) +","+str(self.internal_threshold[1])),font= font2)
                self.internal_threshold_label.grid(row=8,column=2, sticky="W")

        grayscale_img = ImageTk.PhotoImage(Image.open("Grayscale.jpg"))
        grayscale_image = Label(self.thresh_menu, text="Grayscale Values", image=grayscale_img)
        grayscale_image.image = grayscale_img
        grayscale_image.grid(row = 10, columnspan = 3)

    def thresh_update(self, x): ##Updates the thresholded image based on the positions of the slider bars
        lower_thresh_val = self.low_slide.get()
        upper_thresh_val = self.up_slide.get()
        
        thresh_img = cv2.inRange(self.crop, lower_thresh_val, upper_thresh_val)
        thresh_img_crop = thresh_img[0:thresh_img.shape[0], 0:self.thresh_width]
        thresh_img_crop = resize(thresh_img_crop,self.croped_resize)
        thresh_img_crop = ImageTk.PhotoImage(Image.fromarray(thresh_img_crop))

        if "thresh_panel_new" not in dir(self): #Adds or updates an image to the threshold menu 
            self.thresh_panel_new = Label(self.thresh_menu, text="New Threshold", image = thresh_img_crop)
            self.thresh_panel_new.image = thresh_img_crop
            self.thresh_panel_new.grid(row=1, column = 1)
            Label(self.thresh_menu, text="Most recent image\n("+str(lower_thresh_val)+"-"+str(upper_thresh_val)+")", font= font2).grid(row=2,column=1)
        else:
            self.thresh_panel_new.configure(image=thresh_img_crop)
            self.thresh_panel_new.image=thresh_img_crop
            Label(self.thresh_menu, text="Most recent image\n("+str(lower_thresh_val)+"-"+str(upper_thresh_val)+")", font= font2).grid(row=2,column=1)
        
        self.lower_thresh_old = lower_thresh_val
        self.upper_thresh_old = upper_thresh_val

        if "thresh_close_btn" not in dir(self): #Creates a close button
            self.thresh_close_btn = Button(self.thresh_menu, text="Close and Continue", bg="tomato", font= font2, command=self.thresh_menu.destroy)
            self.thresh_close_btn.grid(row=9, column=1, sticky="W")

            self.thresh_add_btn = Button(self.thresh_menu, text="Add Most Recent Threshold", font= font2, command = self.thresh_add)
            self.thresh_add_btn.grid(row=8, column = 1, sticky="W")


        if "edge_btn" not in dir(self): #Creates a button for the next menu
            self.edge_btn = Button(self.root, text="Select Edges", font = font1, bg="MediumOrchid2", command=self.edge_select)
            self.edge_btn.grid(row = 3, column = 0)
    
    def thresh_compare(self): ##Allows the user to display a third image on the threshold menu to compare between two threshold profiles
        thresh_img = cv2.inRange(self.crop, self.lower_thresh_old, self.upper_thresh_old)
        thresh_img_crop = thresh_img[0:thresh_img.shape[0], 0:self.thresh_width]
        thresh_img_crop = resize(thresh_img_crop,self.croped_resize)
        thresh_img_crop = ImageTk.PhotoImage(Image.fromarray(thresh_img_crop))
        
        if "thresh_panel_old" not in dir(self):
            self.thresh_panel_old = Label(self.thresh_menu, text="New Threshold", image = thresh_img_crop)
            self.thresh_panel_old.image = thresh_img_crop
            self.thresh_panel_old.grid(row=1, column = 2)
            Label(self.thresh_menu, text="Comparison Threshold\n("+str(self.lower_thresh_old)+"-"+str(self.upper_thresh_old)+")",font= font2).grid(row=2,column=2)
        else:
            self.thresh_panel_old.configure(image=thresh_img_crop)
            self.thresh_panel_old.image=thresh_img_crop
            Label(self.thresh_menu, text="Comparison Threshold\n("+str(self.lower_thresh_old)+"-"+str(self.upper_thresh_old)+")",font= font2).grid(row=2,column=2)

    def thresh_add(self): ##Adds the most recent threshold profile to a list to be used later for edge detection
        contour_set = [self.lower_thresh_old, self.upper_thresh_old]
        if contour_set not in self.contour_iterations:
            self.contour_iterations.append(contour_set)
        if "thresh_status" not in dir(self):
            self.thresh_status = Label(self.root, text="You have selected "+str(len(self.contour_iterations))+" different threshold", font= font2)
            self.thresh_status.grid(row=2, column = 1, sticky="W")
        else:
            self.thresh_status.configure(text="You have selected "+str(len(self.contour_iterations))+" different thresholds", font= font2)
            self.thresh_status.update()

    def set_internal_threshold(self, lower_thresh,upper_thresh): ##Extra threshold profile for use with internal oxidation in case the material interface needs a different profile to have high contrast
            self.internal_threshold = (lower_thresh, upper_thresh)
            self.internal_threshold_label.configure(text=("The current settings are "+str(self.internal_threshold[0]) +","+str(self.internal_threshold[1])))
            self.internal_threshold_label.update()
        
  #Contour selection    
    def edge_select(self): ##Creates a menu to select threshold profiles for contour selection
        if "edge menu" in dir(self):
            self.edge_menu.destroy()
        if "lower_list_0" in dir(self):
            del self.lower_list_0
        
        self.tracing_img_main = cv2.cvtColor(self.crop, cv2.COLOR_GRAY2BGR)
        self.tracing_img_main = cv2.copyMakeBorder(self.tracing_img_main, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        self.tracing_img_main = cv2.copyMakeBorder(self.tracing_img_main, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        self.tracing_img_main_backup = self.tracing_img_main

        self.edge_menu = Toplevel()
        self.edge_menu.title("Edge Selection")
        self.edge_menu.configure(bg="gray69")
        self.edge_menu.minsize(300,300)
        Label(self.edge_menu, text="Click on a threshold profile you have saved to mark the boundaries of the feature\n If you are working with a multilayered system you can rename the layers using the entry",font= font1).grid(row = 0, columnspan = 3)

        thresh_preview = self.crop.copy()
        thresh_preview = thresh_preview[0:thresh_preview.shape[0], 0:self.thresh_width]
        
        resize_trace_img = resize(self.tracing_img_main, self.contour_resize) #Creates a trace image that shows the data selected so far
        resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))
        self.edge_menu_trace_image = Label(self.edge_menu, text="Tracing Image", image = resize_trace_img)
        self.edge_menu_trace_image.image = resize_trace_img
        self.edge_menu_trace_image.grid(row=5, columnspan=3, pady=10)

        if len(self.contour_iterations) > 0: #Creates up to three buttons based off the list of thresholds
            thresh_preview_1 = cv2.inRange(thresh_preview, self.contour_iterations[0][0], self.contour_iterations[0][1])
            thresh_preview_1 = resize(thresh_preview_1,self.croped_resize)
            thresh_preview_1 = ImageTk.PhotoImage(Image.fromarray(thresh_preview_1))
            btn_1 = Button(self.edge_menu, image = thresh_preview_1, command = lambda: self.add_contours(0, self.contour_iterations[0][0], self.contour_iterations[0][1], 0) )
            btn_1.image = thresh_preview_1
            btn_1.grid(row=3, column = 0, padx=5)
            self.csvlx_0 = self.csvly_0 = self.csvux_0 = self.csvuy_0 = np.array([], dtype="int64")
            Label(self.edge_menu, text=(str(self.contour_iterations[0][0])+"-"+str(self.contour_iterations[0][1]))).grid(row=4, column = 0)

        
        if len(self.contour_iterations) > 1:
            thresh_preview_2 = cv2.inRange(thresh_preview, self.contour_iterations[1][0], self.contour_iterations[1][1])
            thresh_preview_2 = resize(thresh_preview_2,self.croped_resize)
            thresh_preview_2 = ImageTk.PhotoImage(Image.fromarray(thresh_preview_2))
            btn_2 = Button(self.edge_menu, image = thresh_preview_2, command = lambda: self.add_contours(1, self.contour_iterations[1][0], self.contour_iterations[1][1], 1) )
            btn_2.image = thresh_preview_2
            btn_2.grid(row=3, column = 1, padx=5)
            self.csvlx_1 = self.csvly_1 = self.csvux_1 = self.csvuy_1 = np.array([], dtype="int64")
            Label(self.edge_menu, text=(str(self.contour_iterations[1][0])+"-"+str(self.contour_iterations[1][1]))).grid(row=4, column = 1)

            self.profile_check = IntVar()
            crack_buffer = Checkbutton(self.edge_menu, text="Check to make profiles unique", font=font2, variable=self.profile_check, onvalue=1, offvalue = 0)
            crack_buffer.grid(row=2, column = 0, sticky="E")
        
        if len(self.contour_iterations) >2:
            thresh_preview_3 = cv2.inRange(thresh_preview, self.contour_iterations[2][0], self.contour_iterations[2][1])
            thresh_preview_3 = resize(thresh_preview_3,self.croped_resize)
            thresh_preview_3 = ImageTk.PhotoImage(Image.fromarray(thresh_preview_3))
            btn_3 = Button(self.edge_menu, image = thresh_preview_3, command = lambda: self.add_contours(2, self.contour_iterations[2][0], self.contour_iterations[2][1], 2) )
            btn_3.image = thresh_preview_3
            btn_3.grid(row=3, column = 2, padx=5)
            self.csvlx_2 = self.csvly_2 = self.csvux_2 = self.csvuy_2 = np.array([], dtype="int64")
            Label(self.edge_menu, text=(str(self.contour_iterations[2][0])+"-"+str(self.contour_iterations[2][1]))).grid(row=4, column = 2)

        if len(self.contour_iterations) == 0: #Creates at least one button using the last settings if the list is empty
            thresh_preview_0 = cv2.inRange(thresh_preview, self.lower_thresh_old, self.upper_thresh_old)
            thresh_preview_0 = resize(thresh_preview_0,self.croped_resize)
            thresh_preview_0 = ImageTk.PhotoImage(Image.fromarray(thresh_preview_0))
            btn_0 = Button(self.edge_menu, image = thresh_preview_0, command = lambda: self.add_contours(0, self.lower_thresh_old, self.upper_thresh_old, 0) )
            btn_0.image = thresh_preview_0
            btn_0.grid(row=3, column = 1)
            self.csvlx_0 = self.csvly_0 = self.csvux_0 = self.csvuy_0 = np.array([], dtype="int64")
            Label(self.edge_menu, text=(str(self.contour_iterations[0][0])+"-"+str(self.contour_iterations[0][1]))).grid(row=4, column = 0)

        
        if "internal_threshold" not in dir(self):
            self.internal_threshold = (self.lower_thresh_old, self.upper_thresh_old)

        self.trace_drop_list = []
        for i in range(len(self.contour_iterations)):
            self.trace_drop_list.append("Layer" + str(i+1))
        
        if len(self.trace_drop_list) == 0:
            self.trace_drop_list = ["Layer1"]
            self.contour_list = StringVar()
            self.contour_list.set(self.trace_drop_list[0])
        else:
            self.save_name_entry = Entry(self.edge_menu, font=font2)
            self.save_name_entry.grid(row=1, column = 1, sticky="E")
            self.save_name_entry.insert(END, "Layer Name")
            self.save_name_btn = Button(self.edge_menu, text="Update Layer Name", bg="medium aquamarine", font= font2, command=self.update_csv_names)
            self.save_name_btn.grid(row=1, column=2, sticky="W", pady=10)

            self.contour_list = StringVar()
            self.contour_list.set(self.trace_drop_list[0])
            self.contour_list_drop = OptionMenu(self.edge_menu, self.contour_list, *self.trace_drop_list)
            self.contour_list_drop.config(bg="light sea green", font=font2)
            self.contour_list_drop.grid(row=1, column = 0, sticky="E")
            self.contour_drop_list = self.edge_menu.nametowidget(self.contour_list_drop.menuname)
            self.contour_drop_list.config(font=font2)


        self.edge_close_btn = Button(self.edge_menu, text="Close", bg="tomato", font= font2, command=self.edge_menu.destroy)
        self.edge_close_btn.grid(row=6, column = 1)
    
    def update_csv_names(self):
        entry = self.contour_list.get()
        index = self.trace_drop_list.index(entry)
        self.trace_drop_list[index] = str(self.save_name_entry.get())
        
        self.contour_list_drop.destroy()
        self.contour_list_drop = OptionMenu(self.edge_menu, self.contour_list, *self.trace_drop_list)
        self.contour_list_drop.config(bg="light sea green", font=font2)
        self.contour_list_drop.grid(row=1, column = 0, sticky="E")
        self.contour_drop_list = self.edge_menu.nametowidget(self.contour_list_drop.menuname)
        self.contour_drop_list.config(font=font2)
        self.contour_list.set(self.trace_drop_list[index])

    def add_contours(self, iteration, lower_thresh, upper_thresh, list_number): ##Creates a menu to select contours from selected threshold profile
        if "contour_menu" in dir(self):
            self.contour_menu.destroy()
        if "undo_btn" in dir(self):
            del self.undo_btn

        if lower_thresh == self.internal_threshold[0] and upper_thresh == self.internal_threshold[1]:
            self.internal_check = 1
            self.internal_list = np.array([])
        else:
            self.internal_check = 0
        self.contour_menu = Toplevel()
        self.contour_menu.title("Contour Selection")
        self.contour_menu.configure(bg="gray69")
        
        if "lower_list_0" not in dir(self):
            self.lower_list_0 = self.lower_list_1 = self.lower_list_2 = np.array([])
            self.upper_list_0 = self.upper_list_1 = self.upper_list_2 = np.array([])

        Label(self.contour_menu, text="Click the numbers of the contours you would like to add and the position they are for\n Yellow represents a lower boundary while magenta represents an upper boundary", font= font1).grid(row = 0, columnspan = 5)

        

        thresh_img = cv2.inRange(self.crop, lower_thresh, upper_thresh) #Creates the thresholded image, finds the contours, labels, and adds it to the contour menu
        threshed_image = cv2.cvtColor(thresh_img, cv2.COLOR_GRAY2BGR)
        threshed_image = cv2.copyMakeBorder(threshed_image, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        threshed_image = cv2.medianBlur(threshed_image, 5)
        threshed_image = cv2.copyMakeBorder(threshed_image, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        thresh_img, contours = self.label_center(thresh_img)
        self.click_contours = contours

        thresh_img = resize(thresh_img,self.contour_resize)
        thresh_height, thresh_width = thresh_img.shape[0], thresh_img.shape[1]
        self.thresh_img = ImageTk.PhotoImage(Image.fromarray(thresh_img))

        self.thresh_canvas = Canvas(self.contour_menu, width = thresh_width, height = thresh_height)
        self.thresh_canvas.grid(row=1, columnspan=6)
        self.thresh_canvas_image = self.thresh_canvas.create_image(0,0, image = self.thresh_img, anchor = NW)
        
        if "profile_check" not in dir(self) or self.profile_check.get() != 1:
            resize_trace_img = resize(self.tracing_img_main, self.contour_resize) #Creates a trace image that shows the data selected so far  
            if list_number == 0:
                self.upper_list = self.upper_list_0
                self.lower_list = self.lower_list_0
            elif list_number == 1:
                self.upper_list = self.upper_list_1
                self.lower_list = self.lower_list_1
            else:
                self.upper_list = self.upper_list_2
                self.lower_list = self.lower_list_2
            self.tracing_img_0 = self.tracing_img_main
            self.tracing_img_1 = self.tracing_img_main
            self.tracing_img_2 = self.tracing_img_main

        else:
            if self.contour_list.get() == self.trace_drop_list[0]:
                self.tracing_img_0 = cv2.cvtColor(self.crop, cv2.COLOR_GRAY2BGR)
                self.tracing_img_0 = cv2.copyMakeBorder(self.tracing_img_0, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
                self.tracing_img_0 = cv2.copyMakeBorder(self.tracing_img_0, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
                resize_trace_img = resize(self.tracing_img_0, self.contour_resize)
                self.upper_list = self.upper_list_0
                self.lower_list = self.lower_list_0
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.tracing_img_1 = cv2.cvtColor(self.crop, cv2.COLOR_GRAY2BGR)
                self.tracing_img_1 = cv2.copyMakeBorder(self.tracing_img_1, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
                self.tracing_img_1 = cv2.copyMakeBorder(self.tracing_img_1, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
                resize_trace_img = resize(self.tracing_img_1, self.contour_resize)
                self.upper_list = self.upper_list_1
                self.lower_list = self.lower_list_1
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.tracing_img_2 = cv2.cvtColor(self.crop, cv2.COLOR_GRAY2BGR)
                self.tracing_img_2 = cv2.copyMakeBorder(self.tracing_img_2, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
                self.tracing_img_2 = cv2.copyMakeBorder(self.tracing_img_2, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
                resize_trace_img = resize(self.tracing_img_2, self.contour_resize)
                self.upper_list = self.upper_list_2
                self.lower_list = self.lower_list_2

        
        self.list_label = Label(self.contour_menu, text="Upper list: "+str(self.upper_list)+" and Lower list: " +str(self.lower_list), font= font2) #Displays the values in the upper list and lower list 
        self.list_label.grid(row = 3, column=2, sticky="W")
        
        resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img)) 
        self.tracing_image = Label(self.contour_menu, text="Tracing Image", image = resize_trace_img)
        self.tracing_image.image = resize_trace_img
        self.tracing_image.grid(row=2, columnspan=6)

        Label(self.contour_menu, text="Enter the contour number you would like to use (0-" +str(len(contours)-1)+")\nYou can click with your mouse to add the index of the nearest contour", font= font2).grid(row = 3, column = 0, sticky="E") #Displays the possible contours that can be used

        self.contour_input = Entry(self.contour_menu, font= font2)
        self.contour_input.insert(END, "0")
        self.contour_input.grid(row=3, column =1, sticky = "W")

        self.thresh_canvas.bind("<Button 1>", self.click)

        add_lower_btn = Button(self.contour_menu, text="Add Contour as Lower", bg="yellow", font= font2, command= lambda: self.add_lower(contours, int(self.contour_input.get()), crack_var.get())) #Adds a button to add the lower half of a contour to the lower list
        add_lower_btn.grid(row=4, column = 0, sticky="E", pady=(5,0))

        add_upper_btn = Button(self.contour_menu, text="Add Contour as Upper", bg="magenta2", font= font2, command= lambda: self.add_upper(contours, int(self.contour_input.get()), crack_var.get())) #Adds a button to add the upper half of a contour to the upper list
        add_upper_btn.grid(row=4, column = 1,sticky="W", pady=(5,0))

        add_upper_as_lower_btn = Button(self.contour_menu, text="Add Upper as Lower", bg="goldenrod1", font= font2, command= lambda: self.add_upper_as_lower(contours, int(self.contour_input.get()), crack_var.get())) #Adds the upper half of the contour to the lower list
        add_upper_as_lower_btn.grid(row=5, column = 0, sticky="E")

        add_lower_as_upper_btn = Button(self.contour_menu, text="Add Lower as Upper", bg="magenta4", font= font2, command= lambda: self.add_lower_as_upper(contours, int(self.contour_input.get()), crack_var.get())) #Adds the bottom half of the contour to the upper list
        add_lower_as_upper_btn.grid(row=5, column = 1, sticky="W")
        
        add_bulk_lower_btn = Button(self.contour_menu, text="Add Bulk Lower", bg="gold", font= font2, command=lambda: self.add_bulk(contours,self.upper_list, threshed_image)) #Adds all of the lower half of the contours below the upper data
        add_bulk_lower_btn.grid(row=6, column = 0, sticky="E")

        add_bulk_btn = Button(self.contour_menu, text="Add Bulk Lower to Upper", bg="magenta3", font= font2, command=lambda: self.add_bulk_low_as_up(contours,lower_list)) #Adds a button to add lower half of contours of unselected contours above the lower data to the upper list
        add_bulk_btn.grid(row=6, column = 1, sticky="W")
        Label(self.contour_menu, text="Bulks add traces for data above/below lists used", font= font2).grid(row=6, column =2, sticky="W")

        crack_var = IntVar()
        crack_buffer = Checkbutton(self.contour_menu, text="Crack Buffer Toggle", font=font2, variable=crack_var, onvalue=1, offvalue = 0)
        crack_buffer.grid(row=4, column = 2, sticky="W", pady=(5,0))

        reset_lower_btn = Button(self.contour_menu, text="Reset Lower Boundaries", bg="goldenrod4", font=font2, command = lambda: self.reset_contours(1, contours))
        reset_lower_btn.grid(row=7, column=0, sticky="E")

        reset_upper_btn = Button(self.contour_menu, text="Reset Upper Boundaries", bg="orchid4", font=font2, command = lambda: self.reset_contours(0, contours))
        reset_upper_btn.grid(row=7, column =1, sticky="W")
        if "contour_close_btn" in dir(self):
            self.contour_close_btn = Button(self.contour_menu, text="Close and Continue", bg="tomato", font= font2, command=self.contour_menu.destroy)
            self.contour_close_btn.grid(row=8, column=1 , sticky="W")

    def click(self, event): ##Uses the position of your mouse in the Tkinter canvas to figure out what contours on the thresholded image you are wanting to use
        mouse_x, mouse_y = event.x, event.y
        mouse_x = mouse_x * (100/self.contour_resize)
        mouse_y = mouse_y * (100/self.contour_resize)
        m_array = [(mouse_x, mouse_y)]

        near_contours = [(x,y) for x, y in self.click_tuple if (x in range(int(mouse_x - (self.image_ratio*20)), int(mouse_x + (self.image_ratio*20)))  and y in range(int(mouse_y - (self.image_ratio*20)), int(mouse_y + (self.image_ratio*20))))]
        if len(near_contours) > 0:
            near_index = closest_node(m_array, near_contours)
            close_point = near_contours[near_index]
            contour_index = self.click_tuple.index(close_point)
            contour_number = self.click_index[contour_index]
            self.contour_input.delete(0,"end")
            self.contour_input.insert(END, contour_number)

    def add_upper(self, contours, contour_number, crackbuffer): ##Adds the upper half of a contour to the upper list
        if contour_number not in self.upper_list:
            n_contour = contours[contour_number] #Isolate the desired contour
            brx = None
            bry = None
            blx = None
            bly = None
            coordx = np.array([])#Temporary array for x coordinates
            coordy = np.array([]) #Temporary array for y coordinates
            for d in range(len(n_contour)): #Iterates through the selected contour making the list and looking for the rectangular corners
                totalLength = int(len(n_contour))
                XY_Coordinates = n_contour[d]
                currentx = int(XY_Coordinates[0][0])
                currenty = int(XY_Coordinates[0][1])
                coordy = np.append(coordy, currenty)
                coordx = np.append(coordx, currentx)
            
                if brx is None: #Give default value
                    brx = currentx
                    bry = currenty
                    bottomright  = int(d)
                if currentx > brx: #If the x value is more right than the previous update the rightmost point
                    brx = currentx
                    bry = currenty
                    bottomright  = int(d)
                elif currentx == brx: #If there are multiple rightmost points take the lowest
                    if currenty < bry:
                        bry = currenty
                        bottomright  = int(d)

                if blx is None: #Give default value for bottomleft
                    blx = currentx
                    bly = currenty
                    bottomleft  = int(d)
                if currentx < blx: #Check if new value is more left than previous
                    blx = currentx
                    bly = currenty
                    bottomleft  = int(d)
                elif currentx == blx: #Take the lowest y of equivalent leftmost
                    if currenty < bly:
                        bly = currenty
                        bottomleft  = int(d)

            if (bottomleft - bottomright) > 0: #Finds the slice distance if the corners are continuous 
                sliceLength = bottomleft - bottomright
            else: #Finds the slice distance if the corners are not continuous
                sliceLength = totalLength - (bottomright - bottomleft)

            cx = coordx[bottomright:] #Starts the list with the bottom right
            cx2 = coordx[:bottomright] #Puts everything back in place
            cx = np.append(cx, cx2) # Combines the two small graphs
            cy = coordy[bottomright:]
            cy2 = coordy[:bottomright]
            cy = np.append(cy, cy2)
            if crackbuffer ==1: #Compares average values to remove potential crack values at the ends of the data
                height_check = np.mean(cy)
                for i in range(len(cy)):
                    if cy[i] <= height_check:
                        end_a = i
                        break
                
                for i in range((len(cy)-1),0,-1):
                    if cy[i] <= height_check:
                        end_b = i
                        break
                cx_2 = cx[end_a:end_b]
                cy_2 = cy[end_a:end_b]
                cx = cx_2[(self.contour_buffer*self.crackbuffer):(sliceLength-(self.contour_buffer*self.crackbuffer))]
                cy = cy_2[(self.contour_buffer*self.crackbuffer):(sliceLength-(self.contour_buffer*self.crackbuffer))]
            
            else:
                cx = cx[self.contour_buffer:(sliceLength-self.contour_buffer)]
                cy = cy[self.contour_buffer:(sliceLength-(self.contour_buffer))]
            cx = cx[::-1] #Converts lower data from L-R to R-L
            cy = cy[::-1] #Converts lower data from L-R to R-L


            if self.contour_list.get() == self.trace_drop_list[0]:
                self.csvux_0 = np.append(self.csvux_0, cx)
                self.csvuy_0 = np.append(self.csvuy_0, cy)
                self.upper_list_0 = np.append(self.upper_list_0, contour_number)
                self.update_image_up(self.tracing_img_0, self.csvux_0, self.csvuy_0, contours, contour_number, len(cx))
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.csvux_1 = np.append(self.csvux_1, cx)
                self.csvuy_1 = np.append(self.csvuy_1, cy)
                self.upper_list_1 = np.append(self.upper_list_1, contour_number)
                self.update_image_up(self.tracing_img_1, self.csvux_1, self.csvuy_1, contours, contour_number, len(cx))
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.csvux_2 = np.append(self.csvux_2, cx)
                self.csvuy_2 = np.append(self.csvuy_2, cy)
                self.upper_list_2 = np.append(self.upper_list_2, contour_number)
                self.update_image_up(self.tracing_img_2, self.csvux_2, self.csvuy_2, contours, contour_number, len(cx))
            self.upper_list = np.append(self.upper_list, contour_number)

            if "undo_btn" in dir(self):
                self.undo_btn.grid_remove()
                del self.undo_btn
            self.undo_btn = Button(self.contour_menu, text="Undo", bg="alice blue", font= font2, command= lambda: self.undo(0, len(cx), contours))
            self.undo_btn.grid(row=8, column = 0, sticky="E")
            self.list_label.configure(text="Upper list: "+str(self.upper_list)+" and Lower list: " +str(self.lower_list), font= font2)
            self.list_label.update()
        if "save_csv_btn" not in dir(self):
            self.save_csv_btn = Button(self.root, text="Save CSVs", font = font1, bg="lawn green",command=self.save_csv)
            self.save_csv_btn.grid(row=4, column=0)
        self.edge_close_btn.config(text="Close and Continue")
        if "contour_close_btn" not in dir(self):
            self.contour_close_btn = Button(self.contour_menu, text="Close and Continue", bg="tomato", font= font2, command=self.contour_menu.destroy)
            self.contour_close_btn.grid(row=8, column=1 , sticky="W")
    
    def add_lower(self, contours, contour_number, crackbuffer): ##Adds the lower half of a contour to the lower list
        if contour_number not in self.lower_list:
            n_contour = contours[contour_number]
            bigx = None
            bigy = None
            tprx = None
            tpry = None
            coordx = np.array([])
            coordy = np.array([])
            for d in range(len(n_contour)):
                totalLength = int(len(n_contour))
                XY_Coordinates = n_contour[d]
                currentx = int(XY_Coordinates[0][0])
                currenty = int(XY_Coordinates[0][1])
                coordy = np.append(coordy, currenty)
                coordx = np.append(coordx, currentx)

                if bigx is None:
                    bigx = currentx
                    bigy = currenty
                    topleft  = int(d)
                if currentx < bigx:
                    bigx = currentx
                    bigy = currenty
                    topleft  = int(d)
                elif currentx == bigx:
                    if currenty > bigy:
                        bigy = currenty
                        topleft  = int(d)

                if tprx is None:
                    tprx = currentx
                    tpry = currenty
                    topright  = int(d)
                if currentx > tprx:
                    tprx = currentx
                    tpry = currenty
                    topright  = int(d)
                elif currentx == bigx:
                    if currenty > bigy:
                        bigy = currenty
                        topright  = int(d)
        
            if (topright - topleft) < 0:
                sliceLength = totalLength - (topleft - topright)
            else:
                sliceLength = topright - topleft
        
            cx = coordx[topleft:]
            cx2 = coordx[:topleft]
            cx = np.append(cx, cx2)
            cy = coordy[topleft:]
            cy2 = coordy[:topleft]
            cy = np.append(cy, cy2)
            
            if crackbuffer ==1: #Compares average values to remove potential crack values at the ends of the data
                height_check = np.mean(cy)
                for i in range(len(cy)):
                    if cy[i] >= height_check:
                        end_a = i
                        break
                
                for i in range((len(cy)-1),0,-1):
                    if cy[i] >= height_check:
                        end_b = i
                        break
                cx_2 = cx[end_a:end_b]
                cy_2 = cy[end_a:end_b]
                cx = cx_2[(self.contour_buffer*self.crackbuffer*3):(sliceLength-(self.contour_buffer*self.crackbuffer*3))]
                cy = cy_2[(self.contour_buffer*self.crackbuffer*3):(sliceLength-(self.contour_buffer*self.crackbuffer*3))]
            
            else:
                cx = cx[self.contour_buffer:(sliceLength-self.contour_buffer)]
                cy = cy[self.contour_buffer:(sliceLength-(self.contour_buffer))]

            if self.contour_list.get() == self.trace_drop_list[0]:
                self.csvlx_0 = np.append(self.csvlx_0, cx)
                self.csvly_0 = np.append(self.csvly_0, cy)
                self.lower_list_0 = np.append(self.lower_list_0, contour_number)
                self.update_image_low(self.tracing_img_0, self.csvlx_0, self.csvly_0, contours, contour_number, len(cx))
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.csvlx_1 = np.append(self.csvlx_1, cx)
                self.csvly_1 = np.append(self.csvly_1, cy)
                self.lower_list_1 = np.append(self.lower_list_1, contour_number)
                self.update_image_low(self.tracing_img_1, self.csvlx_1, self.csvly_1, contours, contour_number, len(cx))
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.csvlx_2 = np.append(self.csvlx_2, cx)
                self.csvly_2 = np.append(self.csvly_2, cy)
                self.lower_list_2 = np.append(self.lower_list_2, contour_number)
                self.update_image_low(self.tracing_img_2, self.csvlx_2, self.csvly_2, contours, contour_number, len(cx))
            self.lower_list = np.append(self.lower_list, contour_number)
           
            if self.internal_check == 1:
                self.internal_list = np.append(self.internal_list, contour_number) 
            if "undo_btn" in dir(self):
                self.undo_btn.grid_remove()
                del self.undo_btn
            self.undo_btn = Button(self.contour_menu, text="Undo", bg="alice blue", font= font2, command= lambda: self.undo(1, len(cx), contours))
            self.undo_btn.grid(row=8, column = 0, sticky="E")
            self.list_label.configure(text="Upper list: "+str(self.upper_list)+" and Lower list: " +str(self.lower_list), font= font2)
            self.list_label.update()
        if "save_csv_btn" not in dir(self):
            self.save_csv_btn = Button(self.root, text="Save CSVs", font = font1, bg="lawn green",command=self.save_csv)
            self.save_csv_btn.grid(row=4, column=0)
        self.edge_close_btn.config(text="Close and Continue")
        if "contour_close_btn" not in dir(self):
            self.contour_close_btn = Button(self.contour_menu, text="Close and Continue", bg="tomato", font= font2, command=self.contour_menu.destroy)
            self.contour_close_btn.grid(row=8, column=1 , sticky="W")

    def add_bulk_low_as_up(self, contours, lower_list): ##Adds the lower half of contours of unselected contours above the lower data to upper data
        if self.contour_list.get() == self.trace_drop_list[0]:
            minval = np.amax(self.csvly_0)
        elif self.contour_list.get() == self.trace_drop_list[1]:
            minval = np.amax(self.csvly_1)
        elif self.contour_list.get() == self.trace_drop_list[2]:
            minval = np.amax(self.csvly_2)
    
        for i in range(len(contours)):
            if i not in self.lower_list and minval > contours[i][0][0][1]:
                n_contour = contours[i] #Isolate the desired contour
                brx = None
                bry = None
                blx = None
                bly = None
                coordx = np.array([])#Temporary array for x coordinates
                coordy = np.array([]) #Temporary array for y coordinates
                for d in range(len(n_contour)): #Iterates through the selected contour making the list and looking for the rectangular corners
                    totalLength = int(len(n_contour))
                    XY_Coordinates = n_contour[d]
                    currentx = int(XY_Coordinates[0][0])
                    currenty = int(XY_Coordinates[0][1])
                    coordy = np.append(coordy, currenty)
                    coordx = np.append(coordx, currentx)
            
                    if brx is None: #Give default value
                        brx = currentx
                        bry = currenty
                        bottomright  = int(d)
                    if currentx > brx: #If the x value is more right than the previous update the rightmost point
                        brx = currentx
                        bry = currenty
                        bottomright  = int(d)
                    elif currentx == brx: #If there are multiple rightmost points take the lowest
                        if currenty < bry:
                            bry = currenty
                            bottomright  = int(d)

                    if blx is None: #Give default value for bottomleft
                        blx = currentx
                        bly = currenty
                        bottomleft  = int(d)
                    if currentx < blx: #Check if new value is more left than previous
                        blx = currentx
                        bly = currenty
                        bottomleft  = int(d)
                    elif currentx == blx: #Take the lowest y of equivalent leftmost
                        if currenty < bly:
                            bly = currenty
                            bottomleft  = int(d)

                if (bottomleft - bottomright) > 0: #Finds the slice distance if the corners are continuous 
                    sliceLength = bottomleft - bottomright
                else: #Finds the slice distance if the corners are not continuous
                    sliceLength = totalLength - (bottomright - bottomleft)

                cx = coordx[bottomright:] #Starts the list with the bottom right
                cx2 = coordx[:bottomright] #Puts everything back in place
                cx = np.append(cx, cx2) # Combines the two small graphs
                cx = cx[self.contour_buffer:(sliceLength-self.contour_buffer)]
                cx = cx[::-1] #Converts lower data from L-R to R-L

                cy = coordy[bottomright:]
                cy2 = coordy[:bottomright]
                cy = np.append(cy, cy2)
                cy = cy[self.contour_buffer:(sliceLength-self.contour_buffer)] 
                cy = cy[::-1] #Converts lower data from L-R to R-L
                
                if self.contour_list.get() == self.trace_drop_list[0]:
                    self.csvux_0 = np.append(self.csvux_0, cx)
                    self.csvuy_0 = np.append(self.csvuy_0, cy)
                    self.upper_list_0 = np.append(self.upper_list_0, i)
                    self.update_image_up(self.tracing_img_0, self.csvux_0, self.csvuy_0, contours, i, len(cx))
                elif self.contour_list.get() == self.trace_drop_list[1]:
                    self.csvux_1 = np.append(self.csvux_1, cx)
                    self.csvuy_1 = np.append(self.csvuy_1, cy)
                    self.upper_list_1 = np.append(self.upper_list_1, i)
                    self.update_image_up(self.tracing_img_1, self.csvux_1, self.csvuy_1, contours, i, len(cx))
                elif self.contour_list.get() == self.trace_drop_list[2]:
                    self.csvux_2 = np.append(self.csvux_2, cx)
                    self.csvuy_2 = np.append(self.csvuy_2, cy)
                    self.upper_list_2 = np.append(self.upper_list_2, i)
                    self.update_image_up(self.tracing_img_2, self.csvux_2, self.csvuy_2, contours, i, len(cx))
                self.upper_list = np.append(self.upper_list, i)
                
        if "save_csv_btn" not in dir(self):
            self.save_csv_btn = Button(self.root, text="Save CSVs", font = font1, bg="lawn green",command=self.save_csv)
            self.save_csv_btn.grid(row=4, column=0)
        self.edge_close_btn.config(text="Close and Continue")
        if "contour_close_btn" not in dir(self):
            self.contour_close_btn = Button(self.contour_menu, text="Close and Continue", bg="tomato", font= font2, command=self.contour_menu.destroy)
            self.contour_close_btn.grid(row=8, column=1 , sticky="W")

    def add_lower_as_upper(self, contours, contour_number, crackbuffer): ##Adds the bottom half of the contour data to the upper data
        if contour_number not in self.upper_list and contour_number not in self.lower_list:
            n_contour = contours[contour_number]
            bigx = None
            bigy = None
            tprx = None
            tpry = None
            coordx = np.array([])
            coordy = np.array([])
            for d in range(len(n_contour)):
                totalLength = int(len(n_contour))
                XY_Coordinates = n_contour[d]
                currentx = int(XY_Coordinates[0][0])
                currenty = int(XY_Coordinates[0][1])
                coordy = np.append(coordy, currenty)
                coordx = np.append(coordx, currentx)

                if bigx is None:
                    bigx = currentx
                    bigy = currenty
                    topleft  = int(d)
                if currentx < bigx:
                    bigx = currentx
                    bigy = currenty
                    topleft  = int(d)
                elif currentx == bigx:
                    if currenty > bigy:
                        bigy = currenty
                        topleft  = int(d)

                if tprx is None:
                    tprx = currentx
                    tpry = currenty
                    topright  = int(d)
                if currentx > tprx:
                    tprx = currentx
                    tpry = currenty
                    topright  = int(d)
                elif currentx == bigx:
                    if currenty > bigy:
                        bigy = currenty
                        topright  = int(d)
        
            if (topright - topleft) < 0:
                sliceLength = totalLength - (topleft - topright)
            else:
                sliceLength = topright - topleft
        
            cx = coordx[topleft:]
            cx2 = coordx[:topleft]
            cx = np.append(cx, cx2)
            cy = coordy[topleft:]
            cy2 = coordy[:topleft]
            cy = np.append(cy, cy2)
            if crackbuffer ==1: #Compares average values to remove potential crack values at the ends of the data
                height_check = np.mean(cy)
                for i in range(len(cy)):
                    if cy[i] >= height_check:
                        end_a = i
                        break
                
                for i in range((len(cy)-1),0,-1):
                    if cy[i] >= height_check:
                        end_b = i
                        break
                cx = cx[end_a:end_b]
                cy = cy[end_a:end_b]
                cx = cx[(self.contour_buffer*self.crackbuffer):(sliceLength-(self.contour_buffer*self.crackbuffer))]
                cy = cy[(self.contour_buffer*self.crackbuffer):(sliceLength-(self.contour_buffer*self.crackbuffer))]
            
            else:
                cx = cx[self.contour_buffer:(sliceLength-self.contour_buffer)]
                cy = cy[self.contour_buffer:(sliceLength-(self.contour_buffer))]

            if self.contour_list.get() == self.trace_drop_list[0]:
                self.csvux_0 = np.append(self.csvux_0, cx)
                self.csvuy_0 = np.append(self.csvuy_0, cy)
                self.upper_list_0 = np.append(self.upper_list_0, contour_number)
                self.update_image_up(self.tracing_img_0, self.csvux_0, self.csvuy_0, contours, contour_number, len(cx))
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.csvux_1 = np.append(self.csvux_1, cx)
                self.csvuy_1 = np.append(self.csvuy_1, cy)
                self.upper_list_1 = np.append(self.upper_list_1, contour_number)
                self.update_image_up(self.tracing_img_1, self.csvux_1, self.csvuy_1, contours, contour_number, len(cx))
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.csvux_2 = np.append(self.csvux_2, cx)
                self.csvuy_2 = np.append(self.csvuy_2, cy)
                self.upper_list_2 = np.append(self.upper_list_2, contour_number)
                self.update_image_up(self.tracing_img_2, self.csvux_2, self.csvuy_2, contours, contour_number, len(cx))
            self.upper_list = np.append(self.upper_list, contour_number)
           
            if "undo_btn" in dir(self):
                self.undo_btn.grid_remove()
                del self.undo_btn
            self.undo_btn = Button(self.contour_menu, text="Undo", bg="alice blue", font= font2, command= lambda: self.undo(0, len(cx), contours))
            self.undo_btn.grid(row=8, column = 0, sticky="E")
            self.list_label.configure(text="Upper list: "+str(self.upper_list)+" and Lower list: " +str(self.lower_list), font= font2)
            self.list_label.update()
        
        if "save_csv_btn" not in dir(self):
            self.save_csv_btn = Button(self.root, text="Save CSVs", font = font1, bg="lawn green",command=self.save_csv)
            self.save_csv_btn.grid(row=4, column=0)
        self.edge_close_btn.config(text="Close and Continue")
        if "contour_close_btn" not in dir(self):
            self.contour_close_btn = Button(self.contour_menu, text="Close and Continue", bg="tomato", font= font2, command=self.contour_menu.destroy)
            self.contour_close_btn.grid(row=8, column=1 , sticky="W")

    def add_upper_as_lower(self, contours, contour_number, crackbuffer):
        if contour_number not in self.lower_list and contour_number not in self.upper_list :
            n_contour = contours[contour_number] #Isolate the desired contour
            brx = None
            bry = None
            blx = None
            bly = None
            coordx = np.array([])#Temporary array for x coordinates
            coordy = np.array([]) #Temporary array for y coordinates
            for d in range(len(n_contour)): #Iterates through the selected contour making the list and looking for the rectangular corners
                totalLength = int(len(n_contour))
                XY_Coordinates = n_contour[d]
                currentx = int(XY_Coordinates[0][0])
                currenty = int(XY_Coordinates[0][1])
                coordy = np.append(coordy, currenty)
                coordx = np.append(coordx, currentx)
            
                if brx is None: #Give default value
                    brx = currentx
                    bry = currenty
                    bottomright  = int(d)
                if currentx > brx: #If the x value is more right than the previous update the rightmost point
                    brx = currentx
                    bry = currenty
                    bottomright  = int(d)
                elif currentx == brx: #If there are multiple rightmost points take the lowest
                    if currenty < bry:
                        bry = currenty
                        bottomright  = int(d)

                if blx is None: #Give default value for bottomleft
                    blx = currentx
                    bly = currenty
                    bottomleft  = int(d)
                if currentx < blx: #Check if new value is more left than previous
                    blx = currentx
                    bly = currenty
                    bottomleft  = int(d)
                elif currentx == blx: #Take the lowest y of equivalent leftmost
                    if currenty < bly:
                        bly = currenty
                        bottomleft  = int(d)

            if (bottomleft - bottomright) > 0: #Finds the slice distance if the corners are continuous 
                sliceLength = bottomleft - bottomright
            else: #Finds the slice distance if the corners are not continuous
                sliceLength = totalLength - (bottomright - bottomleft)

            cx = coordx[bottomright:] #Starts the list with the bottom right
            cx2 = coordx[:bottomright] #Puts everything back in place
            cx = np.append(cx, cx2) # Combines the two small graphs
            cy = coordy[bottomright:]
            cy2 = coordy[:bottomright]
            cy = np.append(cy, cy2)
            if crackbuffer ==1: #Compares average values to remove potential crack values at the ends of the data
                height_check = np.mean(cy)
                for i in range(len(cy)):
                    if cy[i] <= height_check:
                        end_a = i
                        break
                
                for i in range((len(cy)-1),0,-1):
                    if cy[i] <= height_check:
                        end_b = i
                        break
                cx_2 = cx[end_a:end_b]
                cy_2 = cy[end_a:end_b]
                cx = cx_2[(self.contour_buffer*self.crackbuffer):(sliceLength-(self.contour_buffer*self.crackbuffer))]
                cy = cy_2[(self.contour_buffer*self.crackbuffer):(sliceLength-(self.contour_buffer*self.crackbuffer))]
            
            else:
                cx = cx[self.contour_buffer:(sliceLength-self.contour_buffer)]
                cy = cy[self.contour_buffer:(sliceLength-(self.contour_buffer))]
            cx = cx[::-1] #Converts lower data from L-R to R-L
            cy = cy[::-1] #Converts lower data from L-R to R-L


            if self.contour_list.get() == self.trace_drop_list[0]:
                self.csvlx_0 = np.append(self.csvlx_0, cx)
                self.csvly_0 = np.append(self.csvly_0, cy)
                self.lower_list_0 = np.append(self.lower_list_0, contour_number)
                self.update_image_low(self.tracing_img_0, self.csvlx_0, self.csvly_0, contours, contour_number, len(cx))
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.csvlx_1 = np.append(self.csvlx_1, cx)
                self.csvly_1 = np.append(self.csvly_1, cy)
                self.lower_list_1 = np.append(self.lower_list_1, contour_number)
                self.update_image_low(self.tracing_img_1, self.csvlx_1, self.csvly_1, contours, contour_number, len(cx))
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.csvlx_2 = np.append(self.csvlx_2, cx)
                self.csvly_2 = np.append(self.csvly_2, cy)
                self.lower_list_2 = np.append(self.lower_list_2, contour_number)
                self.update_image_low(self.tracing_img_2, self.csvlx_2, self.csvly_2, contours, contour_number, len(cx))
            self.lower_list = np.append(self.lower_list, contour_number)

            if "undo_btn" in dir(self):
                self.undo_btn.grid_remove()
                del self.undo_btn
            self.undo_btn = Button(self.contour_menu, text="Undo", bg="alice blue", font= font2, command= lambda: self.undo(1, len(cx), contours))
            self.undo_btn.grid(row=8, column = 0, sticky="E")
            self.list_label.configure(text="Upper list: "+str(self.upper_list)+" and Lower list: " +str(self.lower_list), font= font2)
            self.list_label.update()
        if "save_csv_btn" not in dir(self):
            self.save_csv_btn = Button(self.root, text="Save CSVs", font = font1, bg="lawn green",command=self.save_csv)
            self.save_csv_btn.grid(row=4, column=0)
        self.edge_close_btn.config(text="Close and Continue")
        if "contour_close_btn" not in dir(self):
            self.contour_close_btn = Button(self.contour_menu, text="Close and Continue", bg="tomato", font= font2, command=self.contour_menu.destroy)
            self.contour_close_btn.grid(row=8, column=1 , sticky="W")

    def add_bulk(self, contours, upper_list, threshed_image): #Adds all of the lower half of the contours below the upper data  
        if len(self.csvuy_0) > 0:
            minval = np.amin(self.csvuy_0)
            largest_in_list = np.amax(upper_list) 
        elif self.profile_check.get() != 1 and len(self.csvux_1) > 0:
            minval = np.amin(self.csvuy_1)
            largest_in_list = 9999 
        elif self.profile_check.get() != 1 and len(self.csvux_2) > 0:
            minval = np.amin(self.csvuy_2)
            largest_in_list = 9999
        else:
            minval = 0
            largest_in_list = 9999
        counter = 0
        for i in range(len(contours)): #Iterates the contours and does the add lower process
            cx = contours[i][0][0][0]
            cy = contours[i][0][0][1]
            try:
                b, _, _ = (threshed_image[(cy),(cx)])
                c, _, _ = (threshed_image[(cy+2),(cx)])
            except:
                continue
                
            
            #if i not in upper_list and i < largest_in_list and minval < cy and b == 255: #Something is wrong with b
            if (i not in upper_list and i < largest_in_list and minval < cy and (b ==255)):
                counter+=1
                n_contour = contours[i]
                bigx = None
                bigy = None
                tprx = None
                tpry = None
                coordx = np.array([])
                coordy = np.array([])
                for d in range(len(n_contour)):
                    totalLength = int(len(n_contour))
                    XY_Coordinates = n_contour[d]
                    currentx = int(XY_Coordinates[0][0])
                    currenty = int(XY_Coordinates[0][1])
                    coordy = np.append(coordy, currenty)
                    coordx = np.append(coordx, currentx)

                    if bigx is None:
                        bigx = currentx
                        bigy = currenty
                        topleft  = int(d)
                    if currentx < bigx:
                        bigx = currentx
                        bigy = currenty
                        topleft  = int(d)
                    elif currentx == bigx:
                        if currenty > bigy:
                            bigy = currenty
                            topleft  = int(d)

                    if tprx is None:
                        tprx = currentx
                        tpry = currenty
                        topright  = int(d)
                    if currentx > tprx:
                        tprx = currentx
                        tpry = currenty
                        topright  = int(d)
                    elif currentx == bigx:
                        if currenty > bigy:
                            bigy = currenty
                            topright  = int(d)
        
                if (topright - topleft) < 0:
                    sliceLength = totalLength - (topleft - topright)
                else:
                    sliceLength = topright - topleft
        
                cx = coordx[topleft:]
                cx2 = coordx[:topleft]
                cx = np.append(cx, cx2)
                cx = cx[self.contour_buffer:(sliceLength-self.contour_buffer)]
                cy = coordy[topleft:]
                cy2 = coordy[:topleft]
                cy = np.append(cy, cy2)
                cy = cy[self.contour_buffer:(sliceLength-self.contour_buffer)]
                
                if self.contour_list.get() == self.trace_drop_list[0]:
                    self.csvlx_0 = np.append(self.csvlx_0, cx)
                    self.csvly_0 = np.append(self.csvly_0, cy)
                    self.lower_list_0 = np.append(self.lower_list_0, i)
                    self.update_image_low(self.tracing_img_0, self.csvlx_0, self.csvly_0, contours, i, len(cx))
                elif self.contour_list.get() == self.trace_drop_list[1]:
                    self.csvlx_1 = np.append(self.csvlx_1, cx)
                    self.csvly_1 = np.append(self.csvly_1, cy)
                    self.lower_list_1 = np.append(self.lower_list_1, i)
                    self.update_image_low(self.tracing_img_1, self.csvlx_1, self.csvly_1, contours, i, len(cx))
                elif self.contour_list.get() == self.trace_drop_list[2]:
                    self.csvlx_2 = np.append(self.csvlx_2, cx)
                    self.csvly_2 = np.append(self.csvly_2, cy)
                    self.lower_list_2 = np.append(self.lower_list_2, i)
                    self.update_image_low(self.tracing_img_2, self.csvlx_2, self.csvly_2, contours, i, len(cx))
                self.lower_list = np.append(self.lower_list, i)
                
                if self.internal_check == 1:
                    if i not in self.internal_list:
                        self.internal_list = np.append(self.internal_list, i)
                self.update_image_low(self.tracing_img_0, self.csvlx_0, self.csvly_0, contours, i, len(cx))
        if "save_csv_btn" not in dir(self):
            self.save_csv_btn = Button(self.root, text="Save CSVs", font = font1, bg="lawn green",command=self.save_csv)
            self.save_csv_btn.grid(row=4, column=0)
        self.edge_close_btn.config(text="Close and Continue")
        if "contour_close_btn" not in dir(self):
            self.contour_close_btn = Button(self.contour_menu, text="Close and Continue", bg="tomato", font= font2, command=self.contour_menu.destroy)
            self.contour_close_btn.grid(row=8, column=1 , sticky="W")

    def undo(self, up_or_low, len_data, contours): ##Undoes the previous non-bulk action
        if up_or_low == 0: #Remove recent data if last entry was to upper list
            if self.contour_list.get() == self.trace_drop_list[0]:
                self.upper_list_0 = self.upper_list_0[:-1]
                self.csvux_0 = self.csvux_0[:-len_data]
                self.csvuy_0 = self.csvuy_0[:-len_data]
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.upper_list_1 = self.upper_list_1[:-1]
                self.csvux_1 = self.csvux_1[:-len_data]
                self.csvuy_1 = self.csvuy_1[:-len_data]
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.upper_list_2 = self.upper_list_2[:-1]
                self.csvux_2 = self.csvux_2[:-len_data]
                self.csvuy_2 = self.csvuy_2[:-len_data]
        else: #Remove recent data if last entry was to lower list
            if self.contour_list.get() == self.trace_drop_list[0]:
                self.lower_list_0 = self.lower_list_0[:-1]
                self.csvlx_0 = self.csvlx_0[:-len_data]
                self.csvly_0 = self.csvly_0[:-len_data]
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.lower_list_1 = self.lower_list_1[:-1]
                self.csvlx_1 = self.csvlx_1[:-len_data]
                self.csvly_1 = self.csvly_1[:-len_data]
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.lower_list_2 = self.lower_list_2[:-1]
                self.csvlx_2 = self.csvlx_2[:-len_data]
                self.csvly_2 = self.csvly_2[:-len_data]
        
        tracing_img_backup = self.tracing_img_main_backup
        if self.contour_list.get() == self.trace_drop_list[0]: #Redo traces to remove last entry from traces
            for i in range(len(self.csvlx_0)):
                cv2.circle(tracing_img_backup, (int(self.csvlx_0[i]), int(self.csvly_0[i])), self.center_circle, (255,255,0), -1)
            for i in range(len(self.csvux_0)):
                cv2.circle(tracing_img_backup, (int(self.csvux_0[i]), int(self.csvuy_0[i])), self.center_circle, (255,0,255), -1)
            for i in self.lower_list_0:
                cx = contours[int(i)][0][0][0]
                cy = contours[int(i)][0][0][1]
                cv2.putText(tracing_img_backup, (str(i)), (cx, cy+(int(self.scale_bar/20))), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (255,255,0),self.center_circle+1)
            for i in self.upper_list_0:
                cx = contours[int(i)][0][0][0]
                cy = contours[int(i)][0][0][1]
                cv2.putText(tracing_img_backup, (str(i)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (255,0,255),self.center_circle+1)
            self.upper_list = self.upper_list_0
            self.lower_list = self.lower_list_0
    
        elif self.contour_list.get() == self.trace_drop_list[1]:
            for i in range(len(self.csvlx_1)):
                cv2.circle(tracing_img_backup, (int(self.csvlx_1[i]), int(self.csvly_1[i])), self.center_circle, (212,212,48), -1)
            for i in range(len(self.csvux_1)):
                cv2.circle(tracing_img_backup, (int(self.csvux_1[i]), int(self.csvuy_1[i])), self.center_circle, (212,48,212), -1)
            for i in self.lower_list_1:
                cx = contours[int(i)][0][0][0]
                cy = contours[int(i)][0][0][1]
                cv2.putText(tracing_img_backup, (str(i)), (cx, cy+(int(self.scale_bar/20))), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (212,212,48),self.center_circle+1)
            for i in self.upper_list_1:
                cx = contours[int(i)][0][0][0]
                cy = contours[int(i)][0][0][1]
                cv2.putText(tracing_img_backup, (str(i)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (212,48,212),self.center_circle+1)          
            self.upper_list = self.upper_list_1
            self.lower_list = self.lower_list_1

        elif self.contour_list.get() == self.trace_drop_list[2]:
            for i in range(len(self.csvlx_2)):
                cv2.circle(tracing_img_backup, (int(self.csvlx_2[i]), int(self.csvly_2[i])), self.center_circle, (178,178,61), -1)
            for i in range(len(self.csvux_2)):
                cv2.circle(tracing_img_backup, (int(self.csvux_2[i]), int(self.csvuy_2[i])), self.center_circle, (178,61,178), -1)
            for i in self.lower_list_2:
                cx = contours[int(i)][0][0][0]
                cy = contours[int(i)][0][0][1]
                cv2.putText(tracing_img_backup, (str(i)), (cx, cy+(int(self.scale_bar/20))), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (178,178,61),self.center_circle+1)
            for i in self.upper_list_2:
                cx = contours[int(i)][0][0][0]
                cy = contours[int(i)][0][0][1]
                cv2.putText(tracing_img_backup, (str(i)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (178,61,178),self.center_circle+1)
            self.upper_list = self.upper_list_2
            self.lower_list = self.lower_list_2
        
        resize_trace_img = resize(tracing_img_backup, self.contour_resize)
        resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))
        self.tracing_image.configure(image=resize_trace_img)
        self.tracing_image.image=resize_trace_img

        self.list_label.configure(text="Upper list: "+str(self.upper_list)+" and Lower list: " +str(self.lower_list), font= font2)
        self.list_label.update()
        self.undo_btn.grid_remove()
        del self.undo_btn
    
    def reset_contours(self, up_or_low, contours):
        self.tracing_img_main_backup = cv2.cvtColor(self.crop, cv2.COLOR_GRAY2BGR)
        self.tracing_img_main_backup = cv2.copyMakeBorder(self.tracing_img_main_backup, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        self.tracing_img_main_backup = cv2.copyMakeBorder(self.tracing_img_main_backup, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        if up_or_low == 0: #Remove recent data if last entry was to upper list
            if self.contour_list.get() == self.trace_drop_list[0]:
                self.upper_list = self.upper_list_0 = np.array([])
                self.csvux_0 = self.csvuy_0 = np.array([], dtype="int64")
                csvlx = self.csvlx_0
                csvly = self.csvly_0
                color = (255,255,0)
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.upper_list = self.upper_list_1 = np.array([])
                self.csvux_1 = self.csvuy_1 = np.array([], dtype="int64")
                csvlx = self.csvlx_1
                csvly = self.csvly_1
                color = (212,212,48)
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.upper_list = self.upper_list_2 = np.array([])
                self.csvux_2 = self.csvuy_2 = np.array([], dtype="int64")
                csvlx = self.csvlx_2
                csvly = self.csvly_2
                color = (178,178,61)
            for i in range(len(csvlx)):
                cv2.circle(self.tracing_img_main_backup, (int(csvlx[i]), int(csvly[i])), self.center_circle, (color), -1)
            for i in self.lower_list_2:
                cx = contours[int(i)][0][0][0]
                cy = contours[int(i)][0][0][1]
                cv2.putText(self.tracing_img_main_backup, (str(i)), (cx, cy+(int(self.scale_bar/20))), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (color),self.center_circle+1)
            
            
        else: #Remove recent data if last entry was to lower list
            if self.contour_list.get() == self.trace_drop_list[0]:
                self.lower_list = self.lower_list_0 = np.array([])
                self.csvlx_0 = self.csvly_0 = np.array([], dtype="int64")
                csvux = self.csvux_0
                csvuy = self.csvuy_0
                color = (255,0,255)
            elif self.contour_list.get() == self.trace_drop_list[1]:
                self.lower_list = self.lower_list_1 = np.array([])
                self.csvlx_1 = self.csvly_1 = np.array([], dtype="int64")
                csvux = self.csvux_1
                csvuy = self.csvuy_1
                color = (212,48,212)
            elif self.contour_list.get() == self.trace_drop_list[2]:
                self.lower_list = self.lower_list_2 = np.array([])
                self.csvlx_2 = self.csvly_2 = np.array([], dtype="int64")
                csvux = self.csvux_2
                csvuy = self.csvuy_2
                color = (178,61,178)

            for i in range(len(csvux)):
                cv2.circle(self.tracing_img_main_backup, (int(csvux[i]), int(csvuy[i])), self.center_circle, (color), -1)
            for i in self.upper_list:
                cx = contours[int(i)][0][0][0]
                cy = contours[int(i)][0][0][1]
                cv2.putText(self.tracing_img_main_backup, (str(i)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (color),self.center_circle+1)
            
        
        resize_trace_img = resize(self.tracing_img_main_backup, self.contour_resize)
        resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))
        self.tracing_image.configure(image=resize_trace_img)
        self.tracing_image.image=resize_trace_img

        self.list_label.configure(text="Upper list: "+str(self.upper_list)+" and Lower list: " +str(self.lower_list), font= font2)
        self.list_label.update()


    def update_image_low(self, tracing_img, csvx, csvy, contours, contour_number, new_data): ##Updates the image when new data is added to the lower list
        if self.contour_list.get() == self.trace_drop_list[0] or "profile_check" not in dir(self) or self.profile_check.get() != 1:
            color_set = (255, 255, 0)
        elif self.contour_list.get() == self.trace_drop_list[1]:
            color_set = (212, 212, 48)
        else:
            color_set = (178, 178, 61)
        for i in range(new_data):
            cv2.circle(tracing_img, (int(csvx[-i]), int(csvy[-i])), self.center_circle, (color_set), -1)
            cv2.circle(self.tracing_img_main, (int(csvx[i]), int(csvy[i])), self.center_circle, (color_set), -1)
        cx = contours[contour_number][0][0][0]
        cy = contours[contour_number][0][0][1]
        cv2.putText(tracing_img, (str(contour_number)), (cx, cy+(int(self.scale_bar/20))), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (color_set),self.center_circle+1)
        cv2.putText(self.tracing_img_main, (str(contour_number)), (cx, cy+(int(self.scale_bar/20))), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (color_set),self.center_circle+1)

        resize_trace_img = resize(tracing_img, self.contour_resize)
        resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))
        self.tracing_image.configure(image=resize_trace_img)
        self.tracing_image.image=resize_trace_img
        
        resize_tracing_img_main = resize(self.tracing_img_main, self.contour_resize)
        resize_tracing_img_main = ImageTk.PhotoImage(Image.fromarray(resize_tracing_img_main))
        self.edge_menu_trace_image.configure(image=resize_tracing_img_main)
        self.edge_menu_trace_image.image=resize_tracing_img_main
        
        if "contour_status" not in dir(self):
            self.contour_status = Label(self.root, text="You have selected some contour data", font= font2)
            self.contour_status.grid(row = 3, column =1, sticky="W")
    
    def update_image_up(self, tracing_img, csvx, csvy, contours, contour_number, new_data): ##Updates the image when new data is added to the upper list
        if self.contour_list.get() == self.trace_drop_list[0] or "profile_check" not in dir(self) or self.profile_check.get() != 1:
            color_set = (255, 0, 255)
        elif self.contour_list.get() == self.trace_drop_list[1]:
            color_set = (212, 48, 212)
        else:
            color_set = (178, 61, 178)
        for i in range(new_data):
            cv2.circle(tracing_img, (int(csvx[-i]), int(csvy[-i])), self.center_circle, (color_set), -1)
            cv2.circle(self.tracing_img_main, (int(csvx[-i]), int(csvy[-i])), self.center_circle, (color_set), -1)
        cx = contours[contour_number][0][0][0]
        cy = contours[contour_number][0][0][1]
        cv2.putText(tracing_img, (str(contour_number)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (color_set),self.center_circle+1)
        cv2.putText(self.tracing_img_main, (str(contour_number)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (color_set),self.center_circle+1)
        
        resize_trace_img = resize(tracing_img, self.contour_resize)
        resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))
        self.tracing_image.configure(image=resize_trace_img)
        self.tracing_image.image=resize_trace_img
        
        resize_tracing_img_main = resize(self.tracing_img_main, self.contour_resize)
        resize_tracing_img_main = ImageTk.PhotoImage(Image.fromarray(resize_tracing_img_main))
        self.edge_menu_trace_image.configure(image=resize_tracing_img_main)
        self.edge_menu_trace_image.image=resize_tracing_img_main

        if "contour_status" not in dir(self):
            self.contour_status = Label(self.root, text="You have selected some contour data", font= font2)
            self.contour_status.grid(row = 3, column =1, sticky="W")
  #Internal/External calculations and Data Saving
    def save_csv(self): ##Saves the upper and lower lists as CSVs
        if "profile_check" not in dir(self) or self.profile_check.get() != 1:
            ratio = str(self.scale_ratio) #Gets the scale ratio from the image
         #Proceeds with normal process if scale_reader doesn't fail    
            tracing_img = cv2.cvtColor(self.crop, cv2.COLOR_GRAY2BGR)
            tracing_img = cv2.copyMakeBorder(tracing_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
            tracing_img = cv2.copyMakeBorder(tracing_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
            width = int(tracing_img.shape[1])
            height = int(tracing_img.shape[0])

            scale_length = int(self.img_width/10)
            scale_text = str(round((scale_length/self.scale_ratio), 3)) + "um"

            needed_length = 8 - len(ratio)

            if needed_length > 0: # Adds zeroes until the string is eight characters long
                additional_length =""
                for _ in range(needed_length):
                    additional_length += "0"
                ratio= additional_length + ratio
            else:
                ratio = ratio[:8] 
            
         #Saves the Data
            
            csvlx = self.csvlx_0.astype(np.int)
            csvux = self.csvux_0.astype(np.int)
            csvly = self.csvly_0.astype(np.int)
            csvuy = self.csvuy_0.astype(np.int)
            if "csvux_1" in dir(self):
                csvlx = np.append(csvlx, self.csvlx_1)
                csvux = np.append(csvux, self.csvux_1)
                csvly = np.append(csvly, self.csvly_1)
                csvuy = np.append(csvuy, self.csvuy_1)
            if "csvux_2" in dir(self):
                csvlx = np.append(csvlx, self.csvlx_2)
                csvux = np.append(csvux, self.csvux_2)
                csvly = np.append(csvly, self.csvly_2)
                csvuy = np.append(csvuy, self.csvuy_2)
            csvlx = csvlx.astype(np.int)
            csvux = csvux.astype(np.int)
            csvly = csvly.astype(np.int)
            csvuy = csvuy.astype(np.int)

            if len(self.contour_iterations) > 0:
                lower_thresh_value = str(self.contour_iterations[0][0])
                upper_thresh_value = str(self.contour_iterations[0][1])
                needed_length = 3-len(lower_thresh_value)
                if needed_length >0:
                    additional_length=""
                    for _ in range(needed_length):
                        additional_length += "0"
                    lower_thresh_value= additional_length + lower_thresh_value
                needed_length = 3-len(upper_thresh_value)
                if needed_length >0:
                    additional_length=""
                    for _ in range(needed_length):
                        additional_length += "0"
                    upper_thresh_value= additional_length + upper_thresh_value
            else:
                lower_thresh_value = str(self.lower_thresh_old)
                upper_thresh_value = str(self.upper_thresh_old)
                needed_length = 3-len(lower_thresh_value)
                if needed_length >0:
                    additional_length=""
                    for _ in range(needed_length):
                        additional_length += "0"
                    lower_thresh_value= additional_length + lower_thresh_value
                needed_length = 3-len(upper_thresh_value)
                if needed_length >0:
                    additional_length=""
                    for _ in range(needed_length):
                        additional_length += "0"
                    upper_thresh_value= additional_length + upper_thresh_value

            
            filename = os.path.basename(self.path) #Saves the csvs in the unworkedcsvs folder
            filename = filename[:-4]
            name_entry = str(self.trace_drop_list[0])
            if len(name_entry) > 0:
                name_entry+="-"
            if self.in_or_ex == 1:
                unworked_dir = self.current_dir+"/unworkedcsv/"
                check_dir = Path(unworked_dir)
                if check_dir.exists() is False:
                    os.mkdir(unworked_dir)
                    os.mkdir(self.current_dir+"/workedcsv")
                np.savetxt(unworked_dir+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(self.image_ratio)+ratio+".csv",list(zip(csvlx, csvly)), fmt = "%s", delimiter = ",")
                np.savetxt(unworked_dir+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(self.image_ratio)+ratio+".csv",list(zip(csvux, csvuy)), fmt = "%s", delimiter = ",")
            else:
                worked_dir = self.current_dir+"/worked-internalcsv/"
                filefolder = "/"+filename+"/"
                if Path(worked_dir+filefolder).exists() is False:
                    os.mkdir(worked_dir+filefolder)
                np.savetxt(worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(self.image_ratio)+ratio+".csv",list(zip(csvlx, csvly)), fmt = "%s", delimiter = ",")
                np.savetxt(worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(self.image_ratio)+ratio+".csv",list(zip(csvux, csvuy)), fmt = "%s", delimiter = ",")
            for i in range(len(csvux)):
                cv2.circle(tracing_img, (int(csvux[i]), int(csvuy[i])), 3, (255,0,255), -1)
            for i in range(len(csvlx)):
                cv2.circle(tracing_img, (int(csvlx[i]), int(csvly[i])), 3, (255,255,0), -1)
            for i in range(self.label_text+2):
                cv2.line(tracing_img, (width-(scale_length+80), (height-20-i)), ((width-80), (height-20-i)), (255,255,255), (1))
            cv2.line(tracing_img, (width-(scale_length+80), (height-19)), ((width-80), (height-19)), (0,0,0), (1))
            cv2.line(tracing_img, (width-(scale_length+80), (height-21-(self.label_text+2))), ((width-80), (height-21-(self.label_text+2))), (0,0,0), (1))
            cv2.line(tracing_img, (width-(scale_length+81), (height-20)), (width-(scale_length+81), (height-21-(self.label_text+2))), (0,0,0), (1))
            cv2.line(tracing_img, (width-79, (height-20)), (width-79, (height-21-(self.label_text+2))), (0,0,0), (1))
            cv2.putText(tracing_img, scale_text, ((width-(scale_length+120)), (height-22-(self.label_text+4))), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2)

            if self.in_or_ex == 1:
                cv2.imwrite((unworked_dir+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+".png"), tracing_img)
            else:
                cv2.imwrite((worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+".png"), tracing_img)
                int_save_folder_path = worked_dir+filefolder
                self.int_lower_csv = worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(self.image_ratio)+ratio+".csv"
                self.int_upper_csv = worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(self.image_ratio)+ratio+".csv"
        
        else:
            for i in range(len(self.trace_drop_list)):
                ratio = str(self.scale_ratio) #Gets the scale ratio from the image
             #Proceeds with normal process if scale_reader doesn't fail    
                tracing_img = cv2.cvtColor(self.crop, cv2.COLOR_GRAY2BGR)
                tracing_img = cv2.copyMakeBorder(tracing_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
                tracing_img = cv2.copyMakeBorder(tracing_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
                width = int(tracing_img.shape[1])
                height = int(tracing_img.shape[0])

                scale_length = int(self.img_width/10)
                scale_text = str(round((scale_length/self.scale_ratio), 3)) + "um"

                needed_length = 8 - len(ratio)

                if needed_length > 0: # Adds zeroes until the string is eight characters long
                    additional_length =""
                    for _ in range(needed_length):
                        additional_length += "0"
                    ratio= additional_length + ratio
                else:
                    ratio = ratio[:8] 
                
             #Saves the Data
                
                if i == 0:
                    csvlx = self.csvlx_0.astype(np.int)
                    csvux = self.csvux_0.astype(np.int)
                    csvly = self.csvly_0.astype(np.int)
                    csvuy = self.csvuy_0.astype(np.int)
                    name_entry = str(self.trace_drop_list[0])
                elif i == 1:
                    csvlx = self.csvlx_1.astype(np.int)
                    csvux = self.csvux_1.astype(np.int)
                    csvly = self.csvly_1.astype(np.int)
                    csvuy = self.csvuy_1.astype(np.int)
                    name_entry = str(self.trace_drop_list[1])
                elif i == 2:
                    csvlx = self.csvlx_2.astype(np.int)
                    csvux = self.csvux_2.astype(np.int)
                    csvly = self.csvly_2.astype(np.int)
                    csvuy = self.csvuy_2.astype(np.int)
                    name_entry = str(self.trace_drop_list[2])

                lower_thresh_value = str(self.contour_iterations[i][0])
                upper_thresh_value = str(self.contour_iterations[i][1])
                needed_length = 3-len(lower_thresh_value)
                if needed_length >0:
                    additional_length=""
                    for _ in range(needed_length):
                        additional_length += "0"
                    lower_thresh_value= additional_length + lower_thresh_value
                needed_length = 3-len(upper_thresh_value)
                if needed_length >0:
                    additional_length=""
                    for _ in range(needed_length):
                        additional_length += "0"
                    upper_thresh_value= additional_length + upper_thresh_value

                
                filename = os.path.basename(self.path) #Saves the csvs in the unworkedcsvs folder
                filename = filename[:-4]
                
                if len(name_entry) > 0:
                    name_entry+="-"
                if self.in_or_ex == 1:
                    unworked_dir = self.current_dir+"/unworkedcsv/"
                    check_dir = Path(unworked_dir)
                    if check_dir.exists() is False:
                        os.mkdir(unworked_dir)
                        os.mkdir(self.current_dir+"/workedcsv")
                    np.savetxt(unworked_dir+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(self.image_ratio)+ratio+".csv",list(zip(csvlx, csvly)), fmt = "%s", delimiter = ",")
                    np.savetxt(unworked_dir+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(self.image_ratio)+ratio+".csv",list(zip(csvux, csvuy)), fmt = "%s", delimiter = ",")
                else:
                    worked_dir = self.current_dir+"/worked-internalcsv/"
                    filefolder = "/"+filename+"/"
                    if Path(worked_dir+filefolder).exists() is False:
                        os.mkdir(worked_dir+filefolder)
                    np.savetxt(worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(self.image_ratio)+ratio+".csv",list(zip(csvlx, csvly)), fmt = "%s", delimiter = ",")
                    np.savetxt(worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(self.image_ratio)+ratio+".csv",list(zip(csvux, csvuy)), fmt = "%s", delimiter = ",")
                for i in range(len(csvux)):
                    cv2.circle(tracing_img, (csvux[i], csvuy[i]), 3, (255,0,255), -1)
                for i in range(len(csvlx)):
                    cv2.circle(tracing_img, (csvlx[i], csvly[i]), 3, (255,255,0), -1)
                for i in range(self.label_text+2):
                    cv2.line(tracing_img, (width-(scale_length+80), (height-20-i)), ((width-80), (height-20-i)), (255,255,255), (1))
                cv2.line(tracing_img, (width-(scale_length+80), (height-19)), ((width-80), (height-19)), (0,0,0), (1))
                cv2.line(tracing_img, (width-(scale_length+80), (height-21-(self.label_text+2))), ((width-80), (height-21-(self.label_text+2))), (0,0,0), (1))
                cv2.line(tracing_img, (width-(scale_length+81), (height-20)), (width-(scale_length+81), (height-21-(self.label_text+2))), (0,0,0), (1))
                cv2.line(tracing_img, (width-79, (height-20)), (width-79, (height-21-(self.label_text+2))), (0,0,0), (1))
                cv2.putText(tracing_img, scale_text, ((width-(scale_length+120)), (height-22-(self.label_text+4))), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2)

                if self.in_or_ex == 1:
                    cv2.imwrite((unworked_dir+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+".png"), tracing_img)
                else:
                    cv2.imwrite((worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+".png"), tracing_img)
                    int_save_folder_path = worked_dir+filefolder
                    self.int_lower_csv = worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(self.image_ratio)+ratio+".csv"
                    self.int_upper_csv = worked_dir+filefolder+filename+"-"+name_entry+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(self.image_ratio)+ratio+".csv"
            
        if self.in_or_ex ==1: 
            if "short_dist_btn" not in dir(self):
                self.short_dist_btn = Button(self.root, text="Calculate Shortest Distance", font = font1, bg="dodger blue", command = self.shortest_distance)
                self.short_dist_btn.grid(row=5, column=0, pady=(10,0))
            waiting_files = len(os.listdir(unworked_dir))//3
            if "calculate_status" not in dir(self):
                self.calculate_status = Label(self.root, text="There are "+str(waiting_files)+" images waiting for calculations", font = font2)
                self.calculate_status.grid(row =5, column = 1, sticky="W", pady=(10,0))
                self.total_calculations_entry = Entry(self.root, font=font2)
                self.total_calculations_entry.insert(END, "500")
                self.total_calculations_entry.grid(row=7, column = 1)
                self.total_calculations_label = Label(self.root, text="The above determines the number of\nshortest distance calculations performed", font=font2)
                self.total_calculations_label.grid(row=8, column = 1, sticky="W")
                reverse_profiles = ["Bottom to Top", "Top to Bottom", "Both", "Vertical", "All of the Above"]
                self.reverse_profile = StringVar()
                self.reverse_profile.set(reverse_profiles[0])
                self.reverse_profile_drop = OptionMenu(self.root, self.reverse_profile, *reverse_profiles)
                self.reverse_profile_drop.config(bg="deep sky blue", font=font2)
                self.reverse_profile_drop.grid(row=7, column = 0)
                self.reverse_status = Label(self.root, font=font2, text="The droplist determines the direction \nthe shortest distance is calculated")
                self.reverse_status.grid(row=8, column =0)
                reverse_drop_list = self.root.nametowidget(self.reverse_profile_drop.menuname)
                reverse_drop_list.config(font=font2)   
            else:
                self.calculate_status.configure(text="There are "+str(waiting_files)+" images waiting for calculations", font = font2)
                self.calculate_status.update()
        else:
            if "int_calc_btn" not in dir(self):
                self.int_calc_btn = Button(self.root, text="Calculate Internal Stats", font=font1, bg="dodger blue", command = self.poly_select)
                self.int_calc_btn.grid(row=5, column = 0, pady=(5,0))
                self.reverse_check = IntVar()
                self.reverse_check_btn = Checkbutton(self.root, text="Compare upper to lower (instead of lower to upper)", font=font2, variable=self.reverse_check)
                self.reverse_check_btn.grid(row=5, column = 1, pady=(5,0))

     #Resets menu
        self.cbtn.destroy()
        del self.cbtn
        self.thresh_btn.destroy()
        del self.thresh_btn
        self.edge_btn.destroy()
        del self.edge_btn
        self.save_csv_btn.destroy()
        del self.save_csv_btn
        self.crop_status.grid_remove()
        del self.crop_status
        self.contour_status.grid_remove()
        del self.contour_status
        del self.lower_list_0

        if "thresh_status" in dir(self):
            self.thresh_status.grid_remove()
            del self.thresh_status

        self.status_path.configure(text="Your CSV has been saved")
        self.status_path.update()

    def shortest_distance(self): ##Finds the files to be used for the shortest distance calcualtion
        unworked_dir = self.current_dir+"/unworkedcsv/"
        worked_dir = self.current_dir+"/workedcsv/"
        for filename in os.listdir(unworked_dir): #Iterations through the unworked folder to find csv pairs
            if "Lower" in filename and "Upper" not in filename:
                ratio = float(filename[-12:-4])
                scale_ratio = float(filename[-13:-12])
                upper_filename = filename[:-18] + "Upper"+filename[-13:]
                save_folder_name = filename[:-19]
                save_folder_path = worked_dir+save_folder_name +"/"
                check_dir = Path(save_folder_path)
                if check_dir.exists() is False:
                    os.mkdir(save_folder_path)
                if self.reverse_profile.get() == "Bottom to Top":
                    shortest_distance_calc((unworked_dir+filename), (unworked_dir+upper_filename), ratio, self.current_dir, save_folder_path, scale_ratio, int(self.total_calculations_entry.get()), 0)
                elif self.reverse_profile.get() == "Top to Bottom":
                    shortest_distance_calc((unworked_dir+upper_filename), (unworked_dir+filename), ratio, self.current_dir, save_folder_path, scale_ratio, int(self.total_calculations_entry.get()), 1)
                elif self.reverse_profile.get() == "Both":
                    shortest_distance_calc((unworked_dir+filename), (unworked_dir+upper_filename), ratio, self.current_dir, save_folder_path, scale_ratio, int(self.total_calculations_entry.get()), 0)
                    shortest_distance_calc((unworked_dir+upper_filename), (unworked_dir+filename), ratio, self.current_dir, save_folder_path, scale_ratio, int(self.total_calculations_entry.get()), 1)
                elif self.reverse_profile.get() == "Vertical":
                    shortest_distance_calc((unworked_dir+filename), (unworked_dir+upper_filename), ratio, self.current_dir, save_folder_path, scale_ratio, int(self.total_calculations_entry.get()), 2)
                elif self.reverse_profile.get() == "All of the Above":
                    shortest_distance_calc((unworked_dir+filename), (unworked_dir+upper_filename), ratio, self.current_dir, save_folder_path, scale_ratio, int(self.total_calculations_entry.get()), 0)
                    shortest_distance_calc((unworked_dir+upper_filename), (unworked_dir+filename), ratio, self.current_dir, save_folder_path, scale_ratio, int(self.total_calculations_entry.get()), 1)
                    shortest_distance_calc((unworked_dir+filename), (unworked_dir+upper_filename), ratio, self.current_dir, save_folder_path, scale_ratio, int(self.total_calculations_entry.get()), 2)
                shutil.move((unworked_dir+filename), (save_folder_path+filename))
                shutil.move((unworked_dir+upper_filename), (save_folder_path+upper_filename))
                shutil.move((unworked_dir+save_folder_name+".png"), (save_folder_path+save_folder_name+".png"))
        self.short_dist_btn.destroy()
        del self.short_dist_btn
        self.calculate_status.grid_remove()
        del self.calculate_status
        self.reverse_profile_drop.destroy()
        del self.reverse_profile_drop
        self.reverse_status.destroy()
        del self.reverse_status
        self.total_calculations_entry.destroy()
        del self.total_calculations_entry
        self.total_calculations_label.destroy()
        del self.total_calculations_label
        self.status_path.configure(text=("Please select another image to continue"), font=font2)
        self.status_path.update()

    def on_pick(self, event):
        if self.current_artist is None:
            self.current_artist = event.artist
            if isinstance(event.artist, patches.Circle):
                if event.mouseevent.dblclick:
                    if self.mousepress == "right":
                        if len(self.poly_ax.patches) > 2:
                            event.artist.remove()
                            xdata = list(self.line_object[0].get_xdata())
                            ydata = list(self.line_object[0].get_ydata())
                            for i in range(0,len(xdata)):
                                if event.artist.get_label() == self.listLabelPoints[i]:
                                    xdata.pop(i) 
                                    ydata.pop(i) 
                                    self.listLabelPoints.pop(i)
                                    break
                            self.line_object[0].set_data(xdata, ydata)
                            plt.draw()
                else:
                    x0, y0 = self.current_artist.center
                    x1, y1 = event.mouseevent.xdata, event.mouseevent.ydata
                    self.offset = [(x0 - x1), (y0 - y1)]
            elif isinstance(event.artist, Line2D):
                if event.mouseevent.dblclick:
                    if self.mousepress == "left":
                        self.n_point = self.n_point+1
                        x, y = event.mouseevent.xdata, event.mouseevent.ydata
                        newPointLabel = "point"+str(self.n_point)
                        point_object = patches.Circle([x, y], radius=15, color='r', fill=False, lw=2,
                                alpha=self.point_alpha_default, transform=self.poly_ax.transData, label=newPointLabel)
                        point_object.set_picker(5)
                        self.poly_ax.add_patch(point_object)
                        xdata = list(self.line_object[0].get_xdata())
                        ydata = list(self.line_object[0].get_ydata())
                        pointInserted = False
                        for i in range(0,len(xdata)-1):
                            if x > min(xdata[i],xdata[i+1]) and x < max(xdata[i],xdata[i+1]) and \
                            y > min(ydata[i],ydata[i+1]) and y < max(ydata[i],ydata[i+1]) :
                                xdata.insert(i+1, x)
                                ydata.insert(i+1, y)
                                self.listLabelPoints.insert(i+1, newPointLabel)
                                pointInserted = True
                                break
                        self.line_object[0].set_data(xdata, ydata)
                        self.poly_canvas.draw()

                        if not pointInserted:
                            print("Error: point not inserted")
                else:
                    xdata = event.artist.get_xdata()
                    ydata = event.artist.get_ydata()
                    x1, y1 = event.mouseevent.xdata, event.mouseevent.ydata
                    self.offset = xdata[0] - x1, ydata[0] - y1

    def on_press(self, event):
        self.currently_dragging = True
        if event.button == 3:
            self.mousepress = "right"
        elif event.button == 1:
            self.mousepress = "left"

    def on_release(self, event):
        self.current_artist = None
        self.currently_dragging = False
    
    def on_motion(self, event):
        if not self.currently_dragging:
            return
        if self.current_artist == None:
            return
        if event.xdata == None:
            return
        dx, dy = self.offset
        if isinstance(self.current_artist, patches.Circle):
            cx, cy =  event.xdata + dx, event.ydata + dy
            self.current_artist.center = cx, cy
            xdata = list(self.line_object[0].get_xdata())
            ydata = list(self.line_object[0].get_ydata())
            for i in range(0,len(xdata)): 
                if self.listLabelPoints[i] == self.current_artist.get_label():
                    xdata[i] = cx
                    ydata[i] = cy
                    break
            self.line_object[0].set_data(xdata, ydata)
        elif isinstance(self.current_artist, Line2D):
            xdata = list(self.line_object[0].get_xdata())
            ydata = list(self.line_object[0].get_ydata())
            xdata0 = xdata[0]
            ydata0 = ydata[0]
            for i in range(0,len(xdata)): 
                    xdata[i] = event.xdata + dx + xdata[i] - xdata0
                    ydata[i] = event.ydata + dy + ydata[i] - ydata0 
            self.line_object[0].set_data(xdata, ydata)
            for p in self.poly_ax.patches:
                pointLabel = p.get_label()
                i = self.listLabelPoints.index(pointLabel) 
                p.center = xdata[i], ydata[i]
        self.poly_canvas.draw()

    def on_click(self, event):
        if event and event.dblclick:
            if len(self.listLabelPoints) < 2:
                self.n_point = self.n_point+1
                x, y = event.xdata, event.ydata
                newPointLabel = "point"+str(self.n_point)
                point_object = patches.Circle([x, y], radius=15, color='r', fill=False, lw=2,
                        alpha=self.point_alpha_default, transform=self.poly_ax.transData, label=newPointLabel)
                point_object.set_picker(5)
                self.poly_ax.add_patch(point_object)
                self.listLabelPoints.append(newPointLabel)
                if len(self.listLabelPoints) == 2:
                    xdata = []
                    ydata = []
                    for p in self.poly_ax.patches:
                        cx, cy = p.center
                        xdata.append(cx)
                        ydata.append(cy)
                    self.line_object = self.poly_ax.plot(xdata, ydata, alpha=0.5, c='r', lw=2, picker=True)
                    self.line_object[0].set_pickradius(5)
                self.poly_update_btn.grid(row = 3, column = 2)
                self.poly_canvas.draw()

    def save_poly_curve(self, event):
        if len(self.listLabelPoints) > 1 and event.key in ["q", "Q"]:
            user_points = []
            for p in self.poly_ax.patches:
                #cx, cy = p.center
                cx = p.center
                user_points.append(cx)
                #ydata.append(cy)
            user_points = np.array(user_points)
            user_points = user_points.astype(np.int)
            self.x_data = []
            self.y_data = []
            for i in range(len(user_points)):
                self.x_data.append(user_points[i][0])
                self.y_data.append(user_points[i][1])



    def poly_select(self): ##Creates a menu with a slider to adjust the order of polynomial fit for internal oxidaiton
     #Create Menu
        if "poly_menu" in dir(self):
            self.poly_menu.destroy()
        
        self.poly_menu = Toplevel()
        self.poly_menu.title("Lower Boundary Trend Menu")
        self.poly_menu.configure(bg="gray69")
        self.poly_menu.minsize(300,300)
     #Load Data
        lower_csv = self.int_lower_csv
        upper_csv = self.int_upper_csv
        fileinput = os.path.basename(lower_csv)
        filelocation = os.path.dirname(lower_csv)
        ratio = float(lower_csv[-12:-4])
        scale_ratio = float(lower_csv[-13:-12])
        current_dir = os.getcwd()
        lower_thresh_value = str(self.lower_thresh_old)
        upper_thresh_value = str(self.upper_thresh_old)
        lower_list_array = self.lower_list

        with open(lower_csv) as csvfile:
            c1 = [tuple(map(int, row)) for row in csv.reader(csvfile)]
        with open(upper_csv) as csvfile2:
            self.c2 = [tuple(map(int, row)) for row in csv.reader(csvfile2)]
        with open(upper_csv) as csvfile2:
            Curve2 = csv.reader(csvfile2, delimiter=",")
            self.c2_check = np.empty(0)
            for line in Curve2:
                self.c2_check = np.append(self.c2_check, line[0])
        self.c2_check = self.c2_check.astype(np.float64)
       
        c1_x = c1_y = np.array([])
        for i in range(len(c1)):
            c1_x = np.append(c1_x, c1[i][0])
            c1_y = np.append(c1_y, c1[i][1])

     #Prepare Image
        internal_img = cv2.imread(self.path, 0)
        internal_img = internal_img[self.upper_crop_val:self.lower_crop_val, 0:internal_img.shape[1]]
        self.in_line_img = cv2.cvtColor(internal_img, cv2.COLOR_GRAY2BGR)
        self.in_line_img = cv2.copyMakeBorder(self.in_line_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        self.in_line_img = cv2.copyMakeBorder(self.in_line_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        if self.internal_threshold[0] == 0:
            internal_img = cv2.copyMakeBorder(internal_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=255)
            internal_img = cv2.medianBlur(internal_img, 5)
            internal_img = cv2.copyMakeBorder(internal_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=255)
        else:
            internal_img = cv2.copyMakeBorder(internal_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
            internal_img = cv2.medianBlur(internal_img, 5)
            internal_img = cv2.copyMakeBorder(internal_img, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
        self.in_line_img = cv2.cvtColor(internal_img, cv2.COLOR_GRAY2BGR)
        internal_img = cv2.inRange(internal_img, self.internal_threshold[0], self.internal_threshold[1])
        segement_traced_img = cv2.cvtColor(internal_img, cv2.COLOR_GRAY2BGR)
        internal_img_width = internal_img.shape[1]
        micron_slice = ratio 
        
        for i in range(len(self.c2)):
            cv2.circle(self.in_line_img, (self.c2[i][0], self.c2[i][1]), 3, (255,0,255), -1)
        for i in range(len(c1)):
            cv2.circle(self.in_line_img, (c1[i][0], c1[i][1]), 3, (255,255,0), -1)

     #Centroid Calculations
        contours_centroid, _ = cv2.findContours(internal_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        centroid_img = cv2.cvtColor(internal_img, cv2.COLOR_GRAY2BGR)
        centroid = np.array([])
        centroid_distance = np.array([])
        circularity = np.array([])
        self.internal_list = self.internal_list.astype(np.int32)
        for i in self.internal_list:
            moment = cv2.moments(contours_centroid[i])
            if moment["m00"] !=0:
                cx = int(moment["m10"]/moment["m00"])
                cy = int(moment["m01"]/moment["m00"])
                cv2.circle(centroid_img, (cx,cy), self.center_circle, (0,0,255), -1)
                cv2.putText(centroid_img,(str(i)), (cx,cy), cv2.FONT_HERSHEY_SIMPLEX, self.center_circle, (255,255,0), self.center_circle)
                horizontal_range = list(range(cx - self.vertical_check, cx+self.vertical_check))
                for z in range(len(horizontal_range)):
                    if horizontal_range[z] in self.c2_check:
                        cparray = [(cx, cy)]
                        break
                if len(cparray) != 0:
                    c2_edit = [(x, y) for x, y in self.c2 if x in range(cx - self.edge_limit, cx + self.edge_limit)]
                    centroid = np.append(centroid, i)
                    centroid_distance = np.append(centroid_distance, ((distance.cdist(cparray,c2_edit).min(axis=1))/ratio))
                    area = cv2.contourArea(contours_centroid[i])
                    perimeter = cv2.arcLength(contours_centroid[i], True)
                    if perimeter != 0:
                        circularity_val = 4*pi*(area/(perimeter**2))
                        circularity = np.append(circularity, circularity_val)
                    else:
                        circularity = np.append(circularity, "None")
                    cparray=[]

     #Line Boundary (There is probably some dead code here, I will clean it up later)
        fig, self.poly_ax = plt.subplots()

        self.poly_ax.set_title("Double left click to create initial vertices\nDouble left on line to create additional vertices, double right to remove\nClick and drag mouse to move vertices")
        self.poly_ax.set_aspect('equal')
        plt.scatter(x = c1_x, y = c1_y, c="b")
        self.poly_ax.set_xlim(0, int(max(c1_x)*1.1))
        self.poly_ax.set_ylim(0, int(max(c1_y)*1.1))
        plt.gca().invert_yaxis()
        plt.grid(True)


        self.listLabelPoints = []
        self.point_alpha_default = 0.8
        self.mousepress = None
        self.currently_dragging = False
        self.current_artist = None
        self.offset = [0,0]
        self.n_point = 0
        self.line_object = None

        self.poly_figure = fig

        self.poly_canvas = FigureCanvasTkAgg(self.poly_figure, master=self.poly_menu)
        self.poly_canvas.draw()
        self.poly_canvas.get_tk_widget().grid(row=1, columnspan=2)
        self.poly_toolbar_frame = Frame(master=self.poly_menu)
        self.poly_toolbar_frame.grid(row = 2, columnspan = 2)
        poly_toolbar = NavigationToolbar2Tk(self.poly_canvas, self.poly_toolbar_frame)

        self.poly_canvas.mpl_connect('button_press_event', self.on_click)
        self.poly_canvas.mpl_connect('button_press_event', self.on_press)
        #fig.canvas.mpl_connect('button_press_event', on_press)
        self.poly_canvas.mpl_connect('button_release_event', self.on_release)
        self.poly_canvas.mpl_connect('pick_event', self.on_pick)
        self.poly_canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.poly_canvas.mpl_connect("key_press_event", self.save_poly_curve)
        self.poly_update_btn = Button(self.poly_menu, text="Finish Calculations from Fit", font=font2, bg = "SeaGreen2", command= lambda: self.poly_calculations(ratio, current_dir, fileinput, filelocation, internal_img_width, micron_slice, segement_traced_img, lower_thresh_value, upper_thresh_value, internal_img, centroid, centroid_distance, circularity, centroid_img))
        


    def poly_calculations(self, ratio, current_dir, fileinput, filelocation, internal_img_width, micron_slice, segement_traced_img, lower_thresh_value, upper_thresh_value, internal_img, centroid, centroid_distance, circularity, centroid_img): ##Performs the caluclations for stats about the positions of the internal oxide clusters
     #Slices
        user_points = []
        for p in self.poly_ax.patches:
            #cx, cy = p.center
            cx = p.center
            user_points.append(cx)
            #ydata.append(cy)
        user_points = np.array(user_points)
        user_points = user_points.astype(np.int)
        self.x_data = []
        self.y_data = []
        ind = np.lexsort((user_points[:,1],user_points[:,0]))
        user_points = user_points[ind]
        for i in range(len(user_points)):
            self.x_data.append(user_points[i][0])
            self.y_data.append(user_points[i][1])

        left_limit = int(min(self.x_data)*1.1)
        right_limit = int(max(self.x_data)*0.9)

        list_list_of_areas = []
        list_list_of_pct = []
        recent_y = None
        
        step_size = (int((right_limit - left_limit)/100))
        if step_size == 0:
            step_size = 1
        for i in range(left_limit, right_limit,step_size):
            width_check = list(range(i-self.vertical_check, i+self.vertical_check))
            minimum_y = 0
            for z in range(len(width_check)):    
                if width_check[z] in self.c2_check:
                    initial_x = width_check[z]
                    potential_list = np.where(self.c2_check == initial_x)
                    for p in potential_list[0]: #Looks for the lowest point at a given x
                        if self.c2[p][1] > minimum_y:
                            minimum_y = self.c2[p][1]
                    break
            list_of_areas = []
            list_of_pct = []
            if minimum_y != 0 or recent_y is not None:
                if minimum_y == 0:
                    minimum_y = recent_y
                try:
                    for row in range(int((np.interp(i, self.x_data, self.y_data)-minimum_y)/micron_slice)+1):
                        
                        temp_slice = internal_img[int(minimum_y+(row*micron_slice)):int(minimum_y+((row+1)*micron_slice)), i:int(i+((internal_img_width*.8)/100))]
                        contours, _ = cv2.findContours(temp_slice, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                        contour_sum = 0
                        for contour in contours:
                            contour_area = cv2.contourArea(contour)
                            contour_sum += contour_area
                        total_area = micron_slice * ((internal_img_width*.8)/100)
                        slice_pct_val = contour_sum / total_area
                        contour_sum_adj = contour_sum / (ratio**2)
                        list_of_areas.append(contour_sum_adj)
                        list_of_pct.append(slice_pct_val)
                        cv2.putText(segement_traced_img, ("_"), (i, int(minimum_y+(row*micron_slice))), cv2.FONT_HERSHEY_SIMPLEX, (self.label_text+2), (0,255,255),(self.center_circle+3))
                    list_list_of_areas.append(list_of_areas)
                    list_list_of_pct.append(list_of_pct)
                    recent_y = minimum_y
                except:
                    continue
            else:
                list_list_of_areas.append([np.nan])
                list_list_of_pct.append([np.nan])
        
        check_list=[]
        inner_limit = inner_limit_x = np.array([])
        step_size = (int((right_limit - left_limit)/500))
        if step_size == 0:
            step_size = 1
        for i in range(left_limit, right_limit, step_size):
            poly_check = list(range(i-self.vertical_check, i+self.vertical_check))
            for z in range(len(poly_check)):
                if poly_check[z] in self.c2_check:
                    try:
                        check_list = [(i, (np.interp(i, self.x_data, self.y_data)))]
                        break
                    except:
                        continue
            if len(check_list) != 0:
                c2_edit = [(x, y) for x, y in self.c2 if x in range(int(i - (1.5*self.edge_limit)), int(i + (1.5*self.edge_limit)))]
                inner_limit = np.append(inner_limit, (distance.cdist(check_list,c2_edit).min(axis=1)/ratio))
                inner_limit_x = np.append(inner_limit_x, i)
            check_list = []

        n = len(max(list_list_of_areas, key=len))
        matrix_areas = [x + [np.nan]*(n-len(x)) for x in list_list_of_areas]
        matrix_pct = [x + [np.nan]*(n-len(x)) for x in list_list_of_pct]
        total_area = np.nansum(matrix_areas, axis=0)
        average_pct = np.nanmean(matrix_pct, axis=0)
        depth_number = np.array([])
        for i in range(len(average_pct)):
            depth_number = np.append(depth_number, i)

        quartiles = percentile(inner_limit, [25,50,75])
     #Save Summary Data
        csv_summary_location = current_dir+"/Internal Oxidation Summary.csv"
        if Path(csv_summary_location).is_file() is False:
            file_start = np.array(["Location", "ratio", "Mean", "Median", "Q1", "Q3", "SD", "Data Points"])
            np.savetxt(csv_summary_location, file_start[None], fmt="%s", delimiter=",")
        with open(csv_summary_location, "a", newline="") as newFile:
            newFileWriter = csv.writer(newFile)
            newFileWriter.writerow([fileinput[:-19], str(ratio), str(round(np.mean(inner_limit),5)), str(round(quartiles[1], 5)), str(round(quartiles[0], 5)), str(round(quartiles[2], 5)), str(round(np.std(inner_limit), 5)), str(len(inner_limit))])
     #Save Continuity Data
        csv_continuity = filelocation + "/"+fileinput[:-19]+lower_thresh_value+"-"+upper_thresh_value+"-Continuity.csv"
        np.savetxt(csv_continuity, list(zip(depth_number, total_area, average_pct)), fmt="%s", delimiter=",", header ="Slice Number, Slice Area (um2), Slice Continuity")
        cv2.imwrite((filelocation+"/"+fileinput[:-19]+"-Slices.png"), segement_traced_img)
     #Save Circularity Data
        csv_circularity_summary = filelocation + "/"+fileinput[:-19]+lower_thresh_value+"-"+upper_thresh_value+"-Circularity.csv"
        np.savetxt(csv_circularity_summary, list(zip(centroid, centroid_distance, circularity)), fmt="%s", delimiter = ",", header ="Centroid Number, Centroid Shortest Distance(um), Circularity")
        cv2.imwrite((filelocation+"/"+fileinput[:-19]+"-Centroids.png"), centroid_img)

     #Save Line Boundary Data
        csv_polynomial_summary = filelocation + "/"+fileinput[:-19]+lower_thresh_value+"-"+upper_thresh_value+"-LineBoundaryCalc.csv"
        np.savetxt(csv_polynomial_summary, list(zip(inner_limit, inner_limit_x)), fmt="%s", delimiter = ",", header ="Distance, X Location")
        
        for i in range(0, len(self.x_data)-1):
            cv2.line(self.in_line_img, (int(self.x_data[i]), int(self.y_data[i])), (int(self.x_data[i+1]), int(self.y_data[i+1])), color = (0,0,255), thickness = 3)
        cv2.imwrite((filelocation+"/"+fileinput[:-19]+"-LineBoundary.png"), self.in_line_img)
        self.poly_menu.destroy()
        self.int_calc_btn.destroy()
        del self.int_calc_btn
        self.reverse_check_btn.destroy()
        del self.reverse_check_btn


 #Concavity functions
    def load_csv(self): ##Allows the user to select a data set to be used in the concavity calculations
        current_dir = os.getcwd()
        worked_dir = current_dir + "/workedcsv"
        self.lower_csv_cc = filedialog.askopenfilename(initialdir = worked_dir, filetypes = [("CSV",".csv" )])
        if len(self.lower_csv_cc)>0:
            if "Lower" in self.lower_csv_cc:
                ratio = float(self.lower_csv_cc[-12:-4])
                self.upper_csv_cc = self.lower_csv_cc[:-18] + "Upper"+self.lower_csv_cc[-13:]
            elif "Upper" in self.lower_csv_cc:
                ratio = float(self.lower_csv_cc[-12:-4])
                self.upper_csv_cc = self.lower_csv_cc
                self.lower_csv_cc = self.upper_csv_cc[:-18] +"Lower"+self.upper_csv_cc[-13:]
            self.cc_csv_status.configure(text ="Data has been selected")
            self.cc_csv_status.update()
            
            if "cc_calc_btn" not in dir(self):
                self.cc_calc_btn = Button(self.cc_menu, text="Calculate Concavities", font=font1, bg="sky blue", command = self.poly_calc)
                self.cc_calc_btn.grid(row=2, column = 0)
        else:
            self.cc_csv_status.configure(text="No data has been selected")
            self.cc_csv_status.update()

    def poly_calc(self): ##Loads the data sets and fits a polynomial and finds regions within a certain level of concavity (up or down) and highlights them
     #Load The Images
        x1 = np.empty(0) #Creates an empty data set to store CSV values
        y1 = np.empty(0)
        fileinput = self.lower_csv_cc
        with open(fileinput) as csvfile:
            Curve = csv.reader(csvfile, delimiter=",")
            for line in Curve:
                x1 = np.append(x1, line[0])
                y1 = np.append(y1, line[1])

        x2 = np.empty(0)
        y2 = np.empty(0)
        fileinput2 = self.upper_csv_cc
        with open(fileinput2) as csvfile2:
            Curve2 = csv.reader(csvfile2, delimiter=",")
            for line in Curve2:
                x2 = np.append(x2, line[0])
                y2 = np.append(y2, line[1])
        with open(fileinput2) as csvfile2:    
            Curve2 = csv.reader(csvfile2, delimiter=",")
            c2 = [tuple(map(int, row)) for row in Curve2]

        xw = np.empty(0)
        yw = np.empty(0)
    
        density = float(fileinput[-12:-4])

        x1 = x1.astype(np.float64) #Creates a numpy array for the x coordinates
        y1 = y1.astype(np.float64) #Creates a numpy array for the y coordinates

        x2 = x2.astype(np.float64)
        y2 = y2.astype(np.float64)

        xw = xw.astype(np.float64)
        yw = yw.astype(np.float64)
     #Create the polynomials
        fit = poly.polyfit(x1, y1, 66) #Creates a polynomial fit of the 66th degree based on the data
        ffit = np.polyval(fit[::-1], x1) #Calculates the y values for the polynomial
        self.deriv = np.polyder(fit[::-1], 2) # Second Derivative of Polynomial Fit
        dfit = np.polyval(self.deriv, x1) #Calculates the y values for the second derivtave

        yccup = np.empty(0) #Empty y array for concave up
        xccup = np.empty(0) #Empty x array for concave up

        yccdown = np.empty(0) #Empty y array for concave down
        xccdown = np.empty(0) #Empty x array for concave down

        yvex = np.empty(0) #Empty y array for convex regions on original polynomial
        ycav = np.empty(0) #Empty y array for concave regions on original polynomial
     #Check concavity
        i = 70
        while i in range(len(dfit) - 400): #Iterates every point to see if it is a part of a concave or convex region
            val = dfit[i]
            if val < -0.0016 and val > -0.015: #Checks if second derivative values are within a filtered range
                yccup = np.append(yccup, dfit[i])
                xccup = np.append(xccup, x1[i])
                yvex = np.append(yvex, y1[i])
                i += 1
            elif val > 0.0016 and val < 0.015: #Checks if second derivative values are within a filtered range
                yccdown = np.append(yccdown, dfit[i])
                xccdown = np.append(xccdown, x1[i])
                ycav = np.append(ycav, y1[i])
                i += 1
            else:
                i += 1
     #Calculate shortest distance for convex
        i1 = 0
        vex = np.array([])
        cvex = []
        print()
        print("Calculating the convex regions please be patient...")
        for i1 in tqdm(range(len(xccup))): #Calculates the shortest distance for every point of the convex regions
            xvex = int(xccup[i1])
            ycvex = int(yvex[i1])
            cvex=[(xvex, ycvex)]
            upvex = [(x, y) for x, y in c2 if x in range(xvex - 250, xvex + 250)]
            vex = np.append(vex, distance.cdist(cvex, upvex).min(axis=1))
            i1 += 1
     #Calculate shortest distance for concave
        i1 = 0
        cave = np.array([])
        ccave = []
        print()
        print("Calculating the concave regions please be patient...")
        for i1 in tqdm(range(len(xccdown))): #Calculates the shortest distance for every point of the concave regions
            xcave = int(xccdown[i1])
            yccave = int(ycav[i1])
            ccave = [(xcave, yccave)]
            dcave = [(x, y) for x, y in c2 if x in range(xcave - 250, xcave + 250)]
            cave = np.append(cave, distance.cdist(ccave, dcave).min(axis=1))
            i1 += 1


        deepcave = np.divide(cave, density)
        deepvex = np.divide(vex, density)

        if len(deepcave) < len(deepvex):
            while len(deepcave) < len(deepvex):
                deepcave = np.append(deepcave, "Blank")
        if len(deepvex) < len(deepcave):
            while len(deepvex) < len(deepcave):
                deepvex = np.append(deepvex, "blank")

        vex = np.divide(vex, density) #Converts the convex values to a real world unit
        cave = np.divide(cave, density) #Converts the concave values to a real world unit
        if len(vex)>0:
            quartvex = percentile(vex, [25, 50, 75])
        else:
            quartvex = [0,0,0]
        if len(cave)>0:
            quartcave = percentile(cave, [25, 50, 75])
        else:
            quartcave = [0,0,0]
     #Save the data to the summary sheet
        current_dir = os.getcwd()
        worked_cc_dir = current_dir+"/Worked Concavity/"
        check_dir = Path(worked_cc_dir)
        fileinput = os.path.basename(self.lower_csv_cc)
        if check_dir.exists() is False:
            os.mkdir(worked_cc_dir)
        if len(os.listdir(worked_cc_dir)) == 0:
            first_line = np.array(["Location", "Ratio"," Concave Points", "Mean", "Median", "Q1", "Q3", "SD", "Convex Points", "Mean", "Median", "Q1", "Q3", "SD"])
            np.savetxt(current_dir+"/Concavity Calculator Summary.csv",first_line[None] ,fmt="%s", delimiter=",")
        with open(current_dir+"/Concavity Calculator Summary.csv", "a", newline="") as newFile:
            newFileWriter = csv.writer(newFile)
            newFileWriter.writerow([fileinput[:-19], str(density),str(len(cave)),str(round(np.mean(cave), 5)), str(round(quartcave[1], 5)), str(round(quartcave[0], 5)), str(round(quartcave[2], 5)), str(round(np.std(cave), 5)),str(len(vex)), str(round(np.mean(vex), 5)), str(round(quartvex[1], 5)), str(round(quartvex[0], 5)), str(round(quartvex[2], 5)), str(round(np.std(vex), 5))])


        fileinput = fileinput.replace(".csv", "")
        fileinput2 = os.path.basename(self.upper_csv_cc)
        fileinput2 = fileinput.replace(".csv", "")
        graphtitle = fileinput[:-19] + "-Concavity"

        np.savetxt((worked_cc_dir+graphtitle + ".csv"), list(zip(deepcave, deepvex)), fmt= "%s", delimiter=",", header="Concave, Convex")#Saves the Data as a CSV in root folder

     #The following plots the original, polynomial, second derivative, and concavities
        fig, ax = plt.subplots(2, sharex = True)
        fig.suptitle(graphtitle)
        ax[0].plot(x2, y2, c="m", label = "Lower")
        ax[1].set_xlabel("Pixels")
        ax[0].set_ylabel("Pixels")
        ax[1].set_ylabel("Pixels")
        ax[0].plot(x1, y1, c="k", label = "Upper")
        ax[0].plot(x1, ffit, c="g", label = "Fit")
        if len(xccup) > 0:
            ax[0].scatter(xccup, yvex, c="b", label="Convex")
        if len(xccdown) > 0:
            ax[0].scatter(xccdown, ycav, c="r", label = "Concave")
        if len(xw) > 0:
            ax[0].scatter(xw, yw, c="y", label = "Wedge")
        ax[1].plot(x1, dfit, c="g", label = "Fit second derivative")
        if len(xccup) > 0:
            ax[1].scatter(xccup, yccup, c="b", label = "CC Up")
        if len(xccdown) > 0:
            ax[1].scatter(xccdown, yccdown, c="r", label = "CC Down")
        ax[0].legend()
        ax[1].legend()
        ax[0].grid(True)
        ax[1].grid(True)
        self.cc_figure = fig
     #The following plots the boxplots
        fig2, ax2 = plt.subplots(nrows=1, ncols = 1, sharex=False, sharey=True)
        fig2.suptitle(graphtitle)
        ax2.set_ylabel("Shortest Distances (μm)")
        ax2.set_xticklabels(["Concave", "Convex"])
        if len(cave) >0 and len(vex) >0:
            ax2.boxplot([cave, vex])
        elif len(cave)> 0 and len(vex) ==0:
            ax2.boxplot(cave)
        elif len(cave) == 0 and len(vex) > 0:
            ax2.boxplot(vex)
        else:
            plt.close("fig2")
        ax2.grid(True)
        curvepath = worked_cc_dir + graphtitle + "-Curves.png"
        boxpath = worked_cc_dir + graphtitle + "-Boxplot.png"
        fig.savefig(curvepath)
        fig2.savefig(boxpath)
     #Contour Checking Button
        if "cc_contour_check_btn" not in dir(self):
            self.cc_contour_check_btn = Button(self.cc_menu, text="Check Images / Wedge Analysis", bg="medium spring green", font=font1, command = lambda: [self.cc_menu.withdraw(), self.cc_contour_check()])
            self.cc_contour_check_btn.grid(row = 3, column = 0)
            self.cc_contour_check_status = Label(self.cc_menu, text="Allows you to find the concavities at specific points", font=font2)
            self.cc_contour_check_status.grid(row=3, column =1)
        self.cc_calc_btn.destroy()
        del self.cc_calc_btn
        self.cc_csv_status.configure(text="The data has been saved in Concavity Calculator Summary.csv")
        self.cc_csv_status.update()

    def cc_contour_check(self): ##Creates an additional menu to manual check concavities at certain points on the data
        self.cc_contour_menu = Toplevel()
        self.cc_contour_menu.title("Concavity Magnitude Calculator")
        self.cc_contour_menu.configure(bg="gray69")
        if "mag_status" in dir(self):
            del self.mag_status
        Label(self.cc_contour_menu, text="This page will let you check the concavity at specified points", font=font2).grid(row=0, columnspan =3)
        cc_canvas = FigureCanvasTkAgg(self.cc_figure, master =self.cc_contour_menu)
        cc_canvas.draw()
        cc_canvas.get_tk_widget().grid(row =1, columnspan = 2)
        Label(self.cc_contour_menu, text="Enter the x coordinate displayed while hovering over the upper boundary", font=font2).grid(row=3, column=0, sticky="E")
        cc_toolbar_frame = Frame(master=self.cc_contour_menu)
        cc_toolbar_frame.grid(row = 2, columnspan = 2)
        cc_toolbar = NavigationToolbar2Tk(cc_canvas, cc_toolbar_frame)
        contour_location = Entry(self.cc_contour_menu, font=font2)
        contour_location.insert(END, "200")
        contour_location.grid(row =3, column = 1, sticky="W")
        
        contour_calculate_btn = Button(self.cc_contour_menu, text="Calculate Magnitude", bg="thistle", font=("Helvetica", 18), command = lambda: self.mag_calc(int(contour_location.get())))
        contour_calculate_btn.grid(row=4, column =1)

        cc_menu_return = Button(self.cc_contour_menu, text="Close and continue", font=("Helvetica", 18), bg="tomato", command=lambda: [(self.cc_contour_menu.destroy(), self.cc_menu.deiconify())])
        cc_menu_return.grid(row=5, column =1)
    
    def mag_calc(self, location): ##Performs the calculations to find out the concavity at selected position
        mag2d = np.polyval(self.deriv, location)
        mag2d = np.format_float_scientific(mag2d, precision = 7)
        if "mag_status" not in dir(self):
            self.mag_status = Label(self.cc_contour_menu, text=("At location x=" + str(location) +" there is a magnitude of: "+str(mag2d)), font=font2)
            self.mag_status.grid(row=4, column = 0)
        else:
            self.mag_status.configure(text=("At location x=" + str(location) +" there is a magnitude of: "+str(mag2d)))
            self.mag_status.update()

def closest_node(node, nodes): #Finds the index in a tuple of tuples closest to a given tuple
    nodes = np.asarray(nodes)
    deltas = nodes - node
    dist_2 = np.einsum("ij,ij->i", deltas, deltas)
    return np.argmin(dist_2)

def resize(Original, sizepercentage): ##Resizes an opencv image array
    width = int(Original.shape[1] * sizepercentage / 100)
    height = int(Original.shape[0] * sizepercentage / 100)
    dsize = (width, height)
    return cv2.resize(Original, dsize)

def round_to_1(x): ##Rounds the input number to one significant figure
    return round(x, -int(floor(log10(abs(x)))))

def scale_reader(path): ##Uses  pyOCR to read the text on TESCAN SEM images to create the pixel/micorn ratio of the image
    img = cv2.imread(path, 0)
    height = img.shape[0]
    width = img.shape[1]
    dim_ratio = width / height

    if (dim_ratio < 0.9 and dim_ratio > 0.85): #Following block is default TESCAN format
        img = img[int((height*0.89)):int((height*0.96)), (int(width*0.48)):(int(width*0.82))]
        height_text = img.shape[0]
        img_text = img[int(height*.042):int(height_text), 0:width]
        img_scale = img[0:int(height_text*.6),0:width]
    elif dim_ratio > 1.6:
        img = img[int((height*0.81)):int((height*0.96)), (int(width*0.48)):(int(width*0.82))]
        height_text = img.shape[0]
        img_text = img[int(height*.042):int(height_text), 0:width]
        img_scale = img[0:int(height_text*.55),0:width]
    elif (dim_ratio > 1.2 and dim_ratio < 1.6):
        img = img[int((height*0.71)):int((height*0.85)), (int(width*0.48)):(int(width*0.82))]
        height_text = img.shape[0]
        img_text = img[int(height*.07):int(height_text), 0:width]
        img_scale = img[0:int(height_text*.55),0:width]
    elif (dim_ratio <.85):
        img = img[int((height*0.83)):int((height*0.9)), (int(width*0.48)):(int(width*0.82))]
        height_text = img.shape[0]
        img_text = img[int(height*.035):int(height_text), 0:width]
        img_scale = img[0:int(height_text*.6),0:width]
    elif (dim_ratio < 1.2) and (dim_ratio >1.1):
        img = img[int((height*0.8)):int((height*0.96)), (int(width*0.48)):(int(width*0.82))]
        height_text = img.shape[0]
        img_text = img[int(height*.11):int(height_text), 0:width]
        img_scale = img[0:int(height_text*.75),0:width]
    else:
        img = img[int((height*0.78)):int((height*0.9)), (int(width*0.48)):(int(width*0.82))]
        height_text = img.shape[0]
        img_text = img[int(height*.045):int(height_text), 0:width]
        img_scale = img[0:int(height_text*.55),0:width]

    
    img = cv2.inRange(img, 250, 255)
    if width < 4100:
        img_text = resize(img_text, 300) #Helps with smaller images
    elif width < 5000:
        img_text = resize(img_text, 150)
    img_text = cv2.inRange(img_text, 250, 255) #Filters
    img_text = cv2.GaussianBlur(img_text, (3,3), 0) #Helps with Smaller Images
    img_scale = cv2.inRange(img_scale, 250, 255)
    custom_config = "--psm 6 outputbase nobatch digits"
    
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        return "No_tool", 1, 1
    tool = tools[0]
    langs = tool.get_available_languages()
    lang = langs[0]
    test_img = im.fromarray(img_text)
    text = tool.image_to_string(test_img, lang = lang, builder = pyocr.builders.TextBuilder())
    distance = ""

    try:
        text = [int(i) for i in text.split() if i.isdigit()]
        text = str(text[0])
        if text != "" and " " not in text and "\\x0c" not in text:
            text = int(text)
            cnts = cv2.findContours(img_scale, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            cnts = imutils.grab_contours(cnts)
            if len(cnts) > 0:
                c = max(cnts, key=cv2.contourArea)
                leftmost = tuple(c[c[:,:,0].argmin()][0])
                rightmost = tuple(c[c[:,:,0].argmax()][0])
                distance = int(rightmost[0])-int(leftmost[0]) - 1
                ratio = float(distance / text)
            else:
                ratio = "Error"
        else:
            ratio = "Error"
    except:
        ratio = "Error"
    return ratio, text, distance

def shortest_distance_calc(lower_csv, upper_csv, ratio,current_dir, save_folder_path, scale_ratio, calculation_count, alternative_status): ##Calculates the absolute shortest distance between points along the lower boundary and upper boundary csvs
 #Loads the csvs   
    reader = csv.reader(open(lower_csv, encoding="ansi")) #Loads the csvs
    with open(lower_csv) as csvfile:
        c1 = [tuple(map(int, row)) for row in csv.reader(csvfile)]
    reader = csv.reader(open(upper_csv, encoding ="ansi"))
    with open(upper_csv) as csvfile2:
        c2 = [tuple(map(int, row)) for row in csv.reader(csvfile2)]
    with open(upper_csv) as csvfile2:
        Curve2 = csv.reader(csvfile2, delimiter=",")
        c2check = np.empty(0)
        for line in Curve2:
            c2check = np.append(c2check, line[0])
    
    c2check = c2check.astype(np.float64)
    density = ratio
    d = np.array([])
    dx = np.array([])
    cparray = []
    print("\nCalculating the shortest distance. Please be patient...")
    
    y_1_u = None
    y_1_l = c1[5][1]
    for i in range((len(c2)-1),0,-1):
        if c2[i][0] == c1[5][0]:
            y_1_u = c2[i][1]
            break
    if y_1_u == None:
        y_1_u = c2[0][0]

    y_2_u = None
    y_2_l = c1[-5][1]
    for i in range((len(c2)-1),0,-1):
        if c2[i][0] == c1[-5][0]:
            y_2_u = c2[i][1]
            break
    if y_2_u == None:
        y_2_u = c2[-5][0]

    
    y_1_dif = abs(y_1_l-y_1_u)
    y_2_dif = abs(y_2_l-y_2_u)
    if y_1_dif < y_2_dif:
        vertical_check = y_2_dif
    else:
        vertical_check = y_1_dif

    if alternative_status == 2: #Vertical check only, makes calculations check for same x value
        vertical_check = 0

    work_width = (len(c1)-(int(vertical_check*3)))
    if calculation_count == 500:
        step_size = int(round(work_width/500))
        
    else:
        step_size = int(round(work_width/calculation_count))
    if step_size == 0:
        step_size = 1

 #Calculate shortest distance   
    cparray_saved= np.array([])
    cdist_saved = np.array([])
    for i1 in tqdm(range(int(vertical_check*1.5), len(c1) - int(vertical_check*1.5), step_size)):
        numb = 0
        cparray = []
        try:
            numb = c1[i1]
        except:
            continue
        if numb != 0:
            tupx = (numb[0])
            tupy = (numb[1])
            tupcheck = list(range(int(tupx- vertical_check*.7), int(tupx + 1 + vertical_check*.7)))
            for i in range(len(tupcheck)):
                if tupcheck[i] in c2check:
                    cparray = [(tupx,tupy)]
                    break
        if len(cparray) != 0:
            c2edit = [(x, y) for x, y in c2 if x in range(int(tupx - (vertical_check*1.25)), int(tupx + 1 + (vertical_check*1.25)))]
            list_of_differences = distance.cdist(cparray, c2edit, "euclidean")
            min_val = list_of_differences.min(1)
            index_of_shortest = np.where(list_of_differences == min_val)
            d = np.append(d, distance.cdist(cparray,c2edit).min(axis=1))
            cparray_saved = np.append(cparray_saved, (cparray))
            if len(index_of_shortest) > 1:
                if len(index_of_shortest[1]) == 1:
                    cdist_saved = np.append(cdist_saved, (c2edit[int(index_of_shortest[1])]))
                else:
                    cdist_saved = np.append(cdist_saved, (c2edit[int(index_of_shortest[1][0])]))
            else:
                cdist_saved = np.append(cdist_saved, (c2edit[int(index_of_shortest[0])]))
            dx = np.append(dx, tupx)

 #Calculate trapezoidal
    x1 = [c[0] for c in c1]
    y1 = [c[1] for c in c1]
    ta1 = np.trapz(y1, x=x1)

    x2 = [c[0] for c in c2]
    y2 = [c[1] for c in c2]
    ta2 = np.trapz(y2, x=x2)

    abc = ta2-ta1
    Tabc = (abc/(density**2))
    cl1 = len(c1) / density
    cl2 = len(c2) / density
    clavg = (cl1+cl2)/2
 #The following creates a polygon using the data points and calculates the area of the polygon
    polygon_points = [] #Creates a list to be used to make a polygon
    for xyvalue in c1: #Adds curve 1
        polygon_points.append([xyvalue[0], xyvalue[1]])
    for xyvalue in c2[::-1]: #adds curve 2
        polygon_points.append([xyvalue[0], xyvalue[1]])
    for xyvalue in c1[0:1]: #adds the first points of curve 1 to close the polygon
        polygon_points.append([xyvalue[0],xyvalue[1]])
    PArea = Polygon(polygon_points)
    area = PArea.area
    Tarea = area / density**2 #Changes the area of the polygon to units^2
        
    d = np.divide(d, density)
    quartile = percentile(d, [25, 75])
 #Creates the boxplot
    fig = plt.figure(1, figsize=(9,6))
    ax = fig.add_subplot(111)
    bp = ax.boxplot(d)
    fileinput = os.path.basename(lower_csv)
    curveinput = os.path.basename(upper_csv)
    ax.set_ylabel("µm")
    title = fileinput[:-19]
    ax.set_title(title)
    ax.set_xlabel("")
    ax.yaxis.set_major_locator(plt.MaxNLocator(15))
 #Saves the boxplot   
    if alternative_status == 0:
        picturename = fileinput[:-19] + "-Boxplot"+str(calculation_count)+".png"   
    elif alternative_status == 1:  
        picturename = fileinput[:-19] +"-ReverseBoxplot"+str(calculation_count)+".png"
    elif alternative_status == 2:
        picturename = fileinput[:-19] +"-VerticalBoxplot"+str(calculation_count)+".png"
    fig.savefig(save_folder_path + picturename)
    plt.close()
    if alternative_status == 0:
        np.savetxt((save_folder_path+ title + "-Distances.csv"), list(zip(d,dx)), fmt= "%s", delimiter=",", header="Shortest Distances, horizontal pixel location")
    elif alternative_status == 1:
        np.savetxt((save_folder_path+ title + "-ReverseDistances.csv"), list(zip(d,dx)), fmt= "%s", delimiter=",", header="Shortest Distances, horizontal pixel location")
    elif alternative_status == 2:
        np.savetxt((save_folder_path+ title + "-VerticalDistances.csv"), list(zip(d,dx)), fmt= "%s", delimiter=",", header="Vertical Distances, horizontal pixel location")
 #Optional Lines
    trace_picture = cv2.imread(lower_csv[:-19]+".png",1)
    for i in range(0,len(cparray_saved), 2):
        trace_picture = cv2.line(trace_picture, (int(cparray_saved[i]), int(cparray_saved[i+1])), (int(cdist_saved[i]), int(cdist_saved[i+1])), (0,255,255), thickness=1)
    if alternative_status == 0:
        picturename2 = fileinput[:-19] + "-Lines"+str(calculation_count)+".png"
    elif alternative_status == 1:
        picturename2 = fileinput[:-19] + "-ReverseLines"+str(calculation_count)+".png"
    elif alternative_status == 2:
        picturename2 = fileinput[:-19] + "-VerticalLines"+str(calculation_count)+".png"
        
    cv2.imwrite((save_folder_path + picturename2), trace_picture)
 #Saves Surface Roughness
    c1_x = np.array([])
    c1_y = np.array([])
    for i in range(len(c1)):
        if c1[i][0] in c1_x:
            pass
        else:
            c1_x = np.append(c1_x, c1[i][0])
            c1_y = np.append(c1_y, c1[i][1])

    slope, y_intercept = np.polyfit(c1_x, c1_y, 1) #Makes line for bulk/oxide boundary

    distance_list = np.array([])
    for i in range(len(c1_x)):
        point_x = c1_x[i]
        point_y = c1_y[i]
        distance1 = np.absolute(((slope*-1*point_x)+(point_y)-y_intercept)/(np.sqrt(1+slope**2)))
        distance_list = np.append(distance_list, distance1)
    Ra_metal = np.sum(distance_list)/len(c1_x)
    std_metal = np.std(distance_list)

    c2_x = np.array([])
    c2_y = np.array([])
    for i in range(len(c2)):
        if c2[i][0] in c2_x:
            pass
        else:
            c2_x = np.append(c2_x, c2[i][0])
            c2_y = np.append(c2_y, c2[i][1])

    slope_2, y_intercept_2 = np.polyfit(c2_x, c2_y, 1) #Makes line for oxide/mount boundary

    distance_list2 = np.array([])
    for i in range(len(c2_x)):
        point_x = c2_x[i]
        point_y = c2_y[i]
        distance2 = np.absolute(((slope_2*-1*point_x)+(point_y)-y_intercept_2)/(np.sqrt(1+slope_2**2)))
        distance_list2 = np.append(distance_list2, distance2)
    Ra_oxide = np.sum(distance_list2)/len(c2_x)
    std_oxide = np.std(distance_list2)
    
    if alternative_status == 1:
        column1 = ["Ra Oxide-mount interface", "STD Oxide-mount interface", "Ra Metal-oxide interface","STD Metal-oxide interface"]
        column2 = [Ra_oxide/ratio, std_oxide, Ra_metal/ratio, std_metal,]
        np.savetxt((save_folder_path+ title + "-ReverseSurface Roughness"+str(calculation_count)+".csv"), list(zip(column1,column2)), fmt= "%s", delimiter=",", header="Roughness Location, Roughness Value (um)")
    else:
        column1 = ["Ra Metal-oxide interface","STD Metal-oxide interface", "Ra Oxide-mount interface", "STD Oxide-mount interface"]
        column2 = [Ra_metal/ratio, std_metal, Ra_oxide/ratio, std_oxide]
        np.savetxt((save_folder_path+ title + "-Surface Roughness"+str(calculation_count)+".csv"), list(zip(column1,column2)), fmt= "%s", delimiter=",", header="Roughness Location, Roughness Value (um)")  
 #Saves the data   
    csv_summary_location = current_dir+"/SOFIA External Summary.csv"
    if Path(csv_summary_location).is_file() is False: #Creates a summary csv if none exists and appends the new data
        file_start = np.array(["Image/Thresholds", "Pixel Ratio", "Mean", "Median", "Q1", "Q3", "SD", "Trapezoidal", "Polygon", "Calculation Count"])
        np.savetxt(current_dir+"/SOFIA External Summary.csv",file_start[None], fmt="%s", delimiter =",")
    with open(current_dir+"/SOFIA External Summary.csv", "a", newline="") as newFile:
        newFileWriter = csv.writer(newFile)
        if alternative_status == 0:
            newFileWriter.writerow([fileinput[:-19],str(density), str(round(np.mean(d), 5)), str(round(np.median(d), 5)), str(round(quartile[0], 5)), str(round(quartile[1], 5)),
            str(round(np.std(d), 5)), str(round(Tabc/clavg, 5)), str(round(Tarea / clavg, 5)), str(len(d))])
        elif alternative_status == 1:
            newFileWriter.writerow([fileinput[:-19]+"-Reverse", str(density), str(round(np.mean(d), 5)), str(round(np.median(d), 5)), str(round(quartile[0], 5)), str(round(quartile[1], 5)),
            str(round(np.std(d), 5)), str(round(Tabc/clavg, 5)), str(round(Tarea / clavg, 5)), str(len(d))])
        else:
            newFileWriter.writerow([fileinput[:-19]+"-Vertical", str(density), str(round(np.mean(d), 5)), str(round(np.median(d), 5)), str(round(quartile[0], 5)), str(round(quartile[1], 5)),
            str(round(np.std(d), 5)), str(round(Tabc/clavg, 5)), str(round(Tarea / clavg, 5)), str(len(d))])

root = Tk()
start = MainWindow(root)
root.mainloop()
