#!/usr/bin/python
import socket
import sqlite3
import paramiko
import sys, os
import getpass                         # For the email password input
import smtplib                         # For sending email
from _thread import *
import xml.etree.ElementTree as ET     # API for xml parsing
from simplecrypt import decrypt
import pysftp                          # API for ssh connection


########################
     # Variables #     #
                       #
filename="data.xml"    #
                       #
########################

# 1.Gets the local ip/ip over LAN.

#HOST =socket.gethostbyname(socket.gethostname())
HOST="192.168.0.102"
# 2.Use port no. above 1800 so it does not interfere with ports already in use.

PORT =input ("Enter the PORT number (1 - 10,000)")

#GMAIL_PASSWORD =input ("Enter your gmail password:")

GMAIL_PASSWORD=getpass.getpass("Insert your gamil password: ")    #password input


# CREATE THE DATABASE

def create_table(db_name,table_name,sql):
	with sqlite3.connect(db_name) as db:
		cursor=db.cursor()
		cursor.execute('PRAGMA foreign_keys=ON')
		cursor.execute("select name from sqlite_master where name=?",(table_name,))
		result=cursor.fetchall()
		kepp_table=True
		if len(result) == 1:
			response = input("The table {0} alerady exists, do yoy wish to recreate it (y/n):".format(table_name))
			if response== "y":
				kepp_table=False
				print('The {0} table will be recreated- all existing data will be lost'.format(table_name))
				cursor.execute('drop table if exists {0}'.format(table_name))
				db.commit()
			else:
				print("The existing table was kept")
		else:
			kepp_table=False
		if not kepp_table:
			cursor.execute(sql)
			db.commit()


# CREATE DATABASE - BUILD THE COLLONS

def create_table_for_doc(db_name):

	sql="""CREATE TABLE IF NOT exists INFORMATION(
			ID INTEGER,
			CLIENT_IP text,
			CLIENT_PORT text,
			MEMORY_FREE text,
			MEMORY_PERCENT text,
			MEMORY_AVAILABLE text,
			MEMORY_TOTAL text,
			MEMORY_USED text,
			CPU text,
			UPTIME text,
			primary key(ID))"""

	create_table(db_name,'INFORMATION',sql)

# CREATE DATABASE - POPULATE THE DATABASE

def insert_text(CLIENT_IP, CLIENT_PORT, MEMORY_FREE, MEMORY_PERCENT, MEMORY_AVAILABLE, MEMORY_TOTAL,MEMORY_USED,CPU,UPTIME):

		with sqlite3.connect("client_data.db") as db:
			cursor=db.cursor()
			data=(CLIENT_IP, CLIENT_PORT, MEMORY_FREE, MEMORY_PERCENT, MEMORY_AVAILABLE, MEMORY_TOTAL,MEMORY_USED,CPU,UPTIME)
			sql="INSERT INTO INFORMATION(CLIENT_IP, CLIENT_PORT, MEMORY_FREE, MEMORY_PERCENT, MEMORY_AVAILABLE, MEMORY_TOTAL, MEMORY_USED, CPU, UPTIME) values (?,?,?,?,?,?,?,?,?)"
			cursor.execute(sql,data)
			db.commit()

# START THE DECRYPTION PROCESS

def parse_decrypted_data(data_list):
    data_length = len(data_list)
    # get the correct variables from the string

    for i in range(data_length):
        if data_list[i] == "CLIENT_IP:":
            ip = data_list[i+1]
        elif data_list[i] == "CLIENT_PORT:":
            port = data_list[i+1]
        elif data_list[i] == "MEMORY_FREE":
            free_memory = data_list[i+1]
        elif data_list[i] == "MEMORY_PERCENT":
            percent_memory = data_list[i+1]
        elif data_list[i] == "MEMORY_TOTAL":
            total_memory = data_list[i+1]
        elif data_list[i] == "MEMORY_USED":
            used_memory = data_list[i+1]
        elif data_list[i] == "MEMORY_AVAILABLE":
            available_memory = data_list[i+1]
        elif data_list[i] == "CPU":
            cpu = data_list[i+1]
        elif data_list[i] == "UPTIME":
            uptime = data_list[i+1]

    # check the integrity of the values
    if ip and port and free_memory and percent_memory and total_memory and used_memory and available_memory and cpu and uptime:
        print("Correct data received!")
        # if ok, enter values into database
        insert_text(str(ip), str(port),str(free_memory),str(percent_memory),str(available_memory),str(total_memory),str(used_memory),str(cpu),str(uptime))
        print("Data entered into database!")
    else:
        print("Data from the client si not correct!")

def decrypt_data(data, addr):

    f = open("mydata.txt",'a+')
    if data:
        print("Decrypting received data....")
        decrypted_data = decrypt('cris', data).decode('utf-8')
        CLIENT_IP,CLIENT_PORT=addr[0],addr[1]
        aditional_info="\n" +"CLIENT_IP: " + str(CLIENT_IP) + " " + "CLIENT_PORT: " + str(CLIENT_PORT) + " "
        aditional_info +=str(decrypted_data)
        data_list = aditional_info.split()
        parse_decrypted_data(data_list)
        f.write(str(aditional_info))
        f.close()
        return(decrypted_data)
    else:
	    print("There is no data to decrypt")



def threded_clinet(conn, addr):

    conn.send(str.encode("Data received by the server!\n"))
    data = conn.recv(1024)

    start_new_thread(decrypt_data, (data,addr,))

    if data:
        reply = "Server output: Data was received by the server!"
        conn.sendall(str.encode(reply))
    else:
        reply = "Server output: Data was not received by the server!"
        conn.sendall(str.endcode(reply))
    conn.close()

# SENT MAIL TO THE SERVER OWNER

def send_email_function(fromaddr,memory_limit, cpu_limit,gmail_password):
	toaddrs = fromaddr
	# Gmail Login
	username = fromaddr
	msg = """
	This a automated email received from a script. The alert is:
	\n Memory limit: %s
	\n CPU limit: %s""" % (str(memory_limit),str(cpu_limit))
	# Sending the mail
	try:
		server = smtplib.SMTP('smtp.gmail.com:587')
		server.starttls()
		server.login(username,gmail_password)
		server.sendmail(fromaddr, toaddrs, msg, "")
		server.quit()
		print('successfully sent the mail')

	except:
		print("Failed to send mail. Check if the Gmail password is correct.")

	return(True)




# CONNECT TO THE USER THROUGH SSH

def ssh_connection(ip,port,user_name,pasd):

	pathname = os.path.dirname(sys.argv[0])
	full_pathname=os.path.abspath(pathname)

	try:
		send_script=os.path.join(full_pathname,"Send")
	except Exception:
		print("Check if 'Send' directory exists in this path!")

	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, username=user_name, password=pasd)
		print("Conected to:", user_name)
	except Exception:
		print("Could not connect!")

	try:
		sftp = ssh.open_sftp()
		main_directory = sftp.listdir()
		if not "temp" in main_directory:
			sftp.mkdir('temp',511) # Create directory
			print("temp directory created.")
		else:
			print("temp is already there")
	except Exception:
		print("Could not create directory")
	try:
		sftp.put('Send/monitor.py','temp/monitor.py')   # a lot of problems i had here. Man, docs are not very specific!
		print("File transfered!")
	except Exception:
		print("Could not transfer the script")

	try:
		sftp.chdir("temp")
		print("Directory changed")
	except Exception:
		print("Could not change to temp directory")
	try:
		print("Current directory:", sftp.getcwd())
	except Exception:
		print("Could not print current directory")

	try:
		command="python monitor.py" + HOST + " " + PORT
		stdout = ssh.exec_command(command)[1]
		print("Script executed")
		for line in stdout:
			print(line)
	except Exception:
		print("Was not able to execute the script")

def check_mail_alert(child,user_mail):

	number_of_alerts=len(child)

	if number_of_alerts > 0:
		for second_child in child:
			second_child_attrib=second_child.attrib
			check_type=second_child_attrib.get("type")
			if check_type=="memory":
				memory_limit=second_child_attrib.get("limit")
			elif check_type=="cpu":
				cpu_limit= second_child_attrib.get("limit")
			else:
				print("There are no tests to be done!")

            # SEND MAIL
		send_email_function(user_mail, memory_limit,cpu_limit,  GMAIL_PASSWORD)
	else:
		print("There are no alerts to take into consideration!")

	return(True)

# PARSE THE XML DATA
def start_parsing(filename):
	try:
		tree = ET.parse(filename)   # PARSE
		root = tree.getroot()
		number_of_clients=len(root)
		print("The number of total clients are:", number_of_clients)
		counter=1
		# START THE XML ANALYZATION
		for child in root:
			child_attributes=child.attrib

        	# Check for errors in the xml
			if "username" in child_attributes and "ip" in child_attributes and "port" in child_attributes and "password" in child_attributes and "mail"  in child_attributes:
				user_name=child_attributes.get("username")
				ip=child_attributes.get("ip")
				port=child_attributes.get("port")
				password=child_attributes.get("password")
				user_mail=child_attributes.get("mail")
				check_mail_alert(child,user_mail)     # send the user_mail to check_mail_alert function

            	# Call the ssh_connection function to start connecting to the users
            	# Open a multiple threads to make multiple connections for the users specified in the xml
				start_new_thread(ssh_connection, (ip, port, user_name, password, ))
			else:
				print("One of the attributes is missing in xml!")
			counter +=1

		return(True)
	except Exception:
		print("Xml file not found!")


# MAIN FUNCTION

def main(filename):

    create="none"

    while create != "y" and create !="n":
        create = input("Do you want to create the database for the future data [y/n]:")
        if create == "y":
            create_table_for_doc('client_data.db')
        elif create =="n":
            print("ATTENTION! Program can not run without a database. ")


    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.bind((HOST, int(PORT)))
    except socket.error as msg:
        print(str(msg))

    s.listen(100)
    print("Waiting for a connection....")
    print("Starting to parse the xml data....")
    start_parsing(filename)

    while True:
        conn ,addr = s.accept()
        print("Connected to :"+  addr[0] + ":" + str(addr[1]))

        start_new_thread(threded_clinet, (conn,addr,))


if __name__ == "__main__":
    main(filename)
