# https://www.pyimagesearch.com/2014/09/15/python-compare-two-images/

import os

import cv2
import numpy as np
# import the necessary packages
from skimage.measure import compare_ssim as ssim

__all__ = ["is_blurry", "are_similar"]

def is_blurry(directory, filename, threshold=100):
    image = read_picture(directory, filename)
    if image is None: return False
    return variance_of_laplacian(image) < threshold


def are_similar(dirA, filenameA, dirB, filenameB, threshold=0.9):
    imageA = read_picture(dirA, filenameA, 100)
    imageB = read_picture(dirB, filenameB, 100)
    if imageA is None or imageB is None: return False
    s = ssim(imageA, imageB)
    if threshold < s:
        print(filenameA, filenameB, s)
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
    imageA = read_picture(directory, nameA)
    imageB = read_picture(directory, nameB)
    m = mse(imageA, imageB)
    s = ssim(imageA, imageB)
    print("m:", m)
    print("s", s)


def read_picture(directory, name, xscale=500):
    fullname = os.path.join(directory, name)
    picture = cv2.imread(fullname)
    if picture is None or not picture.data:
        print("failed to load", fullname)
        return
    picture = cv2.resize(picture, (xscale, int(xscale * 2. / 3.)))
    # convert the images to grayscale
    picture = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY)
    return picture
