import socket   
import time
import StringIO
import threading
import select
from PIL import Image, ImageTk
import Tkinter as tk


class GGServer:
    def __init__(self):
        self.send_port = 6001
        self.recv_img_port = 6000
        self.recv_message_port = 6002
        self.status = True
        self.connect_status = False
        
        # get wireless ip address when computer is connected to Ethernet  
        # http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
        s = socket.socket()
        s.connect(('ustc.edu.cn', 80))
        self.host, port = s.getsockname()
        s.close()

    def send_message(self, message, address):
        try:
            s = socket.create_connection(address, timeout=1)
            s.sendall(message)
            s.close()
        except socket.error:
            pass

    def recv_message(self):
        server = socket.socket()
        server.bind((self.host, self.recv_message_port))
        server.listen(5)

        while self.status:
            input_ready, _, _ = select.select([server], [], [], 0.01)
            if input_ready:
                client, address = server.accept()
                message = client.recv(1024)
                self.send_host = address[0]
                client.close()
                self.connect_status = True
                break
        server.close()

    def recv_img(self):
        while self.status:
            if not self.connect_status:
                time.sleep(0.01)
            else:
                break

        server = socket.socket()
        server.bind((self.host, self.recv_img_port))
        server.listen(50)

        while self.status:
            input_ready, _, _ = select.select([server], [], [], 0.005)
            if input_ready:
                client, address = server.accept()
                # store image data in StringIO
                image_data = client.makefile('r+b')
                buff = StringIO.StringIO()
                for line in image_data:
                    buff.write(line)
                # get PIL image from StringIO 
                buff.seek(0)
                img = Image.open(buff)
                # close all
                image_data.flush()
                image_data.close()
                client.close()

                processed = self.process_img(img)
                threading.Thread(target=self.send_img, args=(processed,)).start()

        server.close()

    def process_img(self, img):
        return img

    def send_img(self, img):
        try:
            client = socket.create_connection((self.send_host, self.send_port), timeout=1)
            buff = StringIO.StringIO()
            img.save(buff, format='JPEG')
            client.sendall(buff.getvalue())
            client.close()
        except socket.error:
            return

    def connect(self):
        if self.connect_status:
            return
        # send to all addresses in local network
        for i in range(255):
            address = (self.host.rpartition('.')[0] + '.' + str(i),
                       self.send_port)
            # without \n android phone won't get the address
            message = self.host + '\n'
            threading.Thread(target=self.send_message,
                             args=(message, address)).start()

    def start(self):
        threading.Thread(target=self.recv_message, args=()).start()
        threading.Thread(target=self.recv_img, args=()).start()

    def close(self):
        self.status = False


class GGServerViewer(tk.Frame, GGServer):
    def __init__(self, parent=None):
        tk.Frame.__init__(self, parent)
        self.init_GUI(parent)

        GGServer.__init__(self)
        self.start()

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
        tk_img = ImageTk.PhotoImage(img)
        self.video_label.configure(image=tk_img)
        self.video_label.image = tk_img
        return img

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
    sv = GGServerViewer(root)
    sv.mainloop()
