import win32gui, win32ui
from PIL import Image, ImageTk
import Tkinter as tk
import ttk


class WindowCapture:
    """Capture a window withor without margins in read-time.
    Functions:
        get_wins: enumerate all available windows
        select_win: select the window you want to capture in console
        set_win (init_capture): set the window and create resources
        capture_window: capture window and return PIL image (RGB)
                mode: 0 without margins
                      1 with margins
        save_winsow: save captured window image
                mode: 0 without margins
                      1 with margins
    """

    def __init__(self):
        self.wins = []
        self.get_wins()

    def _callback(self, hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd): 
            name = win32gui.GetWindowText(hwnd)
            if name:
                self.wins.append((hwnd, name))

    def get_wins(self):
        self.wins = []
        win32gui.EnumWindows(self._callback, None)

    def select_win(self):
        for idx, win in enumerate(self.wins):
            print idx, ': ', win[1]
        while True:
            try:
                idx = int(raw_input(
                    'Please select the window you want to capture: '))
                break
            except ValueError:
                print 'Input error'
        self.set_win(idx)
        
    def set_win(self, idx): 
        self._init_capture(self.wins[idx][0])

    def _init_capture(self, hwnd): 
        self.hwnd = hwnd
        win32gui.SetForegroundWindow(hwnd)
        self.wDc = win32gui.GetWindowDC(self.hwnd)
        self.dcObj = win32ui.CreateDCFromHandle(self.wDc)
        self.cDC = self.dcObj.CreateCompatibleDC()
        self.dataBitMap = win32ui.CreateBitmap()

    def capture_window(self, mode=0):
        if not self.hwnd:
            return None

        l, t, r, b = win32gui.GetWindowRect(self.hwnd)
        if mode:
            w, h = r - l, b - t
            self.dataBitMap.CreateCompatibleBitmap(self.dcObj, w, h)
            self.cDC.SelectObject(self.dataBitMap)

            # win32con.SRCCOPY == 13369376
            self.cDC.BitBlt((0, 0), (w, h), self.dcObj, (0, 0), 13369376)
        else:
            _, _, w, h = win32gui.GetClientRect(self.hwnd)
            w, h = w - 1, h - 1
            self.dataBitMap.CreateCompatibleBitmap(self.dcObj, w, h)
            self.cDC.SelectObject(self.dataBitMap)

            # calculate top and left margins 
            mlc, mtc = win32gui.ScreenToClient(self.hwnd, (l, t))
            ml, mt = abs(mlc), abs(mtc)

            # win32con.SRCCOPY == 13369376
            self.cDC.BitBlt((0, 0), (w, h), self.dcObj, (ml, mt), 13369376)

        bmpinfo = self.dataBitMap.GetInfo()
        bmpstr = self.dataBitMap.GetBitmapBits(True)
        # default mode is BGRX
        img = Image.frombuffer('RGBX',
                               (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                               bmpstr, 
                               'raw', 'BGRX', 0, 1).convert('RGB')
        return img

    def save_window(self, filename, mode=0):
        img = self.capture_window(mode)
        if img:
            img.save(filename)


class CaptureViewer(tk.Frame):
    """A GUI program that can select, preview, capture and save window."""

    def __init__(self, parent=None):
        tk.Frame.__init__(self, parent)
        self.wc = WindowCapture()
        self.mode = 0
        self.count = 1
        self.status = 0

        #############################
        # ComboBox: window names
        # add decode('gbk') for some chinese words
        names = tuple(map(lambda x: x[1].decode('gbk'), self.wc.wins))
        self.win_box = ttk.Combobox(parent, values=names, state='readonly')
        self.win_box.current(0)
        self.win_box.grid(column=0, row=0)
        self.win_box.bind('<<ComboboxSelected>>', self.win_box_handle)
        # refresh windows every 5 seconds
        self.update_wins()

        ############################
        # Button: toggle margins
        self.mode_button = tk.Button(parent, text='Margins', 
                                     command=self.toggle_mode)
        self.mode_button.grid(column=1, row=0)

        ############################
        # Button: start preview window
        self.preview_button = tk.Button(parent, text='Preview', 
                                        command=self.start_preivew)
        self.preview_button.grid(column=2, row=0)

        ############################
        # Button: save window
        self.save_button = tk.Button(parent, text='Save',
                                     command=self.save_win)
        self.save_button.grid(column=3, row=0)

        ############################
        # Button: quit program
        self.quit_button = tk.Button(parent, text='Quit', 
                                     command=self.quit)
        self.quit_button.grid(column=4, row=0)

        ############################
        # Label: preview label
        img = Image.open('google-glass.jpg')
        tk_img = ImageTk.PhotoImage(img)
        self.img_label = tk.Label(parent, image=tk_img)
        self.img_label.image = tk_img
        self.img_label.grid(column=0, row=1, columnspan=5)

    def win_box_handle(self, event):
        pass

    def toggle_mode(self):
        self.mode = not self.mode

    def start_preivew(self):
        # stop current preview process
        self.status = 0

        idx = self.win_box.current()
        self.wc.set_win(idx)

        self.status = 1
        self.preview()

    def preview(self):
        if self.status:
            img = self.wc.capture_window(self.mode)
            if img:
                self.update_img_label(img)

            self.after(30, self.preview)

    def update_img_label(self, img):
        tk_img = ImageTk.PhotoImage(img)
        self.img_label.configure(image=tk_img)
        self.img_label.image = tk_img
    
    def update_wins(self):
        self.wc.get_wins()
        names = tuple(map(lambda x: x[1].decode('gbk'), self.wc.wins))
        self.win_box.configure(values=names)
        self.win_box.values = names
        self.after(5000, self.update_wins)

    def save_win(self):
        self.wc.save_window('capture_%s.bmp' % self.count, self.mode)
        self.count += 1

    def quit(self):
        # quit the top level container
        self.master.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    cap_viewer = CaptureViewer(root)
    cap_viewer.mainloop()
