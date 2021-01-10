from skimage.metrics import structural_similarity
from colorama import init, Fore, Back, Style
import imutils
import cv2
import time
from tkinter import filedialog
import tkinter as tk
import os
import numpy as np
import sys
import img2pdf
from PIL import Image
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)

init()

preDone = 'N'
postDone = 'N'

root = tk.Tk()
root.geometry("400x80+500+50")
root.withdraw()

# Validate the input fie format, should be .pdf
def fileValidation(fileName):
    if not(fileName.lower().endswith('.pdf')):
        print(Fore.RED + 'File format is not pdf,retry')
        return 'N'
    return 'Y'

# Saving the images in JPEG format
def saveImages(ppmImage, folder):
    count = 1
    for image in ppmImage:
        fileName = folder+str(count) +'.jpg'
        image.save(fileName, 'JPEG')
        count += 1

while preDone=='N':
    print(Fore.RED + 'Provide an older version of the pdf file - ')
    time.sleep(.50)
    preFile = filedialog.askopenfilename()
    print(Fore.GREEN + preFile)
    preDone = fileValidation(preFile)

while postDone == 'N':
    print(Fore.RED + 'Provide a newer version of the pdf file - ')
    time.sleep(.50)
    postFile =filedialog.askopenfilename()
    print(Fore.GREEN + postFile)
    postDone = fileValidation(postFile)

Style.RESET_ALL
preFolder = './/temp//images//Pre//'
postFolder = './/temp/images//Post//'
tempOut = './/temp//output//'
reportsFolder = './/reports//'
outFileName = ((preFile.split('.')[0]).split('/')[-1]).split('.')[0]+ '_report.pdf'
images_from_pre_path = convert_from_path(preFile, poppler_path='.//poppler//poppler-0.68.0//bin', output_folder='.//temp//ppm')
saveImages(images_from_pre_path, preFolder)
images_from_post_path = convert_from_path(postFile, poppler_path='.//poppler//poppler-0.68.0//bin', output_folder='.//temp//ppm')
saveImages(images_from_post_path, postFolder)

preImages = os.listdir(preFolder)
postImages = os.listdir(postFolder)

extraFiles = list(list(set(preImages)-set(postImages)))
if(len(extraFiles) > 0):
    print(Fore.RED + 'There are %s extra pages in pre sample which will be ignored from comparison process' %len(extraFiles))
    for item in extraFiles:
        print(Fore.RED + 'Ignoring page number %s' % item.split('.')[0])
extraFiles = list(list(set(postImages)-set(preImages)))
if(len(extraFiles) > 0):
    print(Fore.RED + 'There are %s extra pages in post sample which will be ignored from comparison process' % len(extraFiles))
    for item in extraFiles:
        print(Fore.RED + 'Ignoring page number %s' % item.split('.')[0])

commonFiles = list(list(set(postImages).intersection(set(preImages))))

# percentage to resize the image
resize_scale_percent = 50

diff_found = 'N'

print(Fore.YELLOW + 'Starting comparison process')
for item in commonFiles:
    preImage = cv2.imread(preFolder+item, cv2.IMREAD_UNCHANGED)
    postImage = cv2.imread(postFolder+item, cv2.IMREAD_UNCHANGED)
    # Get new width and height based upon the resize scale
    width = int(preImage.shape[1] * resize_scale_percent / 100)
    height = int(postImage.shape[0] * resize_scale_percent / 100)
    # Convert images in greyscale for compariosn
    grayPre = cv2.cvtColor(preImage, cv2.COLOR_BGR2GRAY)
    grayPost = cv2.cvtColor(postImage, cv2.COLOR_BGR2GRAY)
    # Calculate the difference between the images
    (score, diff) = structural_similarity(grayPre, grayPost, full=True)
    diff = (diff * 255).astype("uint8")
    print(Fore.YELLOW + "SSIM: {}".format(score))
    if float(score) != 1.0:
        diff_found = 'Y'
        print(Fore.RED + 'Difference found')
    thresh = cv2.threshold(diff, 0, 255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for c in cnts:
    # compute the bounding box of the contour and then draw the
    # bounding box on both input images to represent where the two
    # images differ
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(preImage, (x, y), (x + w, y + h), (0, 165, 255), 3)
        cv2.rectangle(postImage, (x, y), (x + w, y + h), (0, 165, 255), 3)
    # resize the image
    img_pre = cv2.resize(preImage, (width, height))
    # cv2.imshow("Original", img)
    img_post = cv2.resize(postImage, (width, height))
    # Combine original and modified image side by side
    vis = np.concatenate((img_pre,img_post), axis=1)

    # cv2.imshow("Modified", img)
    cv2.imwrite(tempOut+item, vis)
    # cv2.imshow("Diff", diff)
    # cv2.imshow("Thresh", thresh)
    # cv2.waitKey(0)


if diff_found == 'Y':
    print(Fore.YELLOW + 'Difference found for %s' % preFile)
    print(Fore.YELLOW + 'Generating comparison file')
    with open(outFileName, "wb") as f:
        imgs = []
        lst = os.listdir(tempOut)
        # lst.sort(key=int)
        for fname in lst:
            if not fname.endswith(".jpg"):
                continue
            path = os.path.join(tempOut, fname)
            if os.path.isdir(path):
                continue
            imgs.append(path)
        f.write(img2pdf.convert(imgs))
        f.close()
        os.replace(outFileName, reportsFolder+outFileName)
        print(Fore.YELLOW + 'Comparison file successfully created, please check reports folder!')
        print(Fore.YELLOW + 'Comparison process completed')       
else:
    print(Fore.YELLOW + 'No difference found')
    print(Fore.YELLOW + 'Comparison process completed')
