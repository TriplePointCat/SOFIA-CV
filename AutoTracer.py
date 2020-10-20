from tkinter import *
import os
import sys
import imutils
import pytesseract
from PIL import Image
from PIL import ImageTk
from tkinter import filedialog
import cv2
import os.path

#Allows the user to load an image and quickly crop, threshold, and detect edges to isolate lines for the purpose
#of measuring scale thicknesses.
#Created by Padraig Stack on April 16, 2020
#Last modified May 12, 2020

pytesseract.pytesseract.tesseract_cmd = "C:\Program Files\Tesseract-OCR\\tesseract.exe" #Location of the text reading software


panelA = panelB = panelC = panelD = path = cbtn = cropmenu = directory = filename = OrigImg = lowcrop = highcrop = crop = cropclose = threshbtn = threshmenu = None
lowthresh = highthresh = picturedescription = lowt = hight = oldlt = oldht = oldimg = threshclose = edgebtn = thresh= None
def resize(Original, sizepercentage): #Resizes an opencv image array
    width = int(Original.shape[1] * sizepercentage / 100)
    height = int(Original.shape[0] * sizepercentage / 100)
    dsize = (width, height)
    return cv2.resize(Original, dsize)

def select_image():
    global path, cbtn, directory, filename, OrigImg
    path = filedialog.askopenfilename()
    if len(path) > 0:
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        OrigImg = cv2.imread(path, 0)
        statusp.configure(text=("The current loaded image is: " + filename), font=("Helvetica", 10))
        statusp.update()
        if cbtn is None:
            cbtn = Button(root, text="Crop the image", bg="PaleTurquoise1",  font=("Helvetica", 14), command = crop_image)
            cbtn.pack(fill="both", padx=10, pady=10)
    else:
        statusp.configure(text="You have not selected a new image, please select one", font=("Helvetica", 10))
        statusp.update()

def crop_image():
    global cropmenu, lowcrop, highcrop, cropclose, panelA
    if cropmenu is not None:
        cropmenu.destroy()
    cropclose = None
    panelA = None
    cropmenu = Toplevel()
    cropmenu.title("Cropping Menu")
    cropmenu.configure(bg="gray69")
    cropmenu.minsize(300,300)

    Label(cropmenu, text=("The image you have loaded is "  +str(OrigImg.shape[0]) +" pixels tall"
    "\nAdjust the parameters until the entire scale is in the frame"), bg="thistle1", font=("Helvetica", 12)).pack(padx=10, pady=10)

    Label(cropmenu, text="Please enter the lower crop height", font=("Helvetica", 10)).pack(padx=10, pady=10)
    lowcrop = Entry(cropmenu, font=("Helvetica", 10))
    lowcrop.insert(END, "3706")
    lowcrop.pack()

    Label(cropmenu, text="Please enter the upper crop height", font=("Helvetica", 10)).pack(padx=10, pady=10)
    highcrop = Entry(cropmenu, font=("Helvetica", 10))
    highcrop.insert(END, "4286")
    highcrop.pack()

    cropupbtn = Button(cropmenu, text="Update Crop", bg="gold2", font=("Helvetica", 12), command = crop_update)
    cropupbtn.pack(fill="both", padx=10, pady=10)

def crop_update():
    global panelA, crop, cropclose, threshbtn
    lowcrop2 = int(float(OrigImg.shape[0]) - float(lowcrop.get()))
    highcrop2 = int(float(OrigImg.shape[0]) - float(highcrop.get()))

    crop = OrigImg[highcrop2:lowcrop2, 0:9999]
    crop2 = resize(crop, 20)
    crop2 = Image.fromarray(crop2)
    crop2 = ImageTk.PhotoImage(crop2)

    if panelA is None:
        panelA = Label(cropmenu, text="Cropped", image = crop2)
        panelA.image = crop2
        panelA.pack(padx=10, pady=10)
    else:
        panelA.configure(image=crop2)
        panelA.image = crop2

    if cropclose is None:
        cropclose = Button(cropmenu, text="Close and Continue", bg = "tomato", font=("Helvetica", 12), command = cropmenu.destroy)
        cropclose.pack(fill="both", padx=10, pady=10)
    
    if threshbtn is None:
        threshbtn = Button(root, text="Adjust Thresholds", bg="DeepSkyBlue2", font=("Helvetica", 14), command = thresh_image)
        threshbtn.pack(fill="both", padx=10, pady=10)

def thresh_image():
    global threshmenu, lowthresh, highthresh, panelB, panelC, panelD, picturedescription, threshclose, oldht, oldlt
    if threshmenu is not None:
        threshmenu.destroy()
    panelB = panelC = panelD = threshclose = oldht = oldlt = None
    threshmenu = Toplevel()
    threshmenu.title("Threshold Menu")
    threshmenu.configure(bg="gray69")
    threshmenu.minsize(300,300)

    Label(threshmenu, text="Adjust the parameters until the desired section of the image is white\nA blur will be applied do not worry about dots in the center", bg="cornsilk2", font=("Helvetica", 12)).pack(padx=10, pady=10)

    Label(threshmenu, text="Please enter the lower threshold value (0-255)", font=("Helvetica", 10)).pack(padx=10, pady=10)
    lowthresh = Entry(threshmenu, font=("Helvetica", 10))
    lowthresh.insert(END, "60")
    lowthresh.pack()

    Label(threshmenu, text="Please enter the higher threshold value (0-255)", font=("Helvetica", 10)).pack(padx=10, pady=10)
    highthresh = Entry(threshmenu, font=("Helvetica", 10))
    highthresh.insert(END, "195")
    highthresh.pack()

    threshupbtn = Button(threshmenu, text="Update Threshold", bg="OliveDrab1", font=("Helvetica", 12), command = thresh_update)
    threshupbtn.pack(fill="both", padx=10, pady=10)

    picturedescription = Label(threshmenu, text="The following image is the cropped image with a reduced width", font=("Helvetica", 10))
    picturedescription.pack(padx=10, pady=10)

    crop3 = crop[0:9999, 0:1000]
    crop3 = resize(crop3, 50)
    crop3 = Image.fromarray(crop3)
    crop3 = ImageTk.PhotoImage(crop3)
    panelB = Label(threshmenu, text="Original", image= crop3)
    panelB.image = crop3
    panelB.pack(side = "left", padx=10, pady=10)

def thresh_update():
    global lowt, hight, oldlt, oldht, panelC, panelD, oldimg, threshclose, edgebtn, thresh
    lowt = int(lowthresh.get())
    hight = int(highthresh.get())
    
    thresh = cv2.inRange(crop, lowt, hight)
    thresh2 = thresh[0:9999, 0:1000]
    thresh2 = resize(thresh2, 50)
    thresh2 = Image.fromarray(thresh2)
    thresh2 = ImageTk.PhotoImage(thresh2)
    if panelC is None:
        panelC = Label(threshmenu, text="Threshold", image = thresh2)
        panelC.image = thresh2
        panelC.pack(side="left", padx=10, pady=10)
    else:
        panelC.configure(image=thresh2)
        panelC.image = thresh2
    if oldlt is not None:
        if panelD is None:
            panelD = Label(threshmenu, text="Previous Image", image = oldimg)
            panelD.image = oldimg
            panelD.pack(side="left", padx=10, pady=10)
        else:
            panelD.configure(image=oldimg)
            panelD.image = oldimg
        picturedescription.configure(text=("The first image is the original\nThe second image is thresholded at "+ str(lowt) +"-" +str(hight)
        +"\n The third image is thresholded at " +str(oldlt)+"-"+str(oldht)), font=("Helvetica", 10))

    else:
        picturedescription.configure(text=("The first image is the original\nThe second image is thresholded at "+ str(lowt) +"-" +str(hight)), font=("Helvetica", 10))
    oldlt = lowt
    oldht = hight
    oldimg = thresh2

    if threshclose is None:
        threshclose = Button(threshmenu, text="Close and Continue", bg= "LightSalmon2", font=("Helventica", 12), command = threshmenu.destroy)
        threshclose.pack(anchor = SE, side = "right", fill="both", padx=10, pady=10)
    
    if edgebtn is None:
        edgebtn = Button(root, text="Calculate Edges", bg="MediumOrchid2", font=("Helvetica", 14), command = edge_calc)
        edgebtn.pack(fill="both", padx=10, pady=10)

def edge_calc():
    global filename, directory
    if ".tif" in filename or ".jpg" in filename or ".png" in filename:
        filename2 = filename[:-4]
    if ".tiff" in filename or ".jpeg" in filename:
        filename2 = filename[:-5] 
    filename2 = (filename2 + "-" + str(lowt) +"-" + str(hight))
    filename2 = ((directory+"/"+filename2))
    edim = cv2.medianBlur(thresh, 9)
    edim = cv2.Canny(edim, 50, 150)
    
    edimorig = edim
    edimorig = Image.fromarray(edimorig)
    edimorig.save(filename2+"-edges.tif")
    
    edim = ImageCleanup(edim)
    edim = Image.fromarray(edim)
    edim.save(filename2+"-FilteredEdges.tif")
    
    Label(root, text=("The image has been save in the folder where the original image was located. It is saved as: " + filename2
    +"\nIf you want to use another image you do not have to restart the program, just restart the procedure"), font=("Helvetica", 8)).pack()

def ImageCleanup(unclean):
    #Removes non-border edges to help isolate scale borders
    contours, hierarchy = cv2.findContours(unclean, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(contours)):
        if cv2.arcLength(contours[i], False) < 500:
            cv2.drawContours(unclean, contours, i, 0, -1)
    return unclean

def ScaleReader(path):
    img = cv2.imread(path)
    height, width = img.shape
    if height == 5696 or height> 8193:
        img = img[(height-1650):(height-900), 4000:6000]
    elif width > 5000 and height > 5000:
        img = img[(height-900):(height-300), 4000:6000]
    else:
        print("This image size has not been seen before")
        print("Width: "+width)
        print("Height: "+height)
        sys.exit()
    img = cv2.inRange(img, 240, 255)
    text = pytesseract.image_to_string(img,lang = "eng", config = '--psm 3 --oem 3 -c tessedit_char_whitelist=0123456789oO ') #tessedit_char_blacklist = abcdefghijklmnopqrstuvwxyz
    if "o" in text:
        text = text.replace("o", "5")
    if "O" in text:
        text = text.replace("O", "0")
    text = int(text)

    height, width = img.shape
    img = img[0:(height-300), 0:2000]
    cnts = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    cnts = imutils.grab_contours(cnts)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    c = max(cnts, key=cv2.contourArea)
    leftmost = tuple(c[c[:,:,0].argmin()][0])
    rightmost = tuple(c[c:,:,0].argmin()[0])
    distance = int(rightmost[0])-int(leftmost[0]) - 1
    ratio = distance / text
    return ratio

root = Tk()
root.minsize(300,300)
root.title("Auto Tracer")
root.configure(bg="gray69")

pbtn = Button(root, text="Please select the image you would like to use", bg = "SpringGreen2", font=("Helvetica", 14), command = select_image)
pbtn.pack(fill="both", padx=10, pady=10)
statusp = Label(root, text="There is no loaded image", font=("Helvetica", 10))
statusp.pack()

root.mainloop()