import vidcap
from PIL import Image
import numpy as np
import cv2

class Camera():
    """
        Camera device using DirectShow
        depencency: VideoCapture http://videocapture.sourceforge.net/
    """

    def __init__(self, devnum=0):
        try:
            self.dev = vidcap.new_Dev(devnum, 0)
            self.name = self.dev.getdisplayname()
        except Exception as e:
            self.dev = None
            self.name = 'None'

    def is_open(self):
        if self.dev:
            return True
        else:
            return False

    def _get_buffer(self):
        return self.dev.getbuffer()
    
    def get_image(self, mode=0):
        """
            get image from camera, 
            in some cases, image size is not 640X480 and there exist black margins,
            so we should resize and crop it.
                mode: 0  color image
                      1  grayscale iamge
        """

        if not self.is_open():
            raise IOError, 'camera is not open'

        buffer, width, height = self._get_buffer()
        if buffer:
            img = Image.fromstring('RGB', (width, height), buffer, 'raw', 'RGB', 0, -1)
            cv_img = np.array(img)

            if mode:
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            if height != 480:
                r = 480.0 / 768
                cv_img = cv2.resize(cv_img, (0, 0), fx=r, fy=r)
                h, w = cv_img.shape[:2]
                new_img = cv_img[:, (w - 640) / 2:(w - 640) / 2 + 640]
                return new_img
            else:
                return cv_img

def test():
    cam = Camera(0)
    if not cam.is_open():
        print 'cannot open cam'
        return

    cv2.namedWindow('camera', cv2.WINDOW_AUTOSIZE)

    while True:
        img = cam.get_image(1)
        cv2.imshow('camera', img)
        c = cv2.waitKey(30)
        if c == ord('s'):
            cv2.imwrite('template.jpg', img)
        elif c == 27: 
            break 
    cv2.destroyAllWindows()

if __name__ == '__main__':
    test()
