from PIL import Image, ImageTk
import Tkinter as tk
import time

import GG_server
import merge
import window_capture


class GGNaviViewer(tk.Frame, GG_server.GGServer):
    def __init__(self, parent=None):
        tk.Frame.__init__(self, parent)
        self.init_GUI(parent)

        self.get_fluo_window()
        GG_server.GGServer.__init__(self)
        self.start()

    def get_fluo_window(self):
        self.template = Image.open('template.jpg')

        # capture src image from AMCap application window
        self.wc = window_capture.WindowCapture()
        for idx, win in enumerate(self.wc.wins):
            if 'AMCap' in win[1]:
                self.wc.set_win(idx)
                break
        else:
            raise IOError('cannot find AMCap window')
        return

    def init_GUI(self, parent):
        ################################
        # Button: Start
        self.start_button = tk.Button(parent, text='Start', 
                                      command=self.start_viewer)
        self.start_button.grid(column=0, row=0)

        ################################
        # Buttin: Quit
        self.quit_button = tk.Button(parent, text='Quit', 
                                     command=self.quit)
        self.quit_button.grid(column=1, row=0)

        ################################
        # Label: Video Viewer
        gg_img = Image.open('google-glass.jpg')
        tk_gg_img = ImageTk.PhotoImage(gg_img)
        self.video_label = tk.Label(parent, image=tk_gg_img)
        self.video_label.image = tk_gg_img
        self.video_label.grid(column=0, row=1, columnspan=2)

    def process_img(self, img):
        src = self.wc.capture_window()
        merged = merge.img_registration(src, img, self.template, 'PIL')

        tk_img = ImageTk.PhotoImage(merged)
        self.video_label.configure(image=tk_img)
        self.video_label.image = tk_img
        return merged

    def start_viewer(self):
        self.connect()

    def update_label(self, img):
        tk_img = ImageTk.PhotoImage(img)
        self.video_label.configure(image=tk_img)
        self.video_label.image = tk_img

    def quit(self):
        self.close()
        time.sleep(0.5)
        self.master.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    root.wm_title('Google Glass Viewer')
    sv = GGNaviViewer(root)
    sv.mainloop()
