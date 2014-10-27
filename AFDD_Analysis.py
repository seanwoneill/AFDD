##Scrip to calculate the accumulated freezing degree days (AFDD), and
## estimated ice thickness (based on the Steven formual; thickness =
## alpha * sqrt(AFDD)

import os, sys, math, string
import numpy as np
import datetime as dt


##change cwd to location of python file (AFDD_Analysis.py)
os.chdir(os.path.dirname(sys.argv[0]))


##Metric or English units?  To determine variables.
unitQ = 0
while unitQ == 0:
    unitQ = str(raw_input("Please choose English or Matric units: \n"))
    if string.lower(unitQ)[0] == "e":
        units = 0           ##Units are English
        frzT = 32
    elif string.lower(unitQ)[0] == "m":
        units = 1           ##Units are Metric
        frzT = 0
    else:
        print "Please choose a valid system of units: English or Metric"
        unitQ = 0


##Print table of possible alpha values for use in Steven
## formula (ice thickness = alpha * sqrt(AFDD))
##Ask for user input to establish alpha
if units == 0:
    print "\n"
    print "Windy lake with snow\t0.8\n\
Average lake with snow\t0.5 - 0.7\n\
Average river with snow\t0.4 - 0.5\n\
Sheltered small river\n\
  with rapid flow\t0.2 - 0.4"
    print "\n"
    alpha = float(raw_input("Please choose a value for the parameter alpha: \t"))
else:
    print "\n"
    print "Windy lake with snow\t2.7\n\
Average lake with snow\t1.7 - 2.4\n\
Average river with snow\t1.4 - 1.7\n\
Sheltered small river\n\
  with rapid flow\t0.7 - 1.4"
    print "\n"
    alpha = float(raw_input("Please choose a value for the parameter alpha: \t"))
    

##open data file that's in cwd, specified by the user
print 'Please specify the data file to process: '
fileName = str(raw_input('Please specify the data file to process:\n'))
f = open(fileName, 'r+')


##read file into list; break list into array of important data
readFile = f.readlines()
f.close()


##setup list with dates
bothDates = [(readFile[0].split(','))[0],(readFile[-1].split(','))[0]]
##break both dates into year,month,day
for dat in range(2): 
    bothDates[dat] = dt.date(int(bothDates[dat][:4]) ,int(bothDates[dat][4:6]), int(bothDates[dat][6:]))


#Build array of raw data and AFDD analysis
#C1: date; C2: max temp; C3: min temp; C4: avg temp; C5: AFDD; C6: ice thickness
afdd = np.ones((len(readFile),len(readFile[0].split(','))+3))*-9999


##Intialize variables/triggers
line = 0
yearTrigger = 1  ## If trigger = 1, update bounding dates
afddTrigger = 1
afddTrigDate = dt.date.today()
currentMax = ([0,0],)
annual_Max = ()


while line < len(readFile):
    splitLine = readFile[line].split(',')
    
    lineDate = dt.date(int(splitLine[0][:4]),int(splitLine[0][4:6]),int(splitLine[0][6:]))  

    if yearTrigger == 1:                                               ##set bounding dates
        if lineDate < dt.date(int(splitLine[0][:4]),9,1):              ##If current date before 9/30, lower date is 
            dateLower = lineDate                                       ##current date of current year
        else: dateLower = dt.date(int(splitLine[0][:4]),9,1)           ##Else lower date is 9/30 of current year
        dateUpper = dt.date(dateLower.year+1,8,31)                     ##Upper date is 8/31 of next year
        yearTrigger = 0
        #print "date Lower = ",dateLower,", date Upper = ",dateUpper

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
        afdd[line,5] = math.sqrt(afdd[line,4]) * alpha                  ##Ice formation
        afddTrigLn = line                                               ##Set as reference line for future nan's


    ##Part 2
    elif afddTrigger == 0 and lineDate > afddTrigDate:
        ##Determine column 4 (AFDD)
        if np.isnan(afdd[line-1,4]) or np.isnan(afdd[line,3]):
            afdd[line,4] = (frzT-afdd[line,3]) + afdd[afddTrigLn,4]
            if not np.isnan(afdd[line,3]): afddTrigLn = line
        else:
            afdd[line,4] = (frzT-afdd[line,3]) + afdd[line-1,4]
            afddTrigLn = line                                           ##Save line in case next is NAN

        ##Determine column 5 (Ice thickness)
        if afdd[line,4] >= 0:
            ##Calc ice thickness if AFDD is positive
            afdd[line,5] = math.sqrt(afdd[line,4])*alpha                
        else:
            ##Exceptions will be raised if the AFDD is negatives
            ##Therefore, take sq. root of abs of AFDD, then return to negative for ice thickness calculation
            ##This will reduce the total ice thickness
            afdd[line,5] = -(math.sqrt(abs(afdd[line,4])))*alpha
        

    ##Part 3
    elif afddTrigger == 1:
        afdd[line,4], afdd[line,5] = None, None

        
##################################################


    ##Check if ice thickness is greatest for the year
    if afdd[line,5] > currentMax[-1][1]:
        currentMax = ([lineDate, afdd[line,5]],)


    ##If AFDD goes negative, begin new AFDD calculation
    if afdd[line,5] < 0:
        afddTrigger = 1
        

    ##Update yearTrigger if last year of date range reached    
    if lineDate >= dateUpper:
        yearTrigger = 1
            ##If multiple years skipped, may not trigger changes to afdd
            ##rerun this line with date range forced to update
        if lineDate > dateUpper: line -= 1
            ##Since the year is over,
            ## add the current annual max ice thickness to the annual_Max tuple
        if currentMax[-1][1] != 0:
            annual_Max = annual_Max + currentMax
            ##Reset the current max annual ice thickness to 0 for the coming year
            currentMax = ([0,0],)


    ##Go to next line                                         
    line += 1   


if line == len(readFile):
    print 'Beginning output'
    name = fileName[:-4] + '_output.csv'
    f2 = open(name,'w+')


    ##Print heading based on unit sytems
    f2.write("Date,Min Temp,Max Temp,Mean Temp,AFDD,Ice Thickness\n")
    if units == 0:                                                      ##Units are English
        f2.write("YYYYMMDD,  Deg. F,  Deg. F,  Deg. F,  Days,   in.\n")
    else: f2.write("YYYYMMDD,  Deg. C,  Deg. C,  Deg. C,  Days,   cm\n")##Units are metric


    ##Write the array of raw and analyzed data to the output
    for i in range(len(readFile)):
        lineOut = str(afdd[i,0])+','+str(afdd[i,1])+','+str(afdd[i,2])+','+str(afdd[i,3])+','+str(afdd[i,4])+','+str(afdd[i,5])+'\n'
        f2.write(lineOut)


    ##Write table of maximum annual ice thicknesses
    f2.write("\n\nTable of Maximum Annual Ice Thicknesses\n\
Date,Thickness\n")
    for x in range(len(annual_Max)):
        f2.write(str(annual_Max[x][0])+","+str(annual_Max[x][1])+"\n")

    
    f2.close()
    print 'Completed output generation'
