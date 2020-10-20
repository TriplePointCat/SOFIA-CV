# ShortestDistanceCalculatorStandard Operating Procedure: AutoTracer

Requirements:
python3 code editor (64bit of your OS, if applicable): https://www.anaconda.com/products/individual 

Tesseract (64bit Windows, if applicable): https://github.com/UB-Mannheim/tesseract/wiki 
Tesseact (Non-Windows): https://github.com/tesseract-ocr/tessdoc/blob/master/Home.md 
ImageJ: https://imagej.nih.gov/ij/download.html 

Setting up Python
Run the anaconda installer

    1. Run the installer and keep pressing Next or Agree until you can install
    2. Run Anaconda Navigator
    3. In the Anaconda Navigator menu install VS Code
    4. Launch VS Code
    5. Install the following one at a time by copying the line and pasting it in the terminal at the bottom of the screen
pip install imutils
pip install pytesseract
pip install opencv-python
pip install pathlib
pip install shapely
    6. After installing the modules, restart VS Code

Setting up Tesseract
    1. Run the Tesseract installer and press Next or Agree until the installation is finished
        ◦ Make sure that it is installing to C:\Program Files\Tesseract-OCR

Using the program

    1. Open AutoTracerV2.py in VS Code. You should see code
    2. Press the green triangle in the top right corner to run the script
    3. When you open the scrip you should see the following. If you get any errors make sure you have the required modules installed
    4. Click the green button to select an image to use
    5. Press the teal button to crop the image
    6. A new menu will open to let you adjust the crop
    7. Adjust the numbers in the entry box next to “Lower Height” and “Upper Height” to adjust the window until you have isolated the feature of the image you want (see picture below). There are numbers on the side to help you crop it.
    8. When you have a small window containing the feature you want press “Close and Continue”. You will see a new option on the main menu titled “Adjust Thresholds”. Press than button.
    9. On the new window created you can adjust thresholds (gray values of the image). Adjust the numbers and press the “Update Threshold” button until you have the isolated the feature you want. The image in the center will show you the most recent settings and the image on the right will be the previous settings. 
    10. When you get the thresholds you want you can press the “Add Most Recent Threshold” button to save those into a list if you require multiple thresholds to isolate the feature you want. Otherwise you most recent threshold settings will be used.
    11. When you press “Close and Continue” you will see a new button on the main menu titled “Select Edges”. 
    12. Select the Threshold settings that you want by pressing the “Add Contours w/Threshold…” button. A new menu will open that will allow you select contours.
    13. The top image shows the thresholded image with contours labeled. Enter the numbers that you want into the text box and select an option on how to add the contour. 
        1. Add Contour as Lower will add the bottom half of the image to a list used to represent the bottom of the feature (such as a scale)
        2. Add Contour as Upper will add the top half of the image to a list used to represent the top of the feature (such as a scale)
        3. Add Lower as Upper will add the bottom half of the image to a list used to represent the bottom of the feature (intended for complicated scales or if using multiple thresholds)
        4. Add Bulk Lower requires contours that have been defined as upper boundaries. It will automatically add the lower half of all contours below the previously selected upper boundary contours. (Intended for complicated scales)
        5. Add Bulk Lower to Upper requires contours that have been defined as lower boundaries. It will automatically add the lower half of all contours above the previously selected upper boundary contours. (Intended for complicated scales)
    14. When you press one of the buttons the lower image will update showing the data you have selected so far. Yellow will show the lower boundary and magenta will show the upper boundary. When contours are selected through a non-bulk method an undo button will be added. Pressing the undo button will remove the most recently added data.
    15. When you have added data to define the upper and lower boundaries a button to exit the menu labeled “Close and Continue” will be created. When you have added all of the contours that you want you can press that button to continue the process. (Note: If you are using multiple thresholds repeat steps 12-14 until satisfied)
    16. Press the “Close” button on the page that lists thresholds to continue
    17. On the main menu a new button will be available labeled “Save CSVs”. Press this button to automatically save all the contour data you selected. If you press the button and a text box is created to the right of the button saying ENTER SCALE RATIO refer to Using ImageJ in the following section 
    18. When data has finished saving all of the buttons besides the image selection button will be removed and an option to “Calculate Shortest Distance” will be created
    19. You can repeat steps 1-17 as many times as you would like before pressing “Calculate Shortest Distance”. When you press that button it will perform calculations on the CSVs you have created. The calculations will have finished when the “Calculate Shortest Distance” button disappears. 
    20. The results from the calculations can be found in a spreadsheet titled “Summary.csv” found in the same folder that “AutoTracerV2.py” is located in. Additional information can be found in a folder titled “workedcsv” in the same folder as “Summary.csv” that will contain the CSVs used as well as a CSV that contains all of the data points used and the thickness calculated at those points. A box and whisker graph will also be generated to visually see the data.

Using ImageJ

    1. Download and open ImageJ
    2. Open the SEM image in ImageJ by draggin the image from File Explorer into ImageJ or by File>Open
    3. Select the straight-line tool
    4. Drag across the scalebar in the image. Pro-tip: Use Shift to make lines at multiples of 45°. Also, use the scroll wheel to zoom into the picture to be more accurate with the line.
    5. Go to Analyze>Set Scale
    6. Change the “Known Distance” to the dimension on the scale bar and the “Unit of length to the units” and click OK. Write down the scale in pixels per distance.
    7. Use this scale ratio when the Text Entry box appears when saving the CSVs
