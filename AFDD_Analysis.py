import os, sys, math, string
import numpy as np
import datetime as dt

##change cwd to location of python file (AFDD_Analysis.py)
os.chdir(os.path.dirname(sys.argv[0]))

##Metric or English units?  To determine variables.
unitQ = 0
while unitQ == 0:
    unitQ = "metric" ##str(raw_input("Please choose English or Matric units: \n"))
    print "type = ",type(unitQ),", ",unitQ
    if string.lower(unitQ)[0] == "e":
        units = 0           ##Units are English
        frzT = 32
    elif string.lower(unitQ)[0] == "m":
        units = 1           ##Units are Metric
        frzT = 0
    else:
        print "Please choose a valid system of units: English or Metric"
        unitQ = 0

if units == 0:
    print "\n"
    print "Windy lake with snow\t0.8\n\
Average lake with snow\t0.5 - 0.7\n\
Average river with snow\t0.4 - 0.5\n\
Sheltered small river\n\
  with rapid flow\t0.2 - 0.4"
    print "\n"
    alpha = 0.2 ##float(raw_input("Please choose a value for the parameter alpha: \t"))
else:
    print "\n"
    print "Windy lake with snow\t2.7\n\
Average lake with snow\t1.7 - 2.4\n\
Average river with snow\t1.4 - 1.7\n\
Sheltered small river\n\
  with rapid flow\t0.7 - 1.4"
    print "\n"
    alpha = 0.7 ##float(raw_input("Please choose a value for the parameter alpha: \t"))
    

##open data file is cwd, specified by the user
print 'Please specify the data file to process: '
fileName = "testinput.csv" ##str(raw_input())
f = open(fileName, 'r+')

##read file into list; break list into array of important data
readFile = f.readlines()
f.close()

##setup list with dates
bothDates = [(readFile[0].split(','))[0],(readFile[-1].split(','))[0]]
for dat in range(2): ##break both dates into year,month,day
    bothDates[dat] = dt.date(int(bothDates[dat][:4]) ,int(bothDates[dat][4:6]), int(bothDates[dat][6:]))

#Build array of raw data and AFDD analysis
#C1: date; C2: max temp; C3: min temp; C4: avg temp; C5: AFDD; C6: ice thickness
afdd = np.ones((len(readFile),len(readFile[0].split(','))+3))*-9999

##Intialize variables/triggers
line = 0
yearTrigger = 1  ## If trigger = 1, update bounding dates
afddTrigger = 1
afddTrigDate = dt.date.today()

while line < len(readFile):
    splitLine = readFile[line].split(',')
    
    lineDate = dt.date(int(splitLine[0][:4]),int(splitLine[0][4:6]),int(splitLine[0][6:]))  

    if yearTrigger == 1:                                               ##set bounding dates
        if lineDate < dt.date(int(splitLine[0][:4]),9,1):              ##If current date before 9/30, lower date is 
            dateLower = lineDate                                       ##current date of current year
        else: dateLower = dt.date(int(splitLine[0][:4]),9,1)           ##Else lower date is 9/30 of current year
        dateUpper = dt.date(dateLower.year+1,8,31)                     ##Upper date is 8/31 of next year
        yearTrigger = 0
        print "date Lower = ",dateLower,", date Upper = ",dateUpper

    afdd[line,0] = int(splitLine[0])                                    ##Date column
    if int(splitLine[1]) != -9999 and int(splitLine[2]) != -9999:
        afdd[line,1] = float(splitLine[1])/10.                          ##Max Temp column
        afdd[line,2] = float(splitLine[2])/10.                          ##Min Temp column
        afdd[line,3] = (afdd[line,1]+afdd[line,2])/2.                   ##Average Temp column
    else: afdd[line,1], afdd[line,2], afdd[line,3] = None, None, None

##################################################        
    ##Part 1
    if lineDate >= dateLower and lineDate <= dateUpper and afdd[line,3] <= 0. and afdd[line,2] != -9999 and afdd[line,3] != -9999 and afddTrigger == 1:
        afddTrigger = 0
        afddTrigDate = lineDate
        afdd[line,4] = frzT - afdd[line,3]                              ##Accumulated Freezing Degree Days 
        afdd[line,5] = math.sqrt(afdd[line,4]) * alpha                  ##Assume least amount of ice formation  
        afddTrigLn = line                                               ##Set as reference line for future nan's
        print "part 1: date = ",lineDate,", temp = ",afdd[line,3],", afdd = ",afdd[line,4]
    ##Part 2
    elif afddTrigger == 0 and lineDate > afddTrigDate:
        if np.isnan(afdd[line-1,4]) or np.isnan(afdd[line,3]):
            afdd[line,4] = (frzT-afdd[line,3]) + afdd[afddTrigLn,4]
            if not np.isnan(afdd[line,3]): afddTrigLn = line
            print "part 2a: date = ",lineDate,", temp = ",afdd[line,3],", afdd = ",afdd[line,4]
        else:
            afdd[line,4] = (frzT-afdd[line,3]) + afdd[line-1,4]
            afddTrigLn = line                                           ##Save line incase next is NAN
            print "part 2b: date = ",lineDate,", temp = ",afdd[line,3],", afdd = ",afdd[line,4]
        try:
            afdd[line,5] = math.sqrt(afdd[line,4])*alpha                ##Try calc. of ice thickness
        except:
            ##Exceptions should only be raised if the AFDD is negative (cannot take sq. root)
            ##Therefore, take sq. root of abs of AFDD, then return to negative for ice thickness calculation
            afdd[line,5] = -(math.sqrt(abs(afdd[line,4])))*alpha
    ##Part 3
    elif afddTrigger == 1:
        afdd[line,4], afdd[line,5] = None, None
        print "part 3: date = ",lineDate,", temp = ",afdd[line,3],", afdd = ",afdd[line,4]
    if line >= 3290:
        print "afddTrigger: ",afddTrigger
        print "yearTrigger: ",yearTrigger
        
##################################################

    if afdd[line,5] < 0:
        afddTrigger = 1                                                 ##If AFDD goes negative, begin new AFDD calculation

##Update yearTrigger if last year of date range reached    
    if lineDate >= dateUpper:
        yearTrigger = 1
        if lineDate > dateUpper: line -= 1  ##If multiple years skipped, may not trigger changes to afdd
                                            ##rerun this line with date range forced to update 
    line += 1   ##Go to next line

if line == len(readFile):
    print 'Beginning output'
    ##print os.getcwd()
    name = fileName[:-4] + '_output.csv'
    f2 = open(name,'w+')
    f2.write("Date,Min Temp,Max Temp,Mean Temp,AFDD,Ice Thickness\n")
    if units == 0:                                                      ##Units are English
        f2.write("YYYYMMDD,  Deg. F,  Deg. F,  Deg. F,  Days,   in.\n")
    else: f2.write("YYYYMMDD,  Deg. C,  Deg. C,  Deg. C,  Days,   cm\n")##Units are metric
    for i in range(len(readFile)):
        lineOut = str(afdd[i,0])+','+str(afdd[i,1])+','+str(afdd[i,2])+','+str(afdd[i,3])+','+str(afdd[i,4])+','+str(afdd[i,5])+'\n'
        f2.write(lineOut)
    f2.close()
    print 'Completed output generation'
