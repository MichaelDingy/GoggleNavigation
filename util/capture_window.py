import win32gui, win32ui
from PIL import Image

class WindowMgr:
    """
        Capture a window without margins in read-time.
        Functions:
            list_windows:      print all visible windows
            select_window:     select the window need to be captured
            capture_window:    capture window and return a PIL image (BGR)
            save_window:       save the current window image
    """

    def __init__(self):
        self.wins = []
        win32gui.EnumWindows(self._callback, None)
        self.hwnd = self.select_window()

        self.wDc = win32gui.GetWindowDC(self.hwnd)
        self.dcObj = win32ui.CreateDCFromHandle(self.wDc)
        self.cDC = self.dcObj.CreateCompatibleDC()

        _, _, self.w, self.h = win32gui.GetClientRect(self.hwnd)
        self.h, self.w = self.h - 1, self.w - 1

        self.dataBitMap = win32ui.CreateBitmap()
        self.dataBitMap.CreateCompatibleBitmap(self.dcObj, self.w, self.h)

        self.cDC.SelectObject(self.dataBitMap)

    def _callback(self, hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd): 
            self.wins.append((hwnd, win32gui.GetWindowText(hwnd)))

    def list_windows(self):
        for idx, win in enumerate(self.wins):
            print idx, ': ', win[1]

    def select_window(self):
        self.list_windows()
        while True:
            try:
                idx = int(raw_input('Please select the window you want to capture: '))
                break
            except ValueError:
                print 'Input error'
        return self.wins[idx][0]

    def capture_window(self):
        # calculate top and left margins 
        l, t, r, b = win32gui.GetWindowRect(self.hwnd)
        mlc, mtc = win32gui.ScreenToClient(self.hwnd, (l, t))
        ml, mt = abs(mlc), abs(mtc)

        # win32con.SRCCOPY == 13369376
        self.cDC.BitBlt((0, 0), (self.w, self.h) , self.dcObj, (ml, mt), 13369376)

        bmpinfo = self.dataBitMap.GetInfo()
        bmpstr = self.dataBitMap.GetBitmapBits(True)
        # default mode is BGRX, so converting it to RGB will get a BGR-mode image.
        img = Image.frombuffer('RGBX', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'RGBX', 0, 1).convert('RGB')
        return img

    def save_window(self, filename):
        img = self.capture_window()
        # when saving the image, we need to convert it to RBG-mode
        b, g, r = img.split()
        Image.merge('RGB', (r, g, b)).save(filename)

if __name__ == '__main__':
    import cv2
    import numpy as np

    wins = WindowMgr()
    wins.save_window('capture.bmp')

    while True:
        img = wins.capture_window()
        img = np.array(img)
        cv2.imshow('t', img)
        if cv2.waitKey(30) == 27:
            break

    cv2.destroyAllWindows()
