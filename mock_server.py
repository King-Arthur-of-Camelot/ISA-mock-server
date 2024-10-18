import socket
import ssl
import threading
import os
import argparse
import time

current_tag = ""

select_response_1 = """* 3 EXISTS\r\n * 3 RECENT\r\n* OK [UIDNEXT 17] Predicted next UID\r\n
* OK [UIDVALIDITY 42069] UIDs valid\r\n* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft $Forwarded)\r\n
* OK [PERMANENTFLAGS (\\Deleted \\Flagged \\Answered \\Seen \\Draft $Forwarded)] Can be changed permanently\r\n"""

select_response_2 = """* 3 EXISTS\r\n * 3 RECENT\r\n* OK [UIDNEXT 17] Predicted next UID\r\n
* OK [UIDVALIDITY 69420] UIDs valid\r\n* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft $Forwarded)\r\n
* OK [PERMANENTFLAGS (\\Deleted \\Flagged \\Answered \\Seen \\Draft $Forwarded)] Can be changed permanently\r\n"""

uid_fetch_response = "* SEARCH 1 2 3\r\n"

# Function to load and send .eml file contents
def send_eml_file(client_conn, eml_filename):
    filepath = "emls/"+eml_filename+".eml"
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as file:
                file_content = file.read()
                file_size = str(len(file_content.encode('utf-8')))

                data = "* "+eml_filename+"FETCH (UID "+eml_filename+" BODY[] \\{"+str(file_size)+"\\}\r\n"
                data += file_content
                data += ")\r\n"+current_tag+" OK UID FETCH completed\r\n"

                client_conn.sendall(data.encode('utf-8')) 
                print(f"Sent contents of {eml_filename} to client.")
        else:
            print(f"File {eml_filename} not found.")
    except Exception as e:
        print(f"Error sending .eml file: {e}")

# Function to send a message to the client
def send_message(client_conn, message):
    try:
        client_conn.sendall((message + "\r\n").encode('ascii'))
        print(f"Sent message: {message}")
    except Exception as e:
        print(f"Error sending message: {e}")

# Function to receive a message from the client
def receive_message(client_conn):
    global current_tag
    try:
        data = client_conn.recv(1024)  # Receiving up to 1024 bytes
        if data:
            print(f"Received: {data.decode().strip()}")
            data_str = data.decode().strip()
            current_tag = data_str.split(" ")[0]
            return data_str
        return None
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None
    
def log_in(client_conn):
    receive_message(client_conn)
    msg = current_tag + " OK LOGIN Successful"
    send_message(client_conn, msg)
    return


def scenario_1(client_conn):
    log_in(client_conn)
    
    # Select mailbox
    receive_message(client_conn)
    msg = select_response_1 + current_tag + " OK [READ-WRITE] SELECT completed"
    send_message(client_conn, msg)

    # Send UIDs
    receive_message(client_conn)
    msg = "* SEARCH 1 2 3\r\n"+ current_tag + " OK UID SEARCH completed\r\n"
    send_message(client_conn, msg)

    # Send email 1
    msg = receive_message(client_conn)
    if msg and "LOGOUT" in msg:
        send_message(client_conn, current_tag+" OK BYE")
        return

    send_eml_file(client_conn, "1")

    # Send email 2
    receive_message(client_conn)
    send_eml_file(client_conn, "2")

    # Send email 3
    receive_message(client_conn)
    send_eml_file(client_conn, "3")

    # Client disconnect
    receive_message(client_conn)
    send_message(client_conn, current_tag+" OK BYE")
    return

#Same as scenario 1 but the UIDValidity changed
def scenario_2(client_conn):
    log_in(client_conn)
    
    # Select mailbox
    receive_message(client_conn)
    msg = select_response_2 + current_tag + " OK [READ-WRITE] SELECT completed"
    send_message(client_conn, msg)

    # Send UIDs
    receive_message(client_conn)
    msg = "* SEARCH 1 2 3\r\n"+ current_tag + " OK UID SEARCH completed\r\n"
    send_message(client_conn, msg)

    # Send email 1
    msg = receive_message(client_conn)
    if msg and "LOGOUT" in msg:
        send_message(client_conn, current_tag+" OK BYE")
        return

    send_eml_file(client_conn, "UidValDiff/1")

    # Send email 2
    receive_message(client_conn)
    send_eml_file(client_conn, "UidValDiff/2")

    # Send email 3
    receive_message(client_conn)
    send_eml_file(client_conn, "UidValDiff/3")

    # Client disconnect
    receive_message(client_conn)
    send_message(client_conn, current_tag+" OK BYE")
    return

#Spam the client with unsolicited messages
def scenario_3(client_conn):
    log_in(client_conn)
    
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")

    # Select mailbox
    receive_message(client_conn)
    send_message(client_conn, "* 3 EXISTS")
    msg = select_response_1 + current_tag + " OK [READ-WRITE] SELECT completed"
    send_message(client_conn, msg)


    # Send UIDs
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")
    receive_message(client_conn)
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")
    msg = "* SEARCH 1 2 3\r\n"+ current_tag + " OK UID SEARCH completed\r\n"
    send_message(client_conn, msg)

    # Send email 1
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")
    msg = receive_message(client_conn)
    if msg and "LOGOUT" in msg:
        send_message(client_conn, current_tag+" OK BYE")
        return
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")
    send_eml_file(client_conn, "1")

    # Send email 2
    receive_message(client_conn)
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")
    send_eml_file(client_conn, "2")

    # Send email 3
    receive_message(client_conn)
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")
    send_eml_file(client_conn, "3")

    # Client disconnect
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")
    receive_message(client_conn)
    send_message(client_conn, "* OK [ALERT] Server going down for maintenance in 5 minutes")
    send_message(client_conn, current_tag+" OK BYE")
    return

#Don't respond to client for 15 seconds
def scenario_4(client_conn):
    log_in(client_conn)

    # Select mailbox
    receive_message(client_conn)
    send_message(client_conn, "* 3 EXISTS")
    msg = select_response_1 + current_tag + " OK [READ-WRITE] SELECT completed"
    send_message(client_conn, msg)

    time.sleep(15)
    return


def handle_client(client_conn, scenario_num):
    print("Client connected.")

    try:
        # Send welcome message
        send_message(client_conn, "* OK IMAP4rev1 Service Ready")

        if scenario_num == 1:
            scenario_1(client_conn)
        elif scenario_num == 2:
            scenario_2(client_conn)
        elif scenario_num == 3:
            scenario_3(client_conn)
        elif scenario_num == 4:
            scenario_4(client_conn)
        else:
            print("Unknown Scenario")
            

    except Exception as e:
        print(f"Error with client: {e}")
    finally:
        print("Closing client connection.")
        client_conn.shutdown(socket.SHUT_RDWR)

def start_server(port, use_ssl, certfile, scenario_num):
    host = '127.0.0.2'

    # Set up socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse the port
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server listening on {host}:{port}, SSL: {use_ssl}")

    try:
        client_conn, client_addr = server_socket.accept()

        if use_ssl:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=certfile)
            client_conn = context.wrap_socket(client_conn, server_side=True)

        # Handle the client connection
        handle_client(client_conn, scenario_num)

    finally:
        print("Shutting down server.")
        server_socket.close()

# Command-line interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock IMAP Server")
    parser.add_argument("--port", type=int, default=143, help="Port to run the server on")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL")
    parser.add_argument("--certfile", type=str, default="server.crt", help="SSL certificate file")
    parser.add_argument("scenario", type=int, help="Testing scenario number")
    
    args = parser.parse_args()

    start_server(args.port, args.ssl, args.certfile, args.scenario)
