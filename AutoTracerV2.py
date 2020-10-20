from tkinter import *
import numpy as np
from numpy import percentile
import os, imutils, pytesseract, cv2, csv, shutil
from PIL import Image, ImageTk
from tkinter import filedialog
import os.path
from pathlib import Path
from scipy.spatial import distance
from tqdm import tqdm
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from math import log10, floor, pi
import numpy.polynomial.polynomial as poly

#Allows the user to load an image and quickly crop, threshold, and detect edges to isolate lines for the purpose
#of measuring scale thicknesses for internal and external oxidation.
#Created by Padraig Stack
#Last modified September 14, 2020

pytesseract.pytesseract.tesseract_cmd = "C:\Program Files\Tesseract-OCR\\tesseract.exe" ##Location of the text reading software

path = cbtn = directory = filename = orig_img = crop_menu = None
lower_crop = upper_crop = cropping_image = crop_close = thresh_image = thresh_btn = crop = None
thresh_menu = lower_thresh = upper_thresh = thresh_panel_new = thresh_panel_old = lower_thresh_old = upper_thresh_old = None
thresh_img_old = thresh_close_btn = edge_btn = contour_iterations = edge_menu = contour_menu = None
contour_input= lower_list = upper_list = csvlx = csvux = csvly = csvuy = tracing_img = tracing_image = contour_close_btn = None
save_csv_btn = edge_close_btn = short_dist_btn = undo_btn = list_label = crop_status = thresh_status = contour_status = calculate_status = None
cc_calc_btn = cc_contour_check_btn = mag_status = int_calc_btn = None

class imported_image:
    def __init__(self, orig_img, in_or_ex):
        width = orig_img.shape[1]
        ratio = width // 1000
        if ratio == 0: #Prevents divide by zero errors
            ratio = int(1)
        self.ratio = ratio
        if in_or_ex == "ex":
            self.in_or_ex = 1
        else:
            self.in_or_ex = 0
        self.values()
    
    def values(self, pct = 2): #Recallable dynamic resolution function
        monitor_width = root.winfo_screenwidth()
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
                self.fullsize = int((75/self.ratio)*modifier)
                self.crop_resize = int((135/self.ratio)*modifier)
                self.croped_resize = int((165/self.ratio)*modifier)
                self.contour_resize = int((140/self.ratio)*modifier)
                self.thresh_width = int((165*self.ratio))
            elif monitor_width < 1920:
                self.fullsize = int((50/self.ratio)*modifier)
                self.crop_resize = int((90/self.ratio)*modifier)
                self.croped_resize = int((110/self.ratio)*modifier)
                self.contour_resize = int((80/self.ratio)*modifier)
                self.thresh_width = int(110*self.ratio)
            else:
                self.fullsize = int((100/self.ratio)*modifier)
                self.crop_resize = int((180/self.ratio)*modifier)
                self.croped_resize = int((220/self.ratio)*modifier)
                self.contour_resize = int((160/self.ratio)*modifier)
                self.thresh_width = int(220*self.ratio)
            self.vertical_check = int(4*self.ratio)
            self.edge_limit = int(25*self.ratio)
        else:
            if monitor_width >= 1920 and monitor_width < 2560: #Adjusts the image sizes based off monitor resolution  width (assumed 16:9)
                self.fullsize = int((70/self.ratio)*modifier)
                self.crop_resize = int((150/self.ratio)*modifier)
                self.croped_resize = int((150/self.ratio)*modifier)
                self.contour_resize = int((105/self.ratio)*modifier)
                self.thresh_width = int(150*self.ratio)
            elif monitor_width < 1920:
                self.fullsize = int((45/self.ratio)*modifier)
                self.crop_resize = int((100/self.ratio)*modifier)
                self.croped_resize = int((100/self.ratio)*modifier)
                self.contour_resize = int((70/self.ratio)*modifier)
                self.thresh_width = int(100*self.ratio)
            else:
                self.fullsize = int((90/self.ratio)*modifier)
                self.crop_resize = int((160/self.ratio)*modifier)
                self.croped_resize = int((200/self.ratio)*modifier)
                self.contour_resize = int((140/self.ratio)*modifier)
                self.thresh_width = int(200*self.ratio)
            self.vertical_check = int(2*self.ratio)
            self.edge_limit = int(3*self.ratio)

        self.center_circle = int(self.ratio)
        self.label_text = int((self.ratio//2)+1)
        self.scale_bar = int(round_to_1(orig_img.shape[1])/10)
        self.image_area = orig_img.shape[1] * orig_img.shape[0]
        self.area_thresh = int(self.image_area * .00004)
        self.contour_buffer = int(self.ratio*3.125)

       

def resize(Original, sizepercentage): ##Resizes an opencv image array
    width = int(Original.shape[1] * sizepercentage / 100)
    height = int(Original.shape[0] * sizepercentage / 100)
    dsize = (width, height)
    return cv2.resize(Original, dsize)

def round_to_1(x):
    return round(x, -int(floor(log10(abs(x)))))

def select_image(in_or_ex = "ex"): ##Allows the user to select an image from their computer to use in future steps
    global path, cbtn, directory, filename, orig_img, img_class
    path = filedialog.askopenfilename()
    if len(path) > 0:
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        orig_img = cv2.imread(path, 0)
        img_class = imported_image(orig_img, in_or_ex)
        status_path.configure(text=("The current loaded image is: " + filename), font=("Helvetica", 12))
        status_path.update()
        if cbtn is None:
            cbtn = Button(root, text="Crop the image", bg="PaleTurquoise1",  font=("Helvetica", 14), command = crop_image)
            cbtn.grid(row = 1, column = 0)
    else:
        status_path.configure(text="You have not selected a new image, please select one", font=("Helvetica", 12))
        status_path.update()

def crop_image(): ##Creates a menu to crop the image 
    global crop_menu, lower_crop, upper_crop, cropping_image, crop_close
    if crop_menu is not None:
        crop_menu.destroy()
    crop_close = None
    crop_menu = Toplevel()
    crop_menu.title=("Cropping Menu")
    crop_menu.configure(bg="gray69")
    crop_menu.minsize(300,300)

    Label(crop_menu, text=("The image you have loaded is "  +str(orig_img.shape[0]) +" pixels tall"
    "\nAdjust the parameters until the entire scale is in the frame"), bg="thistle1", font=("Helvetica", 12)).grid(row = 0, columnspan = 2)

    orig_scale = orig_img.copy() #Creates a scale on the side of the image to help with cropping
    height = int(orig_img.shape[0])
    for i in range(height//img_class.scale_bar):
        cv2.putText(orig_scale, str(i*img_class.scale_bar), (0, (height-(i*img_class.scale_bar))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.label_text+2), (255,255,255),(img_class.center_circle+3))
        cv2.putText(orig_scale, "____", (0, (height-(i*img_class.scale_bar))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.label_text+2), (255,255,255),(img_class.center_circle))
    
    
    orig_resize = resize(orig_scale, img_class.fullsize) #Prepares and adds an image to the GUI
    orig_resize = ImageTk.PhotoImage(Image.fromarray(orig_resize))
    cropping_image = Label(crop_menu, text = "Cropping Image", image = orig_resize)
    cropping_image.image = orig_resize
    cropping_image.grid(row = 1, columnspan = 2)

    Label(crop_menu, text="Lower Height", font= ("Helvetica", 12)).grid(row = 2, column = 0, sticky = "E") #Entry for lower height
    lower_crop = Entry(crop_menu, font= ("Helvetica", 12))
    lower_crop.insert(END, "0")
    lower_crop.grid(row = 2, column = 1, sticky = "W")

    Label(crop_menu, text="Upper Height", font= ("Helvetica", 12)).grid(row = 3, column = 0, sticky = "E") #Entry for upper height
    upper_crop = Entry(crop_menu, font= ("Helvetica", 12))
    upper_crop.insert(END, str(orig_img.shape[0]))
    upper_crop.grid(row = 3, column = 1, sticky = "W")

    crop_update_btn = Button(crop_menu, text="Update Crop", font= ("Helvetica", 12), bg="gold2", command = crop_update) #Update crop button
    crop_update_btn.grid(row = 4, columnspan = 2)

def crop_update(): ##Checks the values in the entries and updates the image accordingly
    global cropping_image, crop_close, thresh_image, thresh_btn, crop, crop_status, lower_crop_val, upper_crop_val
    lower_crop_val = int(float(orig_img.shape[0])-float(lower_crop.get()))
    upper_crop_val = int(float(orig_img.shape[0])-float(upper_crop.get()))

    crop = orig_img.copy()
    height = int(orig_img.shape[0])
    for i in range(height//img_class.scale_bar):
        cv2.putText(crop, str(i*img_class.scale_bar), (0, (height-(i*img_class.scale_bar))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.label_text+2), (255,255,255),(img_class.center_circle+2))
        cv2.putText(crop, "____", (0, (height-(i*img_class.scale_bar))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.label_text+2), (255,255,255),(img_class.center_circle))
    crop = crop[upper_crop_val:lower_crop_val, 0:orig_img.shape[1]]
    
    crop_pct = (lower_crop_val - upper_crop_val)/ height
    img_class.values(crop_pct) #Recalculates dynamic resolution if necessary

    
    crop_resize = resize(crop, img_class.crop_resize)
    crop_resize = ImageTk.PhotoImage(Image.fromarray(crop_resize))
    crop = orig_img[upper_crop_val:lower_crop_val, 0:orig_img.shape[1]]

    cropping_image.configure(image=crop_resize)
    cropping_image.image = crop_resize

    if crop_close is None:
        crop_close = Button(crop_menu, text = "Close and Continue", bg = "tomato", font= ("Helvetica", 12), command = crop_menu.destroy)
        crop_close.grid(row = 5, columnspan = 2)
    
    if thresh_btn is None:
        thresh_btn = Button(root, text="Adjust Thresholds", font = ("Helvetica", 14), bg="DeepSkyBlue2", command = thresh_image)
        thresh_btn.grid(row = 2, column = 0)
    
    if crop_status is None:
        crop_status = Label(root, text = "Crop has been updated", font = ("Helvetica", 14))
        crop_status.grid(row = 1, column = 1, sticky = "W")

    

def thresh_image(): ##Creates a menu to adjust the thresholds on the image
    global thresh_menu, lower_thresh, upper_thresh, thresh_panel_new, contour_iterations, thresh_panel_old, thresh_close_btn
    if thresh_menu is not None:
        thresh_menu.destroy()
    thresh_panel_new = thresh_panel_old = thresh_close_btn = lower_thresh_old = upper_thresh_old = None

    contour_iterations = []
    thresh_menu = Toplevel()
    thresh_menu.title("Threshold Menu")
    thresh_menu.configure(bg="gray69") 
    Label(thresh_menu, text="Adjust the parameters until the desired section of the image is white\nThe following is a slice of the original image", font= ("Helvetica", 14)).grid(row = 0, columnspan = 3)
    
    adj_crop_img = crop[0:crop.shape[0],0:img_class.thresh_width] #Takes a slice of the cropped image to use as a reference window
    adj_crop_img = resize(adj_crop_img, img_class.croped_resize)
    adj_crop_img = ImageTk.PhotoImage(Image.fromarray(adj_crop_img))
    adj_crop_image = Label(thresh_menu, text="Cropped Original", image = adj_crop_img)
    adj_crop_image.image = adj_crop_img
    adj_crop_image.grid(row=1, column=0)

    Label(thresh_menu, text="Please enter the lower threshold value (0-255)", font= ("Helvetica", 12)).grid(row = 3, column = 0, sticky = "E") #Entry to adjust lower threshold
    lower_thresh = Entry(thresh_menu, font= ("Helvetica", 12))
    lower_thresh.insert(END, "60")
    lower_thresh.grid(row = 3, column = 1, sticky = "W")

    Label(thresh_menu, text = "Please enter the higher threshold value (0-255)", font= ("Helvetica", 12)).grid(row=4, column = 0, sticky = "E") #Entry to adjust upper threshold
    upper_thresh = Entry(thresh_menu, font= ("Helvetica", 12))
    upper_thresh.insert(END, "195")
    upper_thresh.grid(row = 4, column = 1, sticky = "W")

    thresh_update_btn = Button(thresh_menu, text="Update Threshold", bg="OliveDrab1", font= ("Helvetica", 12), command=thresh_update)
    thresh_update_btn.grid(row=5,column=1, sticky="W")
    
    grayscale_img = ImageTk.PhotoImage(Image.open("Grayscale.jpg"))
    grayscale_image = Label(thresh_menu, text="Grayscale Values", image=grayscale_img)
    grayscale_image.image = grayscale_img
    grayscale_image.grid(row = 8, columnspan = 3)


def thresh_update(): ##Checks the values in the entries and updates the threhsold images
    global thresh_panel_new, lower_thresh_old, upper_thresh_old, thresh_panel_old, thresh_img_old, thresh_close_btn, edge_btn
    lower_thresh_val = int(lower_thresh.get())
    upper_thresh_val = int(upper_thresh.get())

    thresh_img = cv2.inRange(crop, lower_thresh_val, upper_thresh_val)
    thresh_img_crop = thresh_img[0:thresh_img.shape[0], 0:img_class.thresh_width]
    thresh_img_crop = resize(thresh_img_crop,img_class.croped_resize)
    thresh_img_crop = ImageTk.PhotoImage(Image.fromarray(thresh_img_crop))

    if thresh_panel_new is None: #Adds or updates an image to the threshold menu 
        thresh_panel_new = Label(thresh_menu, text="New Threshold", image = thresh_img_crop)
        thresh_panel_new.image = thresh_img_crop
        thresh_panel_new.grid(row=1, column = 1)
        Label(thresh_menu, text="Most recent image\n("+str(lower_thresh_val)+"-"+str(upper_thresh_val)+")", font= ("Helvetica", 12)).grid(row=2,column=1)
    else:
        thresh_panel_new.configure(image=thresh_img_crop)
        thresh_panel_new.image=thresh_img_crop
        Label(thresh_menu, text="Most recent image\n("+str(lower_thresh_val)+"-"+str(upper_thresh_val)+")", font= ("Helvetica", 12)).grid(row=2,column=1)
    
    if lower_thresh_old is not None: #Adds or updates the previous iamge to the threshold menu
        if thresh_panel_old is None:
            thresh_panel_old = Label(thresh_menu, text="New Threshold", image = thresh_img_old)
            thresh_panel_old.image = thresh_img_old
            thresh_panel_old.grid(row=1, column = 2)
            Label(thresh_menu, text="Previous Threshold\n("+str(lower_thresh_old)+"-"+str(upper_thresh_old)+")",font= ("Helvetica", 12)).grid(row=2,column=2)
        else:
            thresh_panel_old.configure(image=thresh_img_old)
            thresh_panel_old.image=thresh_img_old
            Label(thresh_menu, text="Previous Threshold\n("+str(lower_thresh_old)+"-"+str(upper_thresh_old)+")",font= ("Helvetica", 12)).grid(row=2,column=2)

    lower_thresh_old = lower_thresh_val
    upper_thresh_old = upper_thresh_val
    thresh_img_old = thresh_img_crop

    if thresh_close_btn is None: #Creates a close button
        thresh_close_btn = Button(thresh_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=thresh_menu.destroy)
        thresh_close_btn.grid(row=7, column=1, sticky="W")

        thresh_add_btn = Button(thresh_menu, text="Add Most Recent Threshold", font= ("Helvetica", 12), command = thresh_add)
        thresh_add_btn.grid(row=6, column = 1, sticky="W")


    if edge_btn is None: #Creates a button for the next menu
        edge_btn = Button(root, text="Select Edges", font = ("Helvetica", 14), bg="MediumOrchid2", command=edge_select)
        edge_btn.grid(row = 3, column = 0)

def thresh_add(): ##Appends a list of thresholds for contour selection
    global contour_iterations, thresh_status
    contour_set = [lower_thresh_old, upper_thresh_old]
    if contour_set not in contour_iterations:
        contour_iterations.append(contour_set)
    if thresh_status is None:
        thresh_status = Label(root, text="You have selected "+str(len(contour_iterations))+" different thresholds", font= ("Helvetica", 12))
        thresh_status.grid(row=2, column = 1, sticky="W")
    else:
        thresh_status.configure(text="You have selected "+str(len(contour_iterations))+" different thresholds", font= ("Helvetica", 12))
        thresh_status.update()

def label_center(threshedimage): ##Finds the coordinates for the first data point in all of the contours and if the area of the contour is above a certain size it will label the contour
    threshedimage = cv2.copyMakeBorder(threshedimage, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
    threshedimage = cv2.medianBlur(threshedimage, 5)
    threshedimage = cv2.copyMakeBorder(threshedimage, 5,5,5,5, cv2.BORDER_CONSTANT, value=0)
    cnts, _ = cv2.findContours(threshedimage, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    threshedimage = cv2.cvtColor(threshedimage, cv2.COLOR_GRAY2BGR)
    step = 0
    area_list = []
    area_number = []
    for cnt in cnts:
        cx = cnt[0][0][0]
        cy = cnt[0][0][1]
        area = cv2.contourArea(cnt)
        b, _, _ = (threshedimage[(cy-1),(cx)])
        if b < 255:
            area_list.append(area)
            area_number.append(step)
            if area > img_class.area_thresh:
                cv2.circle(threshedimage, (cx, cy), img_class.center_circle, (255, 0, 0), -1)
                if cx < (3*(threshedimage.shape[1])/4):
                    if cy < ((threshedimage.shape[0])/4):
                        cv2.putText(threshedimage, (str(step)), (cx, cy+(2*int(img_class.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.center_circle), (0,0,120),(img_class.center_circle+1))
                        cv2.putText(threshedimage, (str(step)), (cx, cy+(2*int(img_class.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (0,255,0),img_class.center_circle)
                    else:
                        cv2.putText(threshedimage, (str(step)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, (img_class.center_circle), (0,0,120),(img_class.center_circle+1))
                        cv2.putText(threshedimage, (str(step)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (0,255,0),img_class.center_circle)
                else:
                    if cy < ((threshedimage.shape[0])/4):
                        cv2.putText(threshedimage, (str(step)), (cx-(3*int(img_class.scale_bar/10)), cy+(2*int(img_class.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.center_circle), (0,0,120),(img_class.center_circle+1))
                        cv2.putText(threshedimage, (str(step)), (cx-(3*int(img_class.scale_bar/10)), cy+(2*int(img_class.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (0,255,0),img_class.center_circle)
                    else:
                        cv2.putText(threshedimage, (str(step)), (cx-(3*int(img_class.scale_bar/10)), cy), cv2.FONT_HERSHEY_SIMPLEX, (img_class.center_circle), (0,0,120),(img_class.center_circle+1))
                        cv2.putText(threshedimage, (str(step)), (cx-(3*int(img_class.scale_bar/10)), cy), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (0,255,0),img_class.center_circle)
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
        cv2.circle(threshedimage, (cx, cy), img_class.center_circle+1, (135, 206, 235), -1)
        if cx < (3*(threshedimage.shape[1])/4):
            if cy < ((threshedimage.shape[0])/4):
                cv2.putText(threshedimage, (str(max_number)), (cx, cy+(2*int(img_class.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.center_circle), (255,192,0),(img_class.center_circle+1))
            else:
                cv2.putText(threshedimage, (str(max_number)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, (img_class.center_circle), (255,192,0),(img_class.center_circle+1))
        else:
            if cy < ((threshedimage.shape[0])/4):
                cv2.putText(threshedimage, (str(max_number)), (cx-(3*int(img_class.scale_bar/10)), cy+(2*int(img_class.scale_bar/10))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.center_circle), (255,192,0),(img_class.center_circle+1))
            else:
                cv2.putText(threshedimage, (str(max_number)), (cx-(3*int(img_class.scale_bar/10)), cy), cv2.FONT_HERSHEY_SIMPLEX, (img_class.center_circle), (255,192,0),(img_class.center_circle+1))
    return threshedimage, cnts

def edge_select(): ##Creates a menu to select the threshold settings you want to use to select contours
    global edge_menu, csvlx, csvly, csvux, csvuy, tracing_img, contour_close_btn, undo_btn
    if edge_menu is not None: #Checks if the menu is currently open and closes it if it is
        edge_menu.destroy()
    
    contour_close_btn = undo_btn = None
    csvlx = csvly = csvux = csvuy = np.array([], dtype="int64")
    tracing_img = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)

    edge_menu = Toplevel()
    edge_menu.title("Edge Selection")
    edge_menu.configure(bg="gray69")
    edge_menu.minsize(300,300)
    Label(edge_menu, text="Select contours from the thresholds you selected",font= ("Helvetica", 14)).grid(row = 0, columnspan = 2)
    edge_counter = 0

    if len(contour_iterations) > 0: #Creates up to three buttons based off the list of thresholds
        btn = Button(edge_menu, text="Add Contours w/ Threshold: "+str(contour_iterations[0][0]) + "," +str(contour_iterations[0][1]), font= ("Helvetica", 12), command = lambda: add_contours(0, contour_iterations[0][0], contour_iterations[0][1]) )
        btn.grid(row=(1), column = 0)

    
    if len(contour_iterations) > 1:
        btn = Button(edge_menu, text="Add Contours w/ Threshold: "+str(contour_iterations[1][0]) + "," +str(contour_iterations[1][1]), font= ("Helvetica", 12), command = lambda: add_contours(1, contour_iterations[1][0], contour_iterations[1][1]) )
        btn.grid(row=(2), column = 0)
    
    if len(contour_iterations) >2:
        btn = Button(edge_menu, text="Add Contours w/ Threshold: "+str(contour_iterations[2][0]) + "," +str(contour_iterations[2][1]), font= ("Helvetica", 12), command = lambda: add_contours(2, contour_iterations[2][0], contour_iterations[2][1]) )
        btn.grid(row=(3), column = 0)

    if len(contour_iterations) == 0: #Creates at least one button using the last settings if the list is empty
        btn = Button(edge_menu, text="Add Contours w/ Threshold: "+str(lower_thresh_old) + "," +str(upper_thresh_old), font= ("Helvetica", 12), command = lambda: add_contours(0, lower_thresh_old, upper_thresh_old) )
        btn.grid(row=1, column = 0)
    
    cls_btn = Button(edge_menu, text="Close", bg="tomato", font= ("Helvetica", 12), command=edge_menu.destroy)
    cls_btn.grid(row=4, column = 0)

def add_contours(iteration, lower_thresh, upper_thresh): ##Creates a menu to select contours
    global contour_menu, contour_input, lower_list, upper_list, tracing_image, list_label, save_csv_btn, undo_btn
    if contour_menu is not None:
        contour_menu.destroy()
    if save_csv_btn is not None:
        save_csv_btn.destroy()
        save_csv_btn = None
    if undo_btn is not None:
        undo_btn.destroy()
        undo_btn = None
    

    contour_menu = Toplevel()
    contour_menu.title("Contour Selection")
    contour_menu.configure(bg="gray69")

    lower_list = np.array([])
    upper_list = np.array([])

    Label(contour_menu, text="Enter the numbers of the contours you would like to add and the position they are for\n Yellow represents a lower boundary and magenta an upper boundary", font= ("Helvetica", 14)).grid(row = 0, columnspan = 5)

    list_label = Label(contour_menu, text="Upper list: "+str(upper_list)+" and Lower list: " +str(lower_list), font= ("Helvetica", 12)) #Displays the values in the upper list and lower list 
    list_label.grid(row = 3, column=2, sticky="W")

    thresh_img = cv2.inRange(crop, lower_thresh, upper_thresh) #Creates the thresholded image, finds the contours, labels, and adds it to the contour menu
    threshed_image = cv2.cvtColor(thresh_img, cv2.COLOR_GRAY2BGR)
    threshed_image = cv2.medianBlur(threshed_image, 5)
    thresh_img, contours = label_center(thresh_img)

    thresh_img = resize(thresh_img,img_class.contour_resize)
    thresh_img = ImageTk.PhotoImage(Image.fromarray(thresh_img))

    thresh_image = Label(contour_menu, text="Threshold Image", image = thresh_img)
    thresh_image.image = thresh_img
    thresh_image.grid(row=1, columnspan=5)
    
    resize_trace_img = resize(tracing_img, img_class.contour_resize) #Creates a trace image that shows the data selected so far
    resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))
    tracing_image = Label(contour_menu, text="Tracing Image", image = resize_trace_img)
    tracing_image.image = resize_trace_img
    tracing_image.grid(row=2, columnspan=5)

    Label(contour_menu, text="Enter the contour number you would like to use (0-" +str(len(contours)-1)+")", font= ("Helvetica", 12)).grid(row = 3, column = 0, sticky="E") #Displays the possible contours that can be used

    contour_input = Entry(contour_menu, font= ("Helvetica", 12))
    contour_input.insert(END, "0")
    contour_input.grid(row=3, column =1, sticky = "W")


    add_lower_btn = Button(contour_menu, text="Add Contour as Lower", bg="yellow", font= ("Helvetica", 12), command= lambda: add_lower(contours, int(contour_input.get()))) #Adds a button to add the lower half of a contour to the lower list
    add_lower_btn.grid(row=5, column = 0, sticky="E")

    add_upper_btn = Button(contour_menu, text="Add Contour as Upper", bg="magenta2", font= ("Helvetica", 12), command= lambda: add_upper(contours, int(contour_input.get()))) #Adds a button to add the upper half of a contour to the upper list
    add_upper_btn.grid(row=5, column = 1,sticky="W")

    add_bulk_btn = Button(contour_menu, text="Add Bulk Lower to Upper", bg="magenta4", font= ("Helvetica", 12), command=lambda: add_bulk_low_as_up(contours,lower_list)) #Adds a button to add lower half of contours of unselected contours above the lower data to the upper list
    add_bulk_btn.grid(row=6, column = 1, sticky="W")
    Label(contour_menu, text="Bulks add traces for data above/below lists used", font= ("Helvetica", 12)).grid(row=6, column =2, sticky="W")

    add_lower_as_upper_btn = Button(contour_menu, text="Add Lower as Upper", bg="magenta4", font= ("Helvetica", 12), command= lambda: add_lower_as_upper(contours, int(contour_input.get()))) #Adds the bottom half of the contour to the upper list
    add_lower_as_upper_btn.grid(row=5, column = 2, sticky="W")
    
    add_bulk_lower_btn = Button(contour_menu, text="Add Bulk Lower", bg="gold", font= ("Helvetica", 12), command=lambda: add_bulk(contours,upper_list, threshed_image)) #Adds all of the lower half of the contours below the upper data
    add_bulk_lower_btn.grid(row=6, column = 0, sticky="E")





def add_upper(contours, contour_number): ##Adds the upper half of a contour to the upper list
    global upper_list, csvux, csvuy, tracing_img, csvlx, csvly, save_csv_btn, in_calc_btn, edge_close_btn, contour_close_btn, undo_btn, lower_list
    if contour_number not in upper_list:
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
        cx = cx[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]
        cx = cx[::-1] #Converts lower data from L-R to R-L
    
        cy = coordy[bottomright:]
        cy2 = coordy[:bottomright]
        cy = np.append(cy, cy2)
        cy = cy[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]
        cy = cy[::-1] #Converts lower data from L-R to R-L
    
        csvux = np.append(csvux, cx)
        csvuy = np.append(csvuy, cy)
        upper_list = np.append(upper_list, contour_number)
        length = len(cx)
        update_image_up(tracing_img, csvux, csvuy, contours, contour_number)
        if undo_btn is not None:
            undo_btn.grid_remove()
        undo_btn = Button(contour_menu, text="Undo", bg="alice blue", font= ("Helvetica", 12), command= lambda: undo(0, length, contours))
        undo_btn.grid(row=7, column = 0, sticky="E")
        list_label.configure(text="Upper list: "+str(upper_list)+" and Lower list: " +str(lower_list), font= ("Helvetica", 12))
        list_label.update()
    if save_csv_btn is None:
        save_csv_btn = Button(root, text="Save CSVs", font = ("Helvetica", 14), bg="lawn green",command=save_csv)
        save_csv_btn.grid(row=4, column=0)
    if edge_close_btn is None:
            edge_close_btn = Button(edge_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=edge_menu.destroy)
            edge_close_btn.grid(row=4, column = 0)
    if contour_close_btn is None:
        contour_close_btn = Button(contour_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=contour_menu.destroy)
        contour_close_btn.grid(row=7, column=1 , sticky="W")
        
def add_lower(contours, contour_number): ##Adds the lower half of a contour to the lower list
    global lower_list, csvlx, csvly, tracing_img, contour_close_btn, in_calc_btn, edge_close_btn, csvux, csvuy, save_csv_btn, undo_btn, upper_list
    if contour_number not in lower_list:
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
        cx = cx[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]
        cy = coordy[topleft:]
        cy2 = coordy[:topleft]
        cy = np.append(cy, cy2)
        cy = cy[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]

        csvlx = np.append(csvlx, cx)
        csvly = np.append(csvly, cy)
        lower_list = np.append(lower_list, contour_number)

        update_image_low(tracing_img, csvlx, csvly, contours, contour_number)
        if undo_btn is not None:
            undo_btn.grid_remove()
        undo_btn = Button(contour_menu, text="Undo", bg="alice blue", font= ("Helvetica", 12), command= lambda: undo(1, len(cx), contours))
        undo_btn.grid(row=7, column = 0, sticky="E")
        list_label.configure(text="Upper list: "+str(upper_list)+" and Lower list: " +str(lower_list), font= ("Helvetica", 12))
        list_label.update()
    
    if save_csv_btn is None:
        save_csv_btn = Button(root, text="Save CSVs", font = ("Helvetica", 14), bg="lawn green",command=save_csv)
        save_csv_btn.grid(row=4, column=0)
    if edge_close_btn is None:
        edge_close_btn = Button(edge_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=edge_menu.destroy)
        edge_close_btn.grid(row=4, column = 0)
    if contour_close_btn is None:
        contour_close_btn = Button(contour_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=contour_menu.destroy)
        contour_close_btn.grid(row=7, column=1 , sticky="W")
    
def add_bulk_low_as_up(contours, lower_list): ##Adds the lower half of contours of unselected contours above the lower data to upper data
    global csvly, csvux, csvuy, tracing_img, save_csv_btn, edge_close_btn, contour_close_btn, upper_list
    minval = np.amax(csvly)
    for i in range(len(contours)):
        if i not in lower_list and minval > contours[i][0][0][1]:
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
            cx = cx[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]
            cx = cx[::-1] #Converts lower data from L-R to R-L

            cy = coordy[bottomright:]
            cy2 = coordy[:bottomright]
            cy = np.append(cy, cy2)
            cy = cy[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)] 
            cy = cy[::-1] #Converts lower data from L-R to R-L
    
            csvux = np.append(csvux, cx)
            csvuy = np.append(csvuy, cy)
            upper_list = np.append(upper_list, i)

            update_image_up(tracing_img, csvux, csvuy, contours, i)

    if save_csv_btn is None:
        save_csv_btn = Button(root, text="Save CSVs", font = ("Helvetica", 14), bg="lawn green", command=save_csv)
        save_csv_btn.grid(row=4, column=0)
    if edge_close_btn is None:
        edge_close_btn = Button(edge_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=edge_menu.destroy)
        edge_close_btn.grid(row=4, column = 0)
    if contour_close_btn is None:
        contour_close_btn = Button(contour_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=contour_menu.destroy)
        contour_close_btn.grid(row=7, column=1 , sticky="W")

def add_lower_as_upper(contours, contour_number): ##Adds the bottom half of the contour data to the upper data
    global upper_list, csvlx, csvly, tracing_img, contour_close_btn, edge_close_btn, csvux, csvuy, save_csv_btn, undo_btn
    if contour_number not in upper_list:
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
        cx = cx[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]
        cy = coordy[topleft:]
        cy2 = coordy[:topleft]
        cy = np.append(cy, cy2)
        cy = cy[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]

        csvux = np.append(csvux, cx)
        csvuy = np.append(csvuy, cy)
        upper_list = np.append(upper_list, contour_number)

        update_image_up(tracing_img, csvux, csvuy, contours, contour_number)
        if undo_btn is not None:
                undo_btn.grid_remove()
        undo_btn = Button(contour_menu, text="Undo", bg="alice blue", font= ("Helvetica", 12), command= lambda: undo(0, len(cx), contours))
        undo_btn.grid(row=7, column = 0, sticky="E")
        list_label.configure(text="Upper list: "+str(upper_list)+" and Lower list: " +str(lower_list), font= ("Helvetica", 12))
        list_label.update()
    
    if len(csvlx) > 0 and len(csvux) > 0:
        if save_csv_btn is None:
            save_csv_btn = Button(root, text="Save CSVs", font = ("Helvetica", 14), bg="lawn green",command=save_csv)
            save_csv_btn.grid(row=4, column=0)
        if edge_close_btn is None:
            edge_close_btn = Button(edge_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=edge_menu.destroy)
            edge_close_btn.grid(row=4, column = 0)
        if contour_close_btn is None:
            contour_close_btn = Button(contour_menu, text="Close and Continue", bg="tomato", font= ("Helvetica", 12), command=contour_menu.destroy)
            contour_close_btn.grid(row=7, column=1 , sticky="W")

def add_bulk(contours, upper_list, threshed_image): #Adds all of the lower half of the contours below the upper data
    global csvly, csvlx, csvux, csvuy, tracing_img, save_csv_btn, edge_close_btn, contour_close_btn, lower_list
    minval = np.amin(csvuy)
    largest_in_list = np.amax(upper_list)
    counter = 0
    for i in range(len(contours)): #Iterates the contours and does the add lower process
        cx = contours[i][0][0][0]
        cy = contours[i][0][0][1]
        b, _, _ = (threshed_image[(cy+1),(cx)])
        
        if i not in upper_list and i < largest_in_list and minval < cy and b == 255:
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
            cx = cx[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]
            cy = coordy[topleft:]
            cy2 = coordy[:topleft]
            cy = np.append(cy, cy2)
            cy = cy[img_class.contour_buffer:(sliceLength-img_class.contour_buffer)]

            csvlx = np.append(csvlx, cx)
            csvly = np.append(csvly, cy)
            lower_list = np.append(lower_list, i)
            update_image_low(tracing_img, csvlx, csvly, contours, i)
    if save_csv_btn is None:
        save_csv_btn = Button(root, text="Save CSVs", font = ("Helvetica", 14), bg="lawn green", command=save_csv)
        save_csv_btn.grid(row=4, column=0)
    if edge_close_btn is None:
        edge_close_btn = Button(edge_menu, text="Close and Continue", font= ("Helvetica", 12), bg="tomato", command=edge_menu.destroy)
        edge_close_btn.grid(row=4, column = 0)
    if contour_close_btn is None:
        contour_close_btn = Button(contour_menu, text="Close and Continue", bg="tomato",font= ("Helvetica", 12), command=contour_menu.destroy)
        contour_close_btn.grid(row=7, column=1 , sticky="W")



def undo(up_or_low, len_data, contours): ##Undoes the previous non-bulk action
    global lower_list, upper_list, csvlx, csvly, csvux, csvuy, undo_btn, tracing_img
    tracing_img = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
    if up_or_low == 0:
        upper_list = upper_list[:-1]
        csvux = csvux[:-len_data]
        csvuy = csvuy[:-len_data]
    
    else:
        lower_list = lower_list[:-1]
        csvlx = csvlx[:-len_data]
        csvly = csvly[:-len_data]
    
    for i in range(len(csvlx)):
        cv2.circle(tracing_img, (int(csvlx[i]), int(csvly[i])), img_class.center_circle, (255,255,0), -1)
    for i in range(len(csvux)):
        cv2.circle(tracing_img, (int(csvux[i]), int(csvuy[i])), img_class.center_circle, (255,0,255), -1)
    
    for i in lower_list:
        cx = contours[int(i)][0][0][0]
        cy = contours[int(i)][0][0][1]
        cv2.putText(tracing_img, (str(i)), (cx, cy+(int(img_class.scale_bar/20))), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (255,255,0),img_class.center_circle+1)

    for i in upper_list:
        cx = contours[int(i)][0][0][0]
        cy = contours[int(i)][0][0][1]
        cv2.putText(tracing_img, (str(i)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (255,0,255),img_class.center_circle+1)
    
    resize_trace_img = resize(tracing_img, img_class.contour_resize)
    resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))

    tracing_image.configure(image=resize_trace_img)
    tracing_image.image=resize_trace_img

    list_label.configure(text="Upper list: "+str(upper_list)+" and Lower list: " +str(lower_list), font= ("Helvetica", 12))
    list_label.update()
    undo_btn.grid_remove()
    
def update_image_low(tracing_img, csvx, csvy, contours, contour_number): ##Updates the image when new data is added to the lower list
    global contour_status
    for i in range(len(csvx)):
        cv2.circle(tracing_img, (int(csvx[i]), int(csvy[i])), img_class.center_circle, (255,255,0), -1)
    cx = contours[contour_number][0][0][0]
    cy = contours[contour_number][0][0][1]
    cv2.putText(tracing_img, (str(contour_number)), (cx, cy+(int(img_class.scale_bar/20))), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (255,255,0),img_class.center_circle+1)

    resize_trace_img = resize(tracing_img, img_class.contour_resize)
    resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))

    tracing_image.configure(image=resize_trace_img)
    tracing_image.image=resize_trace_img
    if contour_status is None:
        contour_status = Label(root, text="You have selected some contour data", font= ("Helvetica", 12))
        contour_status.grid(row = 3, column =1, sticky="W")

def update_image_up(tracing_img, csvx, csvy, contours, contour_number): ##Updates the image when new data is added to the upper list
    global contour_status
    for i in range(len(csvx)):
        cv2.circle(tracing_img, (int(csvx[i]), int(csvy[i])), img_class.center_circle, (255,0,255), -1)
    cx = contours[contour_number][0][0][0]
    cy = contours[contour_number][0][0][1]

    cv2.putText(tracing_img, (str(contour_number)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (255,0,255),img_class.center_circle+1)
    
    resize_trace_img = resize(tracing_img, img_class.contour_resize)
    resize_trace_img = ImageTk.PhotoImage(Image.fromarray(resize_trace_img))

    tracing_image.configure(image=resize_trace_img)
    tracing_image.image=resize_trace_img
    if contour_status is None:
        contour_status = Label(root, text="You have selected some contour data", font= ("Helvetica", 12))
        contour_status.grid(row = 3, column =1, sticky="W")



def save_csv(): ##Saves the upper and lower lists as csvs
    global csvlx, csvly, csvux, csvuy, path, short_dist_btn, cbtn, thresh_btn, edge_btn, save_csv_btn, crop_status, thresh_status, contour_status, calculate_status, scale_ratio, scale_ratio_label, int_save_folder_path, int_lower_csv, int_upper_csv, int_calc_btn
    ratio = scale_reader(path) #Gets the scale ratio from the image
    if ratio != "Error":   
     #Proceeds with normal process if scale_reader doesn't fail    
        tracing_img = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        width = int(tracing_img.shape[1])
        height = int(tracing_img.shape[0])
        int_ratio = int(ratio)
        #print(ratio) #Check value
        #print(width) #Check value
        if int_ratio//10 == 0 and width > 3000:
            scale_length = int(50*ratio)
            scale_text = str(50) + " um"
        elif int_ratio//10 == 0 and width < 3000:
            scale_length = int(20*ratio)
            scale_text = str(20)+" um"
        elif int_ratio//10 == 1 and width <3000:
            scale_length = int(20*ratio)
            scale_text = str(20) +" um"
        elif int_ratio//10 == 2 and width <3000:
            scale_length = int(10*ratio)
            scale_text = str(10) +" um"
        elif int_ratio//10 > 0 and width >3000:
            scale_length = int(250*ratio)
            scale_text = str(250)+" um"
        elif int_ratio//10 == 5 and width < 3000:
            scale_length = int(10*ratio)
            scale_text = str(10)+" um"
        
        ratio = str(ratio)

        needed_length = 8 - len(ratio)

        if needed_length > 0: # Adds zeroes until the string is eight characters long
            additional_length =""
            for _ in range(needed_length):
                additional_length += "0"
            ratio= additional_length + ratio 
        
        current_dir = os.getcwd() #Creates the unworked and worked csvs folder if they do not exist
     #Saves the Data
        csvlx = csvlx.astype(np.int)
        csvux = csvux.astype(np.int)
        csvly = csvly.astype(np.int)
        csvuy = csvuy.astype(np.int)

        if len(contour_iterations) > 0:
            lower_thresh_value = str(contour_iterations[0][0])
            upper_thresh_value = str(contour_iterations[0][1])
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
            lower_thresh_value = str(lower_thresh_old)
            upper_thresh_value = str(upper_thresh_old)
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

     
        filename = os.path.basename(path) #Saves the csvs in the unworkedcsvs folder
        filename = filename[:-4]
        if img_class.in_or_ex == 1:
            unworked_dir = current_dir+"/unworkedcsv/"
            check_dir = Path(unworked_dir)
            if check_dir.exists() is False:
                os.mkdir(unworked_dir)
                os.mkdir(current_dir+"/workedcsv")
            np.savetxt(unworked_dir+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(img_class.ratio)+ratio+".csv",list(zip(csvlx, csvly)), fmt = "%s", delimiter = ",")
            np.savetxt(unworked_dir+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(img_class.ratio)+ratio+".csv",list(zip(csvux, csvuy)), fmt = "%s", delimiter = ",")
        else:
            worked_dir = current_dir+"/worked-internalcsv/"
            filefolder = "/"+filename+"/"
            if Path(worked_dir+filefolder).exists() is False:
                os.mkdir(worked_dir+filefolder)
            np.savetxt(worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(img_class.ratio)+ratio+".csv",list(zip(csvlx, csvly)), fmt = "%s", delimiter = ",")
            np.savetxt(worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(img_class.ratio)+ratio+".csv",list(zip(csvux, csvuy)), fmt = "%s", delimiter = ",")
        for i in range(len(csvux)):
            cv2.circle(tracing_img, (csvux[i], csvuy[i]), 3, (255,0,255), -1)
        for i in range(len(csvlx)):
            cv2.circle(tracing_img, (csvlx[i], csvly[i]), 3, (255,255,0), -1)
        cv2.line(tracing_img, (width-(scale_length+20), (height-20)), ((width-20), (height-20)), (0,0,0), (img_class.label_text+2))
        cv2.line(tracing_img, (width-(scale_length+20), (height-20)), ((width-20), (height-20)), (255,255,255), (img_class.label_text))
        cv2.putText(tracing_img, scale_text, ((width-(scale_length+20)), (height-25)), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2)
    
        if img_class.in_or_ex ==1:
            cv2.imwrite((unworked_dir+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+".png"), tracing_img)
            if short_dist_btn is None:
                short_dist_btn = Button(root, text="Calculate Shortest Distance", font = ("Helvetica", 14), bg="dodger blue", command = shortest_distance)
                short_dist_btn.grid(row=5, column=0)
    
            waiting_files = len(os.listdir(unworked_dir))//3
            if calculate_status is None:
                calculate_status = Label(root, text="There are "+str(waiting_files)+" images waiting for calculations", font = ("Helvetica", 12))
                calculate_status.grid(row =5, column = 1, sticky="W")
            else:
                calculate_status.configure(text="There are "+str(waiting_files)+" images waiting for calculations", font = ("Helvetica", 12))
                calculate_status.update()
        else:
            cv2.imwrite((worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+".png"), tracing_img)
            int_save_folder_path = worked_dir+filefolder
            int_lower_csv = worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(img_class.ratio)+ratio+".csv"
            int_upper_csv = worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(img_class.ratio)+ratio+".csv"
            if int_calc_btn is None:
                int_calc_btn = Button(root, text="Calculate Internal Stats", font=("Helvetica", 14), bg="dodger blue", command = int_calc)
                int_calc_btn.grid(row=5, column = 0)

     #Resets buttons
        cbtn.destroy()
        thresh_btn.destroy()
        edge_btn.destroy()
        save_csv_btn.destroy()
        crop_status.grid_remove()
        contour_status.grid_remove()
        if thresh_status is not None:
            thresh_status.grid_remove()

        cbtn = thresh_btn = edge_btn = save_csv_btn = crop_status = thresh_status = contour_status = None

        status_path.configure(text="Your CSV has been saved")
        status_path.update()
    else:
        save_csv_btn["command"] = save_csv_manual
        scale_ratio = Entry(root, font=("Helvetica", 12))
        scale_ratio.insert(END, "ENTER SCALE RATIO")
        scale_ratio.grid(row = 4, column = 1, sticky="W")
        scale_ratio_label = Label(root, text="Enter a scale ratio here (From ImageJ)", font=("Helvetica", 12))
        scale_ratio_label.grid(row = 5, column =1)

def save_csv_manual():
        global csvlx, csvly, csvux, csvuy, path, short_dist_btn, cbtn, thresh_btn, edge_btn, save_csv_btn, crop_status, thresh_status, contour_status, calculate_status, scale_ratio, scale_ratio_label, int_save_folder_path, int_lower_csv, int_upper_csv, int_calc_btn
     #Normal process using entry    
        ratio = float(scale_ratio.get())
        tracing_img = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        width = int(tracing_img.shape[1])
        height = int(tracing_img.shape[0])
        int_ratio = int(ratio)
        if int_ratio//10 == 0 and width > 3000:
            scale_length = int(50*ratio)
            scale_text = str(50) + " um"
        elif int_ratio//10 == 0 and width < 3000:
            scale_length = int(20*ratio)
            scale_text = str(20)+" um"
        elif int_ratio//10 == 1 and width <3000:
            scale_length = int(20*ratio)
            scale_text = str(20) +" um"    
        elif int_ratio//10 > 0 and width >3000:
            scale_length = int(250*ratio)
            scale_text = str(250)+" um"
        ratio = str(ratio)

        needed_length = 8 - len(ratio)

        if needed_length > 0: # Adds zeroes until the string is eight characters long
            additional_length =""
            for _ in range(needed_length):
                additional_length += "0"
            ratio= additional_length + ratio
     #Creates Directory if it doesn't exist
        current_dir = os.getcwd() #Creates the unworked and worked csvs folder if they do not exist
        unworked_dir = current_dir+"/unworkedcsv/"
        check_dir = Path(unworked_dir)
        if check_dir.exists() is False:
            os.mkdir(unworked_dir)
            os.mkdir(current_dir+"/workedcsv")
     #Saves the Data
        csvlx = csvlx.astype(np.int)
        csvux = csvux.astype(np.int)
        csvly = csvly.astype(np.int)
        csvuy = csvuy.astype(np.int)

        if len(contour_iterations) > 0:
            lower_thresh_value = str(contour_iterations[0][0])
            upper_thresh_value = str(contour_iterations[0][1])
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
            lower_thresh_value = str(lower_thresh_old)
            upper_thresh_value = str(upper_thresh_old)
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

     
        filename = os.path.basename(path) #Saves the csvs in the unworkedcsvs folder
        filename = filename[:-4]
        if img_class.in_or_ex == 1:
            unworked_dir = current_dir+"/unworkedcsv/"
            check_dir = Path(unworked_dir)
            if check_dir.exists() is False:
                os.mkdir(unworked_dir)
                os.mkdir(current_dir+"/workedcsv")
            np.savetxt(unworked_dir+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(img_class.ratio)+ratio+".csv",list(zip(csvlx, csvly)), fmt = "%s", delimiter = ",")
            np.savetxt(unworked_dir+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(img_class.ratio)+ratio+".csv",list(zip(csvux, csvuy)), fmt = "%s", delimiter = ",")
        else:
            worked_dir = current_dir+"/worked-internalcsv/"
            filefolder = "/"+filename+"/"
            if Path(worked_dir+filefolder).exists() is False:
                os.mkdir(worked_dir+filefolder)
            np.savetxt(worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+" Lower"+ratio+".csv",list(zip(csvlx, csvly)), fmt = "%s", delimiter = ",")
            np.savetxt(worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+" Upper"+ratio+".csv",list(zip(csvux, csvuy)), fmt = "%s", delimiter = ",")
        for i in range(len(csvux)):
            cv2.circle(tracing_img, (csvux[i], csvuy[i]), 3, (255,0,255), -1)
        for i in range(len(csvlx)):
            cv2.circle(tracing_img, (csvlx[i], csvly[i]), 3, (255,255,0), -1)
        cv2.line(tracing_img, (width-(scale_length+20), (height-20)), ((width-20), (height-20)), (0,0,0), (img_class.label_text+2))
        cv2.line(tracing_img, (width-(scale_length+20), (height-20)), ((width-20), (height-20)), (255,255,255), (img_class.label_text))
        cv2.putText(tracing_img, scale_text, ((width-(scale_length+20)), (height-25)), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2)
    
        if img_class.in_or_ex ==1:
            cv2.imwrite((unworked_dir+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+".png"), tracing_img)
            if short_dist_btn is None:
                short_dist_btn = Button(root, text="Calculate Shortest Distance", font = ("Helvetica", 14), bg="dodger blue", command = shortest_distance)
                short_dist_btn.grid(row=5, column=0)
    
            waiting_files = len(os.listdir(unworked_dir))//3
            if calculate_status is None:
                calculate_status = Label(root, text="There are "+str(waiting_files)+" images waiting for calculations", font = ("Helvetica", 12))
                calculate_status.grid(row =5, column = 1, sticky="W")
            else:
                calculate_status.configure(text="There are "+str(waiting_files)+" images waiting for calculations", font = ("Helvetica", 12))
                calculate_status.update()
        else:
            cv2.imwrite((worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+".png"), tracing_img)
            int_save_folder_path = worked_dir+filefolder
            int_lower_csv = worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Lower"+str(img_class.ratio)+ratio+".csv"
            int_upper_csv = worked_dir+filefolder+filename+"-"+lower_thresh_value+"-"+upper_thresh_value+"-Upper"+str(img_class.ratio)+ratio+".csv"
            if int_calc_btn is None:
                int_calc_btn = Button(root, text="Calculate Internal Stats", font=("Helvetica", 14), bg="dodger blue", command = int_calc)
                int_calc_btn.grid(row=5, column = 0)

     #Resets buttons
        cbtn.destroy()
        thresh_btn.destroy()
        edge_btn.destroy()
        save_csv_btn.destroy()
        crop_status.grid_remove()
        contour_status.grid_remove()
        scale_ratio.grid_remove()
        scale_ratio_label.grid_remove()

        if thresh_status is not None:
            thresh_status.grid_remove()

        cbtn = thresh_btn = edge_btn = save_csv_btn = crop_status = thresh_status = contour_status = scale_ratio = scale_ratio_label = None

        status_path.configure(text="Your CSV has been saved")
        status_path.update()
     
def scale_reader(path):
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
    else:
        img = img[int((height*0.78)):int((height*0.9)), (int(width*0.48)):(int(width*0.82))]
        height_text = img.shape[0]
        img_text = img[int(height*.045):int(height_text), 0:width]
        img_scale = img[0:int(height_text*.55),0:width]

    
    img = cv2.inRange(img, 250, 255)
    if width < 4000:
        img_text = resize(img_text, 300) #Helps with smaller images
    elif width < 5000:
        img_text = resize(img_text, 150)
    img_text = cv2.inRange(img_text, 250, 255) #Filters
    img_text = cv2.GaussianBlur(img_text, (3,3), 0) #Helps with Smaller Images
    img_scale = cv2.inRange(img_scale, 250, 255)
    custom_config = "--psm 6 outputbase digits"
    text = pytesseract.image_to_string(img_text, lang = "eng", config = custom_config)
    
    if text is not "" and " " not in text :
        text = int(text)
        cnts = cv2.findContours(img_scale, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        cnts = imutils.grab_contours(cnts)
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            leftmost = tuple(c[c[:,:,0].argmin()][0])
            rightmost = tuple(c[c[:,:,0].argmax()][0])
            distance = int(rightmost[0])-int(leftmost[0]) - 1
            ratio = distance / text
        else:
            ratio = "Error"
    else:
        ratio = "Error"
    return ratio

def shortest_distance(): ##Finds the files to be used for the shortest distance calcualtion
    current_dir = os.getcwd()
    unworked_dir = current_dir+"/unworkedcsv/"
    worked_dir = current_dir+"/workedcsv/"
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
            shortest_distance_calc((unworked_dir+filename), (unworked_dir+upper_filename), ratio,current_dir, save_folder_path, scale_ratio)
            shutil.move((unworked_dir+filename), (save_folder_path+filename))
            shutil.move((unworked_dir+upper_filename), (save_folder_path+upper_filename))
            shutil.move((unworked_dir+save_folder_name+".png"), (save_folder_path+save_folder_name+".png"))
    short_dist_btn.destroy()
    calculate_status.grid_remove()


def shortest_distance_calc(lower_csv, upper_csv, ratio,current_dir, save_folder_path, scale_ratio): ##Calculates the absolute shortest distance between points along the lower boundary and upper boundary csvs
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
    print("Calculating the shortest distance. Please be patient...")
    
    edge_limit = int(25*scale_ratio)
    vertical_check = int(3*scale_ratio)

 #Calculate shortest distance   
    for i1 in tqdm(range(edge_limit, len(c1) - edge_limit, ((len(c1)-(edge_limit*2))//(edge_limit*7)))):  #Automatic calculation of distance by reducing the pixel range to +- 200 pixels on second curve
        numb = c1[i1]
        tupx = (numb[0])
        tupy = (numb[1])
        tupcheck = list(range(tupx- vertical_check, tupx + vertical_check))
        for i in range(len(tupcheck)):
            if tupcheck[i] in c2check:
                cparray = [(tupx,tupy)]
                break
        if len(cparray) != 0:
            c2edit = [(x, y) for x, y in c2 if x in range(int(tupx - (vertical_check*1.5)), int(tupx + (vertical_check*1.5)))]
            d = np.append(d, distance.cdist(cparray,c2edit).min(axis=1))
            dx = np.append(dx, tupx)
        cparray = []
     
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
    title = fileinput[:-13] + " v " + curveinput[:-13]
    ax.set_title(title)
    ax.set_xlabel("")
    ax.yaxis.set_major_locator(plt.MaxNLocator(15))
 #Saves the boxplot   
    picturename = fileinput[:-13] + " v " + curveinput[:-13] + ".png"
    fig.savefig(save_folder_path + picturename)
    plt.close()
    np.savetxt((save_folder_path+ title + ".csv"), list(zip(d,dx)), fmt= "%s", delimiter=",", header="Shortest Distances, pixel location")

 #Saves the data   
    csv_summary_location = current_dir+"/Auto Tracer Summary.csv"
    if Path(csv_summary_location).is_file() is False: #Creates a summary csv if none exists and appends the new data
        file_start = np.array(["Image/Thresholds", "ratio", "Mean", "Median", "Q1", "Q3", "SD", "Trapezoidal", "Polygon", "datapoints"])
        np.savetxt(current_dir+"/Auto Tracer Summary.csv",file_start[None], fmt="%s", delimiter =",")
    with open(current_dir+"/Auto Tracer Summary.csv", "a", newline="") as newFile:
        newFileWriter = csv.writer(newFile)
        newFileWriter.writerow([fileinput[:-19],str(density), str(round(np.mean(d), 5)), str(round(np.median(d), 5)), str(round(quartile[0], 5)), str(round(quartile[1], 5)),
        str(round(np.std(d), 5)), str(round(Tabc/clavg, 5)), str(round(Tarea / clavg, 5)), str(len(d))])
def shortest_distance_menu():
    global status_path, root, short_dist_btn, calculate_status
    root = Toplevel()
    main_menu.withdraw()
    root.title("Auto Measurement")
    root.configure(bg="gray69")
    root.minsize(300,300)

    path_btn = Button(root, text="Please select the image you would like to use", font = ("Helvetica", 14), bg="OliveDrab1", command = select_image)
    path_btn.grid(row = 0, column = 0)
    status_path = Label(root, text="There is no loaded image", font = ("Helvetica", 12))
    status_path.grid(row = 0, column = 1)

    current_dir = os.getcwd()
    unworked_dir = current_dir+"/unworkedcsv/"
    check_dir = Path(unworked_dir)
    if check_dir.exists() is False:
        os.mkdir(unworked_dir)
        os.mkdir(current_dir+"/workedcsv")
    waiting_files = len(os.listdir(unworked_dir))//3
    if waiting_files > 0:
        short_dist_btn = Button(root, text="Calculate Shortest Distance", font = ("Helvetica", 14), bg="dodger blue", command = shortest_distance)
        short_dist_btn.grid(row=6, column=0)
        calculate_status = Label(root, text="There are "+str(waiting_files)+" images waiting for calculations", font = ("Helvetica", 12))
        calculate_status.grid(row =6, column = 1, sticky="W")
    return_btn = Button(root, text="Return to Main Menu", font = ("Helvetica", 14), bg="linen", command = lambda:[root.destroy(), main_menu.deiconify()])
    return_btn.grid(row = 7, columnspan = 2)

def concavity_menu():
    global cc_csv_status, cc_menu
    cc_menu = Toplevel()
    main_menu.withdraw()
    cc_menu.title("Concavity Calculator")
    cc_menu.configure(bg="gray69")
    cc_menu.minsize(300,300)


    return_btn = Button(cc_menu, text="Return to Main Menu", font = ("Helvetica", 14), bg="linen", command = lambda:[cc_menu.destroy(), main_menu.deiconify()])
    return_btn.grid(row = 6, columnspan = 2)

    csv_select = Button(cc_menu, text="Select CSVs", font=("Helvetica", 14), bg="deep sky blue", command = load_csv)
    csv_select.grid(row = 1, column = 0)
    cc_csv_status = Label(cc_menu, text="Select the csv you would like to use for calculations", font=("Helvetica", 12))
    cc_csv_status.grid(row=1,column = 1)

    

def load_csv():
    global lower_csv_cc, upper_csv_cc, cc_calc_btn
    current_dir = os.getcwd()
    worked_dir = current_dir + "/workedcsv"
    lower_csv_cc = filedialog.askopenfilename(initialdir = worked_dir, filetypes = [("CSV",".csv" )])
    if len(lower_csv_cc)>0:
        if "Lower" in lower_csv_cc:
            ratio = float(lower_csv_cc[-12:-4])
            upper_csv_cc = lower_csv_cc[:-17] + "Upper"+lower_csv_cc[-12:]
        elif "Upper" in lower_csv_cc:
            ratio = float(lower_csv_cc[-12:-4])
            upper_csv_cc = lower_csv_cc
            lower_csv_cc = upper_csv_cc[:-17] +"Lower"+upper_csv_cc[-12:]
        cc_csv_status.configure(text ="Data has been selected")
        cc_csv_status.update()
        
        if cc_calc_btn is None:
            cc_calc_btn = Button(cc_menu, text="Calculate Concavities", font=("Helvetica", 14), bg="sky blue", command = poly_calc)
            cc_calc_btn.grid(row=2, column = 0)

    else:
        cc_csv_status.configure(text="No data has been selected")
        cc_csv_status.update()
        
def poly_calc():
    global cc_contour_check_btn, cc_figure, cc_contour_check_status, deriv
 #Load The Images
    x1 = np.empty(0) #Creates an empty data set to store CSV values
    y1 = np.empty(0)
    fileinput = lower_csv_cc
    with open(fileinput) as csvfile:
        Curve = csv.reader(csvfile, delimiter=",")
        for line in Curve:
            x1 = np.append(x1, line[0])
            y1 = np.append(y1, line[1])

    x2 = np.empty(0)
    y2 = np.empty(0)
    fileinput2 = upper_csv_cc
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
    deriv = np.polyder(fit[::-1], 2) # Second Derivative of Polynomial Fit
    dfit = np.polyval(deriv, x1) #Calculates the y values for the second derivtave

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
    fileinput = os.path.basename(lower_csv_cc)
    if check_dir.exists() is False:
        os.mkdir(worked_cc_dir)
    if len(os.listdir(worked_cc_dir)) == 0:
        first_line = np.array(["Location", "Ratio"," Concave Points", "Mean", "Median", "Q1", "Q3", "SD", "Convex Points", "Mean", "Median", "Q1", "Q3", "SD"])
        np.savetxt(current_dir+"/Concavity Calculator Summary.csv",first_line[None] ,fmt="%s", delimiter=",")
    with open(current_dir+"/Concavity Calculator Summary.csv", "a", newline="") as newFile:
        newFileWriter = csv.writer(newFile)
        newFileWriter.writerow([fileinput[:-17], str(density),str(len(cave)),str(round(np.mean(cave), 5)), str(round(quartcave[1], 5)), str(round(quartcave[0], 5)), str(round(quartcave[2], 5)), str(round(np.std(cave), 5)),str(len(vex)), str(round(np.mean(vex), 5)), str(round(quartvex[1], 5)), str(round(quartvex[0], 5)), str(round(quartvex[2], 5)), str(round(np.std(vex), 5))])


    fileinput = fileinput.replace(".csv", "")
    fileinput2 = os.path.basename(upper_csv_cc)
    fileinput2 = fileinput.replace(".csv", "")
    graphtitle = fileinput + "Vs" + fileinput2 + "-Concavity"

    np.savetxt((worked_cc_dir+graphtitle + ".csv"), list(zip(deepcave, deepvex)), fmt= "%s", delimiter=",", header="Concave, Convex")#Saves the Data as a CSV in root folder

 #The following plots the original, polynomial, second derivative, and concavities
    fig, ax = plt.subplots(2, sharex = True)
    fig.suptitle(graphtitle)
    ax[0].plot(x2, y2, c="m", label = "Upper")
    ax[1].set_xlabel("Pixels")
    ax[0].set_ylabel("Pixels")
    ax[1].set_ylabel("Pixels")
    ax[0].plot(x1, y1, c="k", label = "Data")
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
    cc_figure = fig
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
    if cc_contour_check_btn is None:
        cc_contour_check_btn = Button(cc_menu, text="Check Images / Wedge Analysis", bg="medium spring green", font=("Helvetica", 14), command = lambda: [cc_menu.withdraw(), cc_contour_check()])
        cc_contour_check_btn.grid(row = 3, column = 0)
        cc_contour_check_status = Label(cc_menu, text="Allows you to find the concavities at specific points", font=("Helvetica", 12))
        cc_contour_check_status.grid(row=3, column =1)
    cc_calc_btn.destroy()
    cc_csv_status.configure(text="The data has been saved in Concavity Calculator Summary.csv")
    cc_csv_status.update()

def cc_contour_check():
    cc_contour_menu = Toplevel()
    cc_contour_menu.title("Concavity Magnitude Calculator")
    cc_contour_menu.configure(bg="gray69")
    mag_status = None
    Label(cc_contour_menu, text="This page will let you check the concavity at specified points", font=("Helvetica", 12)).grid(row=0, columnspan =3)
    cc_canvas = FigureCanvasTkAgg(cc_figure, master =cc_contour_menu)
    cc_canvas.draw()
    cc_canvas.get_tk_widget().grid(row =1, columnspan = 2)
    Label(cc_contour_menu, text="Enter the x coordinate displayed while hovering over the upper boundary", font=("Helvetica", 12)).grid(row=3, column=0, sticky="E")
    cc_toolbar_frame = Frame(master=cc_contour_menu)
    cc_toolbar_frame.grid(row = 2, columnspan = 2)
    cc_toolbar = NavigationToolbar2Tk(cc_canvas, cc_toolbar_frame)
    contour_location = Entry(cc_contour_menu, font=("Helvetica", 12))
    contour_location.insert(END, "200")
    contour_location.grid(row =3, column = 1, sticky="W")
    
    contour_calculate_btn = Button(cc_contour_menu, text="Calculate Magnitude", bg="thistle", font=("Helvetica", 18), command = lambda: mag_calc(int(contour_location.get()), cc_contour_menu, mag_status))
    contour_calculate_btn.grid(row=4, column =1)

    cc_menu_return = Button(cc_contour_menu, text="Close and continue", font=("Helvetica", 18), bg="tomato", command=lambda: [(cc_contour_menu.destroy(), cc_menu.deiconify())])
    cc_menu_return.grid(row=5, column =1)
def mag_calc(location, cc_contour_menu, mag_status):
    mag2d = np.polyval(deriv, location)
    mag2d = np.format_float_scientific(mag2d, precision = 7)
    if mag_status is None:
        mag_status = Label(cc_contour_menu, text=("At location x=" + str(location) +" there is a magnitude of: "+str(mag2d)), font=("Helvetica", 12))
        mag_status.grid(row=4, column = 0)
    else:
        mag_status.configure(text=("At location x=" + str(location) +" there is a magnitude of: "+str(mag2d)))
        mag_status.update()


def internal_menu():
    global status_path, root, short_dist_btn, calculate_status
    root = Toplevel()
    main_menu.withdraw()
    root.title("Internal Oxidation")
    root.configure(bg="gray69")
    root.minsize(300,300)

    path_btn = Button(root, text="Please select the image you would like to use", font = ("Helvetica", 14), bg="OliveDrab1", command = lambda: select_image("in"))
    path_btn.grid(row = 0, column = 0)
    status_path = Label(root, text="There is no loaded image", font = ("Helvetica", 12))
    status_path.grid(row = 0, column = 1)

    current_dir = os.getcwd()
    worked_dir = current_dir+"/worked-internalcsv/"
    check_dir = Path(worked_dir)
    if check_dir.exists() is False:
        os.mkdir(worked_dir)
    return_btn = Button(root, text="Return to Main Menu", font = ("Helvetica", 14), bg="linen", command = lambda:[root.destroy(), main_menu.deiconify()])
    return_btn.grid(row = 7, columnspan = 2)

def int_calc():
    global int_calc_btn
 #Load Information
    lower_csv = int_lower_csv
    upper_csv = int_upper_csv
    fileinput = os.path.basename(lower_csv)
    filelocation = os.path.dirname(lower_csv)
    ratio = float(lower_csv[-12:-4])
    scale_ratio = float(lower_csv[-13:-12])
    current_dir = os.getcwd()
    lower_thresh_value = str(lower_thresh_old)
    upper_thresh_value = str(upper_thresh_old)
    lower_list_array = lower_list
 #Calculations
    centroid, centroid_distance, circularity, centroid_img, poly_val, inner_limit, inner_limit_x, poly_img, depth_number, total_area, average_pct, segement_traced_img = internal_calculations(path, ratio, lower_thresh_old, upper_thresh_old, lower_crop_val, upper_crop_val, scale_ratio, upper_csv, lower_list_array, lower_csv)
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

 #Save Polynomial Data
    csv_polynomial_summary = filelocation + "/"+fileinput[:-19]+lower_thresh_value+"-"+upper_thresh_value+"-Polynomial-Trace.csv"
    np.savetxt(csv_polynomial_summary, list(zip(inner_limit, inner_limit_x)), fmt="%s", delimiter = ",", header ="Distance, X Location")
    cv2.imwrite((filelocation+"/"+fileinput[:-19]+"-Polynomial.png"), poly_img)
    int_calc_btn.destroy()
    int_calc_btn = None

def internal_calculations(path, ratio, lower_threshold, upper_threshold, crop_lower, crop_upper, scale_ratio, upper_csv, lower_list, lower_csv):
    internal_img = cv2.imread(path, 0)
    internal_img = internal_img[crop_upper:crop_lower, 0:internal_img.shape[1]]
    poly_img = cv2.cvtColor(internal_img, cv2.COLOR_GRAY2BGR)
    internal_img = cv2.inRange(internal_img, lower_threshold, upper_threshold)
    segement_traced_img = cv2.cvtColor(internal_img, cv2.COLOR_GRAY2BGR)
    internal_img_width = internal_img.shape[1]
    micron_slice = ratio

 #Centroid Calculations
    with open(lower_csv) as csvfile:
        c1 = [tuple(map(int, row)) for row in csv.reader(csvfile)]
    with open(upper_csv) as csvfile2:
        c2 = [tuple(map(int, row)) for row in csv.reader(csvfile2)]
    with open(upper_csv) as csvfile2:
        Curve2 = csv.reader(csvfile2, delimiter=",")
        c2_check = np.empty(0)
        for line in Curve2:
            c2_check = np.append(c2_check, line[0])
    c2_check = c2_check.astype(np.float64)

    contours_centroid, _ = cv2.findContours(internal_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    centroid_img = cv2.cvtColor(internal_img, cv2.COLOR_GRAY2BGR)
    centroid = np.array([])
    centroid_distance = np.array([])
    circularity = np.array([])
    lower_list = lower_list.astype(np.int32)
    for i in lower_list:
        moment = cv2.moments(contours_centroid[i])
        if moment["m00"] !=0:
            cx = int(moment["m10"]/moment["m00"])
            cy = int(moment["m01"]/moment["m00"])
            cv2.circle(centroid_img, (cx,cy), img_class.center_circle, (0,0,255), -1)
            cv2.putText(centroid_img,(str(i)), (cx,cy), cv2.FONT_HERSHEY_SIMPLEX, img_class.center_circle, (255,0,0), img_class.center_circle)
            horizontal_range = list(range(cx - img_class.vertical_check, cx+img_class.vertical_check))
            for z in range(len(horizontal_range)):
                if horizontal_range[z] in c2_check:
                    cparray = [(cx, cy)]
                    break
            if len(cparray) != 0:
                c2_edit = [(x, y) for x, y in c2 if x in range(cx - img_class.edge_limit, cx + img_class.edge_limit)]
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
    
 #Polynomial Lower Trace
    lower_x_list = np.array([])
    running_y = np.array([])
    running_x = np.array([])
    for i in range(len(c1)):
        x = c1[i][0]
        if x not in lower_x_list:
            running_y = np.append(running_y, c1[i][1])
            running_x = np.append(running_x, x)
            lower_x_list = np.append(lower_x_list, x)
    average_y = np.mean(running_y)
    sd_y = np.std(running_y)
    poly_x_list = np.array([])
    poly_y_list = np.array([])
    for i in range(len(running_y)):
        if i < (average_y - 2 *sd_y):
            poly_x_list = np.append(poly_x_list, running_x[i])
            poly_y_list = np.append(poly_y_list, (running_y[i]+ratio))

    poly_x_list = poly_x_list.astype(np.float64)
    poly_y_list = poly_y_list.astype(np.float64)
    poly_fit = poly.polyfit(poly_x_list, poly_y_list, 6) #Creates a polynomial fit of 6th degree based on the data
    poly_length = range(internal_img_width)
    poly_val = np.polyval(poly_fit[::-1], poly_length)
    check_list=[]
    inner_limit = np.array([])
    inner_limit_x = np.array([])

    for i in range(int(internal_img_width*.1),int(internal_img_width*.9),10):
        poly_check = list(range(i-img_class.vertical_check, i+img_class.vertical_check))
        for z in range(len(poly_check)):
            if poly_check[z] in c2_check:
                check_list = [(i, poly_val[i])]
                break
        if len(check_list) != 0:
            c2_edit = [(x, y) for x, y in c2 if x in range(int(i - (1.5*img_class.edge_limit)), int(i + (1.5*img_class.edge_limit)))]
            inner_limit = np.append(inner_limit, (distance.cdist(check_list,c2_edit).min(axis=1)/ratio))
            inner_limit_x = np.append(inner_limit_x, i)
        check_list = []

    for i in range(len(c2)):
        cv2.circle(poly_img, (c2[i][0], c2[i][1]), 3, (255,0,255), -1)
    for i in range(int(internal_img_width/10),(len(poly_val)-int(internal_img_width/10))):
        cv2.circle(poly_img, (i, int(poly_val[i])), 3, (255,255,0), -1)
    for i in range(len(poly_x_list)):
        cv2.circle(poly_img, (int(poly_x_list[i]), int((poly_y_list[i])-ratio)), 3, (0,0,255), -1)


    
 #Slices
    list_list_of_areas = []
    list_list_of_pct = []
    for i in range(int(internal_img_width*.1), int(internal_img_width*.9), int((internal_img_width*.8)/100)):
        width_check = list(range(i-img_class.vertical_check, i+img_class.vertical_check))
        minimum_y = 0
        recent_y = None
        for z in range(len(width_check)):    
            if width_check[z] in c2_check:
                initial_x = width_check[z]
                potential_list = np.where(c2_check == initial_x)
                for p in potential_list[0]: #Looks for the lowest point at a given x
                    if c2[p][1] > minimum_y:
                        minimum_y = c2[p][1]
                break
        list_of_areas = []
        list_of_pct = []
        if minimum_y != 0 or recent_y is not None:
            if minimum_y == 0:
                minimum_y = recent_y
            for row in range(int((poly_val[i]-minimum_y)/micron_slice)):
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
                cv2.putText(segement_traced_img, ("_"), (i, int(minimum_y+(row*micron_slice))), cv2.FONT_HERSHEY_SIMPLEX, (img_class.label_text+2), (0,255,255),(img_class.center_circle+3))
            list_list_of_areas.append(list_of_areas)
            list_list_of_pct.append(list_of_pct)
            recent_y = minimum_y
        else:
            list_list_of_areas.append([np.nan])
            list_list_of_pct.append([np.nan])
    n = len(max(list_list_of_areas, key=len))
    matrix_areas = [x + [np.nan]*(n-len(x)) for x in list_list_of_areas]
    matrix_pct = [x + [np.nan]*(n-len(x)) for x in list_list_of_pct]
    total_area = np.nansum(matrix_areas, axis=0)
    average_pct = np.nanmean(matrix_pct, axis=0)
    depth_number = np.array([])
    for i in range(len(average_pct)):
        depth_number = np.append(depth_number, i)
 #Returns
    return centroid, centroid_distance, circularity, centroid_img, poly_val, inner_limit, inner_limit_x, poly_img, depth_number, total_area, average_pct, segement_traced_img

main_menu = Tk()
main_menu.minsize(300,300)
main_menu.title("Main Menu")
main_menu.configure(bg="gray69")

Label(main_menu, text = "Please select the following menus to use", font = ("Helvetica", 14)).grid(row = 0, columnspan = 2)

shortest_distance_menu_btn = Button(main_menu, text="Calculate Shortest Distance/Prepare Data", font = ("Helvetica", 14), bg="skyblue", command = shortest_distance_menu)
shortest_distance_menu_btn.grid(row = 1, column = 0)
Label(main_menu, text="This will let you calculate the shortest distance between select contours\nor prepare samples for the concavity calculator", font = ("Helvetica", 12)).grid(row =1, column = 1, sticky="W")

concavity_menu_btn = Button(main_menu, text="Concavity Calculations", font = ("Helvetica", 14), bg="slate blue", command = concavity_menu)
concavity_menu_btn.grid(row = 2, column = 0)
Label(main_menu, text="This will let you find concavity of the lower line. \nCompares thicknesses at concave and concave regions", font = ("Helvetica", 12)).grid(row=2, column = 1, sticky="W")

internal_oxidation_menu_btn = Button(main_menu, text="Internal Oxidation", font= ("Helvetica", 14), bg="purple2", command = internal_menu)
internal_oxidation_menu_btn.grid(row=3, column=0)
Label(main_menu, text="Prepare CSVs to measure internal oxidation\nAlso measures continuity in slices", font = ("Helvetica", 12)).grid(row=3, column=1, sticky="W")

exit_btn = Button(main_menu, text="Exit Program", font= ("Helvetica", 14), bg="tomato", command = main_menu.destroy)
exit_btn.grid(row=4, column=0)

main_menu.mainloop()
