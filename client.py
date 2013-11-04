import socket   
import cv2

#cam = cv2.imread('1.jpg')     
address = ('192.168.1.119', 31500)  
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
cam = cv2.VideoCapture(0)
while True:      
    rval, img = cam.read()
    img = cv2.resize(img, (100, 75))
    msg = img.tostring()
  #  print msg 
    if not msg:  
        break  
    s.sendto(msg, address)   
s.close()  
