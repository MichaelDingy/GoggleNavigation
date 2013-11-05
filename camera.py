from VideoCapture import Device
from PIL import Image
import numpy as np

class Camera():
    def __init__(self, dev=0):
        try:
            self.cam = Device(dev)
        except Exception as e: 
            print e
            self.cam = None
    
    def is_open(self):
        if self.cam:
            return True
        else:
            return False

    def read(self):
        frame = self.cam.getImage().convert('RGB')
        frame = np.array(frame)
        # Convert RGB to BGR 
        cv_img = frame[:, :, ::-1].copy()
        return cv_img

def test():
    import cv2

    cam1 = Camera(0)
    cam2 = Camera(1)

    cv2.namedWindow('pc', cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('usb', cv2.WINDOW_AUTOSIZE)

    while True:
        img1 = cam1.read()
        img2 = cam2.read()
        cv2.imshow('pc', img1)
        cv2.imshow('usb', img2)
        if cv2.waitKey(30) == 27:
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    test()
