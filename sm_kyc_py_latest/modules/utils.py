import os

import cv2
from google.cloud import vision
from google.cloud.vision import types

import numpy as np



class GcpOcrException(Exception):
    pass


class GcpOcr:
    def __init__(self, keypath):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = keypath
        self.client = vision.ImageAnnotatorClient()

    def ocrFromFile(self, imgPath):
        with open(imgPath, 'rb') as image_file:
            content = image_file.read()
        image = vision.types.Image(content=content)
        return  self.ocr(image)


    def ocr(self, image):
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        if len(texts) < 1:
            return ""
        label = texts[0].description
        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))
        return label

    def ocrFromCv2(self, imgPath):
        img = cv2.imread(imgPath)
        imgStr = cv2.imencode('.png', img)[1].tostring()
        image = vision.types.Image(content=imgStr)
        return self.ocr(image)

    def ocrFromEncoded(self, encodedImg):
        img = cv2.imdecode(np.fromstring(encodedImg,dtype='uint8'),cv2.IMREAD_UNCHANGED)
        imgStr = cv2.imencode('.png', img)[1].tostring()
        image = vision.types.Image(content=imgStr)
        return self.ocr(image)


