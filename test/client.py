import socket
import struct
import sys
import config

def sendMessage(message, ipAddress, port):
    multicast_group = (ipAddress, port)

    # Create the datagram socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Set a timeout so the socket does not block indefinitely when trying
    # to receive data.
    sock.settimeout(0.2)

    # Set the time-to-live for messages to 1 so they do not go past the
    # local network segment.
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:

        # Send data to the multicast group
        print(f"sending {message}")
        _ = sock.sendto(bytearray(message, encoding ='utf-8'), multicast_group)

        # Look for responses from all recipients
        while True:
            print(f"waiting to receive")
            try:
                data, server = sock.recvfrom(16)
            except socket.timeout:
                print(f"timed out; no more responses")
                break
            else:
                print(f"received {data} from {server}")

    finally:
        print(f"closing socket")
        sock.close()

def programLoop(loopFunc, inputMessage):

    continueProcessing = True

    # Start a loop that will run until the user enters 'quit'.
    while continueProcessing:
        # Ask the user for a name.
        inputData = input(inputMessage)

        continueProcessing = loopFunc(inputData)

def process(inputData, ipAddress, port):
    sendMessage(inputData, ipAddress, port)
    return (inputData != "exit")

loopMessage = "enter message: "

config = config.read_config()

srv = config['notify'][0]
ipAddress = srv['address']
port = srv['port']

programLoop(lambda inputData: process(inputData, ipAddress, port), loopMessage)