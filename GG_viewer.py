import socket   
import time
import StringIO
import thread
import Tkinter as tk
import tkMessageBox
from PIL import Image, ImageTk


class ServerViewer(tk.Frame):
    def __init__(self, parent=None):
        tk.Frame.__init__(self, parent)
        self.ss = SocketServer()
        self.android_port = 6001

        ################################
        # Entry: IP
        self.ip_entry = tk.Entry(parent)
        self.ip_entry.insert(0, '192.168.1.115')
        self.ip_entry.grid(column=0, row=0)

        ################################
        # Button: Start
        self.start_button = tk.Button(parent, text='Start', 
                                      command=self.start)
        self.start_button.grid(column=1, row=0)

        ################################
        # Buttin: Quit
        self.quit_button = tk.Button(parent, text='Quit', 
                                     command=self.quit)
        self.quit_button.grid(column=2, row=0)

        ################################
        # Label: Video Viewer
        gg_img = Image.open('google-glass.jpg')
        tk_gg_img = ImageTk.PhotoImage(gg_img)
        self.video_label = tk.Label(parent, image=tk_gg_img)
        self.video_label.image = tk_gg_img
        self.video_label.grid(column=0, row=1, columnspan=3)

    def start(self):
        if self.get_ip():
            self.receive()

    def get_ip(self):
        text = self.ip_entry.get()
        try:
            parts = text.split('.')
            if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
                self.android_ip = text
                return True
            else:
                raise ValueError('IP Address Input Error')
        except Exception:
            tkMessageBox.showwarning('Error', 'IP Address Input Error')
            return False

    def receive(self):
        img = self.ss.recv_img()

        self.update_label(img)

        img = self.process(img)

        self.send(img, (self.android_ip, self.android_port))

        self.after(10, self.receive)

    def update_label(self, img):
        tk_img = ImageTk.PhotoImage(img)
        self.video_label.configure(image=tk_img)
        self.video_label.image = tk_img

    def process(self, img):
        # TODO: Image Processing
        return img

    def send(self, img, address):
        self.ss.send_img(img, address)

    def quit(self):
        self.master.destroy()


class SocketServer:
    def __init__(self, port=6000):
        self.server = socket.socket()  
        host = socket.gethostname()
        self.server.bind((host, port))
        # listen(1) will make video frames in disorder 
        self.server.listen(50)

    def recv_img(self):
        client, addr = self.server.accept()
        #print 'Got connection from ', addr
        image_data = client.makefile('r+b')
        buff = StringIO.StringIO()
        for line in image_data:
            buff.write(line)
        # seek back to the beginning of the data
        buff.seek(0)
        img = Image.open(buff)

        image_data.flush()
        image_data.close()
        client.close()
        return img

    def send_img(self, img, address):
        thread.start_new_thread(self.send_img_thread, (img, address))
        time.sleep(0.01)

    def send_img_thread(self, img, address):
        client = socket.create_connection(address)
        buff = StringIO.StringIO()
        img.save(buff, format='JPEG')
        client.sendall(buff.getvalue())
        client.close()

if __name__ == '__main__':
    root = tk.Tk()
    root.wm_title('Google Glass Viewer')
    sv = ServerViewer(root)
    sv.mainloop()
