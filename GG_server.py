import socket   
import time
import StringIO
import thread
from PIL import Image, ImageTk
import Tkinter as tk
import tkMessageBox

import merge


class SocketServer:
    """SocketServer could receive video from Android phone or Googel Glass  
    and send processed video to it.
    Functions:
        - connect(): connect to android phone
            - send_message_to_all(): send PC ip to all addresses in local network
            - recv_message(): receive message from phone
        - recv_img(): receive a PIL image from phone, and we will get phone's IP address 
        - send(img): open a thread to send a PIL image to the phone
    Default port:
        recv: 6000
        send: 6001
        """

    def __init__(self, recv_port=6000, send_port=6001):
        self.send_port = send_port
        self.recv_port = recv_port

        self.server = socket.socket()  
        host = socket.gethostname()
        self.server.bind((host, self.recv_port))
        # listen(1) will make video frames in disorder 
        self.server.listen(50)

    def connect(self):
        self.send_message_to_all()
        self.recv_message()

    def send_message_to_all(self):
        # start 255 threads to send PC ip
        for i in range(255):
            host = socket.gethostbyname(socket.gethostname())
            address = (host.rpartition('.')[0] + '.' + str(i),
                       self.send_port)
            # without \n android phone won't get the address
            message = host + '\n'
            thread.start_new_thread(self.send_message_thread, 
                                   (message, address))

    def send_message_thread(self, message, address):
        try:
            c = socket.create_connection(address, timeout=1)
            c.send(message)
            c.close()
        except socket.error:
            return

    def recv_message(self):
        c, address = self.server.accept()
        c.close()

    def recv_img(self):
        client, address = self.server.accept()
        self.android_ip = address[0]

        image_data = client.makefile('r+b')
        buff = StringIO.StringIO()
        for line in image_data:
            buff.write(line)

         #seek back to the beginning of the data
        buff.seek(0)
        img = Image.open(buff)

        image_data.flush()
        image_data.close()
        client.close()

        return img

    def send_img(self, img):
        thread.start_new_thread(self._send_img_thread,
                               (img, (self.android_ip, self.send_port)))
        time.sleep(0.01)

    def _send_img_thread(self, img, address):
        client = socket.create_connection(address)
        buff = StringIO.StringIO()
        img.save(buff, format='JPEG')
        client.sendall(buff.getvalue())
        client.close()


class ServerViewer(tk.Frame):
    def __init__(self, parent=None):
        tk.Frame.__init__(self, parent)

        self.src = Image.open('src.jpg')
        self.template = Image.open('template.jpg')

        self.ss = SocketServer()

        ##################################
        ### Entry: IP
        #self.ip_entry = tk.Entry(parent)
        #self.ip_entry.insert(0, '192.168.1.108')
        #self.ip_entry.grid(column=0, row=0)

        ################################
        # Button: Start
        self.start_button = tk.Button(parent, text='Start', 
                                      command=self.connect)
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

    #def get_ip(self):
        #text = self.ip_entry.get()
        #try:
            #ip = socket.inet_aton(text)
            #self.android_ip = text
            #return True
        #except socket.error:
            #tkMessageBox.showwarning('Error', 'IP Address Input Error')
            #return False
        
    def connect(self):
        self.ss.connect()
        self.start()

    def start(self):
        img= self.ss.recv_img()

        dst = merge.img_registration(self.src, img, self.template)
        # reisze its width to 640
        w, h = dst.size
        h_resized = int(640.0 / w * h)
        dst = dst.resize((640, h_resized))

        self.update_label(dst)
        self.ss.send_img(dst)
        self.after(10, self.start)

    def update_label(self, img):
        tk_img = ImageTk.PhotoImage(img)
        self.video_label.configure(image=tk_img)
        self.video_label.image = tk_img

    def quit(self):
        self.master.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    root.wm_title('Google Glass Viewer')
    sv = ServerViewer(root)
    sv.mainloop()
