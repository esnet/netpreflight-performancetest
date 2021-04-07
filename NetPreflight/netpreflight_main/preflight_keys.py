#################################################################################################################################
#                                          Netpreflight Usage using Public Keys:                                                #
#################################################################################################################################
#                                                                                                                               #
# on HOST_A: On your terminal run the command below with the following arguements                                               #
#                                                                                                                               #
# #python <scriptname> -H <TargetHostIPaddress> -K <KeyFilepath>  -F <targetFile> -I <no. of iterations> -S <targetFilesize>    #
#                                                                                                                               #
#                                                                                                                               #
# Generate files using dev zero on the Target host(Destination Node)                                                            #
# For example to create a 1MB file with name onemb.zip : dd if=/dev/zero of=onemb.zip count=1 bs=1024                           #                                                                                         #
# For example to create a 1GB file with name onemb.zip : dd if=/dev/zero of=onegig.zip count=1 bs=10240                         #
#                                                                                                                               #
#                                                                                                                               #
# python preflight_keys.py -H 192.5.87.20 -K /Users/bashirm/Downloads/uc-mc4n-key.pem -F /home/cc/experiments/5MB.zip -I 5 -S 5 #
# python preflight_keys.py -H 192.5.87.20 -K /home/cc/experiments/uc-mc4n-key.pem -F /home/cc/experiments/5MB.zip -I 5 -S 5     #                                                                                        #
# Requirements: sudo pip install paramiko                                                                                       #
#################################################################################################################################
import json
import datetime
import socket, os, sys, optparse, time
import subprocess
import paramiko
import threading
import getpass

ssh = paramiko.SSHClient()
outfile = 'results'
BufferSize = 1024

username = ''
key = ''


def userprompt():
    username = input("Hello! Welcome to Netpreflight Tool! \n\nUsername: ") 
    key = getpass.getpass('Password :: ')
    print('key',key)


def retBanner(ip, port=22):
    sock = socket.socket()
    sock.connect((ip, port))
    sock.send(b'Gabbage')
    banner = sock.recv(BufferSize)
    return banner

def download_fileV3(targetHost, targetFile, username,key):
    k = paramiko.RSAKey.from_private_key_file(key)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print ("connecting")
    c.connect( hostname = targetHost, username = username, pkey = k )
    print('..................................')
    print('Starting to download file at {}...!'.format(targetFile))
    sftp = c.open_sftp()
    localpath = targetFile.split("/")[-1]
    remotepath = targetFile
    sftp.get(remotepath,localpath)
    sftp.close()
    c.close()

def main():
    global file_size
    currentime = datetime.datetime.now() 
    newfile = ('res' + str(currentime) + '.txt')
    print(newfile)
    parser = optparse.OptionParser('usage %prog -H <targetHost> -F <targetFile> -I <iterations>')
    parser.add_option('-H', dest='targetHost', type='string', help='')
    parser.add_option('-K', dest='key', type='string', help=' Specify the location of your key')
    parser.add_option('-F', dest='targetFile', type='string', help='Specify File on remote to download')
    parser.add_option('-I', dest='iterations', type='int', help='Specify number of iterations')
    parser.add_option('-S', dest='filesize', type='int', help='File Size')

    (options, args) = parser.parse_args()
    host = options.targetHost
    file = options.targetFile
    key= options.key
    iterations = options.iterations
    file_size = options.filesize

    username = input("Hello! Welcome to Netpreflight Tool! \n\nUsername: ") 

    headings = ["Iter", "Throughput", "Time(s)", "Buffer"]
    data = []
    threads = 2

    file_ = open('traceresult.txt', 'w+')
    subprocess.run('traceroute '+ host, shell=True, stdout=file_)
    file_.close()

    jobs = []
    for i in range(0, threads):
        out_list = list()
        thread = threading.Thread(multithreading(iterations, host, file, username, key, headings, i))
        jobs.append(thread)

    for j in jobs:
        j.start()

    # Ensure all of the threads have finished
    for j in jobs:
        j.join()

    print ("List processing complete.")


    
def multithreading(iterations, host, file, username, key, headings, count):
    data = []
    json_data = {}
    currentime = datetime.datetime.now()
    with open(outfile + str(count) + ".csv", 'a') as ff:
        ff.write(str(currentime)+'\n')
    ff.close()
    for iteration in range(iterations):
        start = time.time()
        download_fileV3(targetHost=host, targetFile=file, username=username, key=key)
        end = time.time()

        lapse = round((end - start), 3)
        #with open(outfile +str(currentime)+ str(count) + ".csv", 'a') as ff:
        with open(outfile + str(count) + ".csv", 'a') as ff:
        #    ff.write(str(currentime))
        #    tp = round(((BufferSize)) / (lapse+0.000001), 3)
        #    tp /= 100
            tp = file_size*8/(lapse * (0.001**0.5))
            smallist = [iteration, tp, lapse, BufferSize]
            data.append(smallist)
            ff.write('iteration {},{},{},{}\n'.format(iteration, tp, lapse, BufferSize))
        # import ast
        # with open("memory.json") as json_file:
        #     data_memory=json.load(json_file)
        #     #print(data_memory)
        #     json_data = {host:{"iteration":iteration,"Throughput":tp, "lapse":lapse, "BufferSize":BufferSize}}
        #     aaa=ast.literal_eval(data_memory)
        #     aaa.update(json_data)
    
        #     json.dump(str(aaa),open("memory.json","w"))
        
    with open ('traceresult.txt') as tfile:
        trace_result = [i for i in tfile.readlines() if "* * *" not in i]
    try:
        with open("memory.json") as json_file:
            data_memory=json.load(json_file)
            main_value = {"iteration":iteration,"Throughput":tp, "lapse":lapse, "BufferSize":BufferSize, "Timestamp":str(currentime), "trace_result":trace_result}
            if host in data_memory.keys():
                main_value = data_memory[host]+[main_value]
                json_data = {host:main_value}
            else:
                json_data = {host:[main_value]}
            data_memory.update(json_data)
            
            json.dump(data_memory, open("memory.json", "w"), indent=4)
    except:
        json.dump(json_data, open("memory.json", "w"),indent=4)

            
            #json.dump(str(json_data),open("memory.json","w"))

    format_row = "{:>12}" * (len(headings) + 1)
    print(format_row.format("", *headings))
    for row in data: 
        print(format_row.format('', *row))

     
    with open('traceresult.txt', 'r') as f:
            print('netpreflight',f.read())
       

if __name__ == '__main__':
    main()


