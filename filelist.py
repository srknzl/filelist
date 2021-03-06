#!/usr/bin/python
import sys
import re
import os
import datetime
import subprocess
import commands
from collections import deque
import time



currentStats = [] # list of stats to be printed, occasionally add the items at the next three lines
totalNumberUniqueFile = 0 # add this if -duplcont
totalNumberUniqueNamed = 0 # add this if -duplname
totalSizeOfUniqueFiles = 0 # add this if -duplcont
bigger = "" # these variables holds options' status. Now their default values are present.
smaller = ""# for example bigger will store something like "10M" or "123123"
after = "" # whereas for instance, delete can be either true or false.
before = ""
match = ""
zipFile = ""
delete = False
duplcont = False
duplname = False
stats = False
nofilelist = False

def run(paths): # this is my main biggest function that call other functions
    global currentStats,totalSizeOfUniqueFiles,totalNumberUniqueNamed,totalNumberUniqueFile
    filesizes = [] # this will store the filesizes of all files for showing total size of all files if -stats is given
    files = traversal(paths) # traverse given paths and return files with paths in it
    includedFiles = [] # store included files' sizes according to options
    includedFilePaths = [] # store included files' paths here

    for file in files: # for all individual file found in specified paths
        try:
            filesize, modtime, shasum, dateAndTime = getinfooffile(file) # this calculates the general information of a file 1.size in bytes 2. modification time 3. shasum 4. modification data and time formatted version
            filesizes.append(filesize)  # list of all files' sizes
            lastIndex = file.rfind("/") # find last index of / in path to extract filename
            filename = file[lastIndex + 1:] # here we extract filename from path

            if delete == True and zipFile != "": # this cannot be hold
                sys.exit("error: both delete and zip exist")

            if delete == True and duplcont == True: # this cannot be hold
                sys.exit("error: both delete and duplcont exist")

            if delete == True and duplname == True: # this cannot be hold
                sys.exit("error: both duplname and delete exist")

            if duplcont == True and duplname == True: # this cannot be hold
                sys.exit("error: both duplname and duplcont exist")

            biggerb = None # if a file satisfy bigger condition
            smallerb = None # if a file satisfy smaller condition
            afterb = None # if a file satisfy after condition
            beforeb = None # if a file satisfy before condition

            if bigger != "": # If bigger is present
                if bigger[-1] == "M":  # mega is 2^20
                    biggerb = filesize >= int(bigger[:len(bigger) - 1]) * 1024 * 1024
                elif bigger[-1] == "G": # giga is 2^30
                    biggerb = filesize >= int(bigger[:len(bigger) - 1]) * 1024 * 1024 * 1024
                elif bigger[-1] == "K": # kilo is 2^10
                    biggerb = filesize >= int(bigger[:len(bigger) - 1]) * 1024
                else:  # If not three of prev options treat directly as bytes
                    biggerb = filesize >= int(bigger)
            else:
                biggerb = True # If bigger is not present it is true anyway
            if smaller != "": # similar to bigger
                if smaller[-1] == "M":
                    smallerb = filesize <= int(smaller[:len(smaller) - 1]) * 1024 * 1024
                elif smaller[-1] == "G":
                    smallerb = filesize <= int(smaller[:len(smaller) - 1]) * 1024 * 1024 * 1024
                elif smaller[-1] == "K":
                    smallerb = filesize <= int(smaller[:len(smaller) - 1]) * 1024
                else:
                    smallerb = filesize <= int(smaller)
            else:
                smallerb = True
            if after != "": # if after is present
                if len(after) == 8: # if it is in YYYYMMDD format (note that we check the format before using regex)
                    d = datetime.datetime(int(after[0:4]), int(after[4:6]), int(after[6:]))
                    unixtime = time.mktime(d.timetuple()) # this and prior statement extract given date's timestamp value
                    afterb = modtime >= unixtime # condition
                else: # other format YYYYMMDDTHHMMSS
                    d = datetime.datetime(int(after[0:4]), int(after[4:6]), int(after[6:8]), int(after[9:11]),int(after[11:13]), int(after[13:]))
                    unixtime = time.mktime(d.timetuple())
                    afterb = modtime >= unixtime # condition
            else:
                afterb = True
            if before != "": # similar to after
                if len(before) == 8:
                    d = datetime.datetime(int(before[0:4]), int(before[4:6]), int(before[6:]))
                    unixtime = time.mktime(d.timetuple())
                    beforeb = modtime <= unixtime
                else:
                    d = datetime.datetime(int(before[0:4]), int(before[4:6]), int(before[6:8]), int(before[9:11]),int(before[11:13]), int(before[13:]))
                    unixtime = time.mktime(d.timetuple())
                    beforeb = modtime <= unixtime
            else:
                beforeb = True

            if biggerb and smallerb and afterb and beforeb and (match == "" or (match != "" and re.match(match, filename))):
                includedFiles.append(filesize) # all the conditions above, added one is match, re.match(..) returns none if not matches
                includedFilePaths.append(file) # list of files will be printed
                if not nofilelist and not duplcont and not duplname:
                    print file
        except OSError:
            print "error: couldn't open file \"" + file + "\""
        except BaseException as e:
            print e.__doc__  # If we cannot open the file
            print e.message

    if not nofilelist and duplcont:
        printDuplCont(includedFilePaths) # duplcont printing
    elif not nofilelist and duplname:
        printDuplName(includedFilePaths) # duplname printing

    if delete:
        for i in includedFilePaths:
            os.remove(i) # deletion

    if zipFile: # zipping with commands
        pwd = commands.getoutput("pwd")  # get current directory into pwd variable
        tempName = commands.getoutput("mktemp -d") # make a new temporary file in /tmp
        foldername = zipFile[:len(zipFile) - 4] # get the name of a folder by excluding .zip of given zipFile
        commands.getoutput("mv " + tempName + " " + pwd) # move temporary file to pwd because we need a unique folder
        commands.getoutput("mkdir " + tempName[5:] + "/" + foldername) # inside temporary folder create a folder with name foldername
        for i in includedFilePaths:
            commands.getoutput("cp " + "'" + i + "'" + " " + tempName[5:] + "/" + foldername) # copy all the files into the foldername folder
        os.chdir(pwd + tempName[4:]) # go insider tmp folder
        commands.getoutput("zip -r " + zipFile + " " + foldername) # zip it there because otherwise the zip file contaion multiple nested folders consisting path
        commands.getoutput("mv " + zipFile + " " + pwd) # mov created zipfile to previous directory i.e proior pwd
        os.chdir(pwd) # go to pwd
        commands.getoutput("rm -r " + tempName[5:]) # remove tmp folder

    if stats: # printing stats
        totalSize = 0
        for i in filesizes:
            totalSize += i # total size of all the files except with errored ones
        currentStats.append("Total number of files visited: " + str(len(filesizes))) # currentStats is a list and we append strings that we want them to be printed into it
        currentStats.append("Total size of the files visited in bytes:" + str(totalSize))
        totalSizeOfIncluded = 0
        for i in includedFiles:
            totalSizeOfIncluded += i # total size of included files is calculated here
        currentStats.append("Total number of included files " + str(len(includedFiles)))
        currentStats.append("Total size of the files included " + str(totalSizeOfIncluded))
        if duplname: # This is added as an extra if duplname option is given
            currentStats.append("Total number of files with unique names: " + str(totalNumberUniqueNamed))
        elif duplcont: # These are added as an extra if duplcont option is given
            currentStats.append("Total number of files with unique content: " + str(totalNumberUniqueFile))
            currentStats.append("Total size of files with unique content: " + str(totalSizeOfUniqueFiles))
        printstats(duplcont, duplname)

def printDuplCont(files): # For printing found files in groups seperated with lines : "-----------------"
    global totalSizeOfUniqueFiles
    global totalNumberUniqueFile
    dict = {} # the format = "shasum: [files]". Will store files with same shasum

    for path in files:
        command = "shasum " + '"' + path + '"'
        shasumstr = subprocess.check_output(command, shell=True) # compute shasum again for convenience, it takes time but whatever, not much.
        shasum = shasumstr[:40]
        if not dict.get(shasum):
            dict[shasum] = [path] # if there is not an entry for current shasum create a new list
        else:
            dict[shasum].append(path) # il there is append

    for i in dict.keys():
        for j in dict[i]:
            print j
        print "-------------------"

    totalNumberUniqueFile = len(dict) # This will be used later in stats

    for i in dict.keys():
        st = os.stat(dict[i][0]) # taking only one file of each group is sufficient
        filesize = st.st_size # finding sizes of unique files here
        totalSizeOfUniqueFiles += filesize

def printDuplName(files):
    global totalNumberUniqueNamed
    dict = {} # format = "name: [path]"

    for i in files:
        last = i.rfind("/")
        name = i[last+1:] # extract filename from path
        if not dict.get(name):
            dict[name] = [i] # if not present create a list
        else:
            dict[name].append(i) # if present append to the list

    for i in dict.keys():
        for j in dict[i]:
            print j
        print "-------------------"

    totalNumberUniqueNamed = len(dict) # again will be used in stats

def printstats(duplcont,duplname):

    if duplname and duplcont:  # should not happen due to description of the project
        sys.exit("error: found that both duplcont and duplname is true while printing stats.")
    else:
        for i in currentStats:
            print i # just print all the entries in currentStats

def getinfooffile(path): # this is used in run function and computes several properties of files

    st = os.stat(path) # stat object
    filesize = st.st_size # filesize
    modtime = st.st_mtime # modification time as timestamp
    command = "shasum " +'"' + path + '"'
    shasum = subprocess.check_output(command,shell=True) # shasum value
    dateAndTime = datetime.datetime.fromtimestamp(modtime).strftime('%Y%m%dT%H%M%S') # formatted modification time
    # format : 20180212T122312
    return filesize, modtime, shasum, dateAndTime

def traversal(paths):
    # traversal of given paths, returns traversed files

    files = [] # will be returned
    for i in paths: # for all paths given
        qlist = deque([i]) # add it to a queue
        while qlist: # until queue is empty
            currentdir = qlist.popleft()   # pop an element
            try:
                dircontents = os.listdir(currentdir) # list the files and folders inside current directory
                for name in dircontents:
                    currentitem = currentdir + "/" + name
                    if os.path.isdir(currentitem):
                        qlist.append(currentitem) # if it is a folder add it to queue
                    else:
                        files.append(currentitem) # if it is a file add it to files list
            except OSError:
                print "cannot read directory "+ currentdir

    return files

args = sys.argv # arguments

if args[1] == "-h" or args[1] == "--help":
    print("""
  FILELIST, Serkan Ozel

  Usage: ./filelist.py options directory 

\t-after, files created after a time
\t-before, files created before a time
\t\tformat of time YYYYMMDD or YYYYMMDDTHHMMSS
\t-bigger, files bigger than a size, append M to a number for megabytes, G for gigabytes and K for kilobytes
\t-match, match files according to a regex 
\t-zip, zip found files
\t-delete, delete found files
\t-stats, show stats
\t\tTotal number of files visited
\t\tTotal size of the files visited in bytes
\t\tTotal number of included files
\t\tTotal size of the files included
\t\tif duplname is set, Total number of files with unique names
\t\tif duplcont is set, Total number of files with unique content
\t\tif duplcont is set, Total size of files with unique content
\t-nofilelist, do not list files
\t-duplname, Print files with same name. 
\t-duplcont, Group files with same content. Groups are seperated by ------- lines
    """)
    exit()

args.pop(0) # To pop name of the executable
counter = 0

while counter < len(args): # parse arguments here
    if args[counter] in ['-bigger', '-smaller']:
        if counter + 1 != len(args): # if arguments finished after options that require extra info exit program
            found = re.match("^\d*[MGK]?$", args[counter+1])
            if found:
                if args[counter] == '-bigger' and bigger == "":
                    bigger = args[counter+1]
                    counter += 2
                elif args[counter] == '-smaller' and smaller == "":
                    smaller = args[counter+1]
                    counter += 2
                else:
                    sys.exit("error: multiple -bigger or -smaller options") # if it is modified twice exit program
            else:
                sys.exit("error: not found good argument after -bigger or -smaller") # if the format is wrong
        else:
            sys.exit("error: not found any argument after -bigger or -smaller please use -bigger/smaller <digits>(optinal M or G or K) notation")
    elif args[counter] in ['-after', '-before']:
        if counter + 1 != len(args):
            found = re.match("^\d{8}(T\d{6})?$", args[counter + 1])
            if found:
                if args[counter] == '-after' and after == "":
                    after = args[counter + 1]
                    counter += 2
                elif args[counter] == '-before' and before == "":
                    before = args[counter + 1]
                    counter += 2
                else:
                    sys.exit("error: multiple -after or -before options")
            else:
                sys.exit("error: not found good argument after -after or -before")
        else:
            sys.exit("error: not found any argument after -after or -before please use -after/before YYYYMMDD or YYYYMMDDTHHMMSS notations.")
    elif args[counter] == '-match':
        if counter + 1 != len(args):
            try:
                re.compile(args[counter+1])  # compiles given pattern if error happens jump to except and mak is valid false
                is_valid = True
            except re.error:
                is_valid = False
            if is_valid:
                if match == "":

                    match = args[counter+1]

                    counter += 2
                else:
                    sys.exit("error: multiple -match options")
            else:
                sys.exit("error: not found good argument after -match option")
        else:
            sys.exit("error: not found any argument after -match option please use -match <validregex> notation.")
    elif args[counter] == '-zip':
        if counter + 1 != len(args):
            found = re.match("^.*\.zip$",args[counter+1]) # if argument after -zip contains .zip at the end
            if found:
                if zipFile == "":
                    zipFile = args[counter + 1]
                    counter += 2
                else:
                    sys.exit("error: multiple -zip options")
            else:
                sys.exit("error: not found good argument after -zip option please use -zip *.zip notation.")
        else:
            sys.exit("error: not found any argument after -zip option")
    elif args[counter] == '-delete': # these don't take extra argument after them, easier
        if not delete:
            delete = True
            counter += 1
        else:
            sys.exit("error: multiple -delete options")
    elif args[counter] == '-duplcont':
        if not duplcont:
            duplcont = True
            counter += 1
        else:
            sys.exit("error: multiple -duplcont options")
    elif args[counter] == '-duplname':
        if not duplname:
            duplname = True
            counter += 1
        else:
            sys.exit("error: multiple -duplname options")
    elif args[counter] == '-stats':
        if not stats:
            stats = True
            counter += 1
        else:
            sys.exit("error: multiple -stats options")
    elif args[counter] == '-nofilelist':
        if not nofilelist:
            nofilelist = True
            counter += 1
        else:
            sys.exit("error: multiple -nofilelist options")
    else:
        break # then we expect that the remaining arguments are all directory paths.

paths = []
while counter < len(args):
    paths.append(args[counter]) # after taking options we assume everything is a path. If it is not a proper path program will complain cannot open path in run()
    counter += 1
if len(paths)==0: # If no path is given search current directory
    pwd = commands.getoutput("pwd")
    paths.append(pwd)
run(paths) # final function that we call after setting up everything