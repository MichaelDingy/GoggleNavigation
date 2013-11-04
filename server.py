import socket  
HOST = '192.168.1.107'
PORT = 31500
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
s.bind((HOST, PORT))  
while True:  
    data, address = s.recvfrom(1000000)
    if not data: break
    print data
conn.close()
