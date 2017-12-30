# https://www.pyimagesearch.com/2014/09/15/python-compare-two-images/

# import the necessary packages
from skimage.measure import compare_ssim as ssim
import numpy as np
import cv2
import os


def is_blurry(filename, threshold=100):
    image = read_picture(filename)
    if image is None: return False
    return variance_of_laplacian(image) < threshold


def are_similar(filenameA, filenameB, threshold=0.9):
    imageA = read_picture(filenameA, 100)
    imageB = read_picture(filenameB, 100)
    if imageA is None or imageB is None: return False
    s = ssim(imageA, imageB)
    if threshold < s:
        print(os.path.basename(filenameA), os.path.basename(filenameB), s)
    return threshold < s


def variance_of_laplacian(image):
    # compute the Laplacian of the image and then return the focus
    # measure, which is simply the variance of the Laplacian
    # the lower the more blurry, example threshold=100
    return cv2.Laplacian(image, cv2.CV_64F).var()


def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])

    # return the MSE, the lower the error, the more "similar"
    # the two images are
    return err


def compare_images(directory, nameA, nameB):
    # compute the mean squared error and structural similarity
    # index for the images
    imageA = read_picture(directory + "\\" + nameA)
    imageB = read_picture(directory + "\\" + nameB)
    m = mse(imageA, imageB)
    s = ssim(imageA, imageB)
    print("m:", m)
    print("s", s)


def read_picture(name="", xscale=500):
    picture = cv2.imread(name)
    if picture is None or not picture.data:
        print("failed to load", name)
        return
    picture = cv2.resize(picture, (xscale, int(xscale * 2. / 3.)))
    # convert the images to grayscale
    picture = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY)
    return picture

# In [10]: compare.compare_images("F:\\Bilder\\bearbeitung\\HDR","L17-0831_01_HDRT_SUN2_Sunset.jpg","L17-0831_02_HDRT_
#    ...: SUN2_Sunset.jpg")
# m: 158.948441558
# s 0.627520235931
#
# In [11]: compare.compare_images("F:\\Bilder\\bearbeitung\\testcomp","L17-0828_02B1_Wolken.JPG","L17-0828_02B2_Wolken
#    ...: .JPG")
# m: 1050.44272727
# s 0.866533901056
#
# In [12]: compare.compare_images("F:\\Bilder\\bearbeitung\\testcomp","L17-0828_02B1_Wolken.JPG","H171006_Butter.JPG")
#    ...:
# m: 5565.24084416
# s 0.149896912847
#
# In [13]: compare.compare_images("F:\\Bilder\\bearbeitung\\testcomp","Kisa_01_01.jpg","Kisa_40_01.jpg")
# m: 0.131948051948
# s 0.999741746826
#
# In [14]: compare.compare_images("F:\\Bilder\\bearbeitung\\testcomp","Kisa_01_01.jpg","Kisa_01_02.jpg")
# m: 1945.7161039
# s 0.389233502472
#
# In [15]: compare.compare_images("F:\\Bilder\\bearbeitung\\testcomp","Kisa_01_01.jpg","Kisa_04_15.jpg")
# m: 6661.06090909
# s 0.0779526264583
