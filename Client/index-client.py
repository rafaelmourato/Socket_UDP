import random
import threading
import socket
from datetime import datetime
import os
import math
from zlib import crc32
import struct

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("localhost", random.randint(8000, 9000)))

# Armazenamento de fragmentos recebidos
frags_received_list = []
frags_received_count = 0


def unpack_and_reassemble(data):
    global frags_received_count, frags_received_list

    header = data[:16]
    message_in_bytes = data[16:]
    frag_size, frag_index, frags_numb, crc = struct.unpack('!IIII', header)

    # Verificar CRC
    if crc != crc32(message_in_bytes):
        print("Fragmento com CRC inválido, ignorando.")
        return

    if len(frags_received_list) < frags_numb:
        add = frags_numb - len(frags_received_list)
        frags_received_list.extend([None] * add)

    frags_received_list[frag_index] = message_in_bytes
    frags_received_count += 1

    if frags_received_count == frags_numb:
        with open('received_message.txt', 'wb') as file:
            for fragment in frags_received_list:
                file.write(fragment)
        frags_received_count = 0
        frags_received_list = []
        print_received_message()

    elif (frags_received_count < frags_numb) and (frag_index == frags_numb - 1):
        print("Provavelmente houve perda de pacotes")
        frags_received_count = 0
        frags_received_list = []


def print_received_message():
    with open('received_message.txt', 'r') as file:
        file_content = file.read()
    os.remove('received_message.txt')
    print(file_content)


def receive():
    while True:
        data, addr = client.recvfrom(1024)
        unpack_and_reassemble(data)


thread1 = threading.Thread(target=receive)
thread1.start()


def create_fragment(payload, frag_size, frag_index, frags_numb):
    data = payload[:frag_size]
    crc = crc32(data)
    header = struct.pack('!IIII', frag_size, frag_index, frags_numb, crc)
    return header + data


def main():
    username = ''

    while True:
        message = input("")

        if message.startswith("hi, meu nome eh") or message.startswith("Hi, meu nome eh"):
            username = message[len("hi, meu nome eh") + 1:].strip()
            sent_msg = f"SIGNUP_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()

        elif username and message == "bye":
            sent_msg = f"SIGNOUT_TAG:{username}"
            with open('message_client.txt', 'w') as file:
                file.write(sent_msg)
            send_txt()
            print("Conexão encerrada, Até logo!")
            exit()

        else:
            if username:
                timestamp = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
                formatted_message = f"{client.getsockname()[0]}:{client.getsockname()[1]}/~{username}: {message} {timestamp}"
                with open('message_client.txt', 'w') as file:
                    file.write(formatted_message)
                send_txt()
            else:
                print("Para conectar a sala digite 'hi, meu nome eh' e digite seu username")


def send_txt():
    frag_index = 0
    frag_size = 1024

    with open('message_client.txt', 'rb') as file:
        payload = file.read()
        frags_numb = math.ceil(len(payload) / frag_size)

        while payload:
            fragment = create_fragment(payload, frag_size, frag_index, frags_numb)
            client.sendto(fragment, ('localhost', 7777))
            payload = payload[frag_size:]
            frag_index += 1
    os.remove('message_client.txt')


main()