#!/usr/bin/python
# vi:set ai sw=4 ts=4 et:
##
## 9/2014, CSW for the Flaming Lotus Girls
## Based on previous Perl code, but adding support for sunrise/sunset calculations
## and a default schedule when the day hasn't been specified
##

import re
import string
import datetime
import sunCalcs
from optparse import OptionParser
from subprocess import call
import sys
import time

# globals
schedules = None
default_schedule = None
latitude = 0.0
longitude = 0.0
debug = False


def parse_relative_time(year, month, day, relativetime):
    '''Accepts "HH:MM", "sunset", "sunrise"
      "sunset-MIN", "sunrise-MIN", sunset+MIN, or "sunrise-MIN" '''
    global latitude, longitude
    is_sunset = re.compile("^sunset").match(relativetime)
    is_sunrise = re.compile("^sunrise").match(relativetime)
    is_time = re.compile("^\d?\d:\d\d[am|pm|AM|PM]").match(relativetime)
    the_time = None;
    #print year, month, day, relativetime, "sunrise", is_sunrise, "sunset", is_sunset, "date", is_date
    if is_sunset:
        sunrise,sunset = sunCalcs.calcSun(latitude, longitude, datetime.date(int(year), int(month), int(day)))
        try:
            offset_minutes=int(relativetime[6:])
        except:
            offset_minutes = 0
        the_time = sunset + (offset_minutes*60)
    elif is_sunrise:
        sunrise,sunset = sunCalcs.calcSun(latitude, longitude, datetime.date(int(year), int(month), int(day)))
        try:
            offset_minutes=int(relativetime[7:])
        except:
            offset_minutes = 0
        the_time = sunrise + (offset_minutes*60)
    elif is_time:
        hour, minampm = string.split(relativetime, ":")
        min = minampm[0:2]
        ampm = minampm[2:4].lower()
        
        if ampm == "pm":
            hour = int(hour) + 12
        the_time = time.mktime([int(year), int(month), int(day), int(hour), int(min), 0, 0, 0, -1])
        
    return the_time


def read_config_file(config_file_name):
    ''' Read latitude and longitude from configuration file. Note that longitude is 
        positive *west*, the reverse of normal'''
    global latitude
    global longitude
    with open(config_file_name) as myfile:
        for line in myfile:
            name, var = line.partition("=")[::2]
            if name:
                if name.lower() == "latitude":
                    latitude = float(var)
                elif name.lower() == "longitude":
                    longitude = float(var)

def read_schedule_file(schedule_file_name):
    ''' Read schedule file and output a list of schedules in canonical form.
        Schedule file can have multiple lines, with each line expressed as 
        <date> <start-time> <end-time>. <date> is either in the format YYYY-MM-DD, or is
        the special value "default" (explained later). <start-time> and <end-time> are 
        represented as a local time in HH:MM format, or one of the special values 
        "sunrise+MIN", "sunrise-MIN", "sunset+MIN", "sunset-MIN".
        Canonical form is [starttime, endtime], where both starttime and endtime are
        expressed in UTC
        If there is a "default" date value specified in the schedule file, the function 
        will also generate a canonical schedule for the current day'''
    global schedules
    global default_schedule
    schedule_file = open(schedule_file_name, "r")
    p = re.compile("\d\d\d\d-\d\d-\d\d")
    schedules = []
    try:
        for line in schedule_file:
            args1 = string.split(line)
            if len(args1) != 3:
                continue 
        
            the_date = args1[0]
            start_time = args1[1]
            end_time = args1[2]
        
            if the_date == "default":
                today = datetime.date.today()
                start_time_UTC = parse_relative_time(today.year, today.month, today.day, start_time)
                end_time_UTC   = parse_relative_time(today.year, today.month, today.day, end_time)
                if (end_time_UTC < start_time_UTC):
                    tomorrow = today + datetime.timedelta(days=1)
                    end_time_UTC   = parse_relative_time(tomorrow.year, tomorrow.month, tomorrow.day, end_time)              
                default_schedule = {"start":start_time_UTC, "end":end_time_UTC}
            elif p.match(the_date):
                year, month, day = string.split(the_date, "-")
                start_time_UTC = parse_relative_time(year, month, day, start_time)
                end_time_UTC   = parse_relative_time(year, month, day, end_time)
                if (end_time_UTC < start_time_UTC): 
                    tomorrow = datetime.date(int(year),int(month),int(day)) + datetime.timedelta(days=1)
                    end_time_UTC   = parse_relative_time(tomorrow.year, tomorrow.month, tomorrow.day, end_time)   
                # push onto schedules
                schedules.append({"start": start_time_UTC, "end":end_time_UTC})
            else:
                pass
    except:
        print "Trouble parsing schedule, line", line
    

def disposition(now):
    ''' Determine whether the system should be on at this particular point in time.'''
    #now = datetime.utcnow()
    global default_schedule, schedules
    if (default_schedule["start"] <= now and default_schedule["end"] > now):
        return True
    for schedule in schedules:
        if (schedule["start"] <= now and schedule["end"] > now):
            return True
    return False
        

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("--schedule", dest="schedule_file", default="/etc/soma/schedule.conf",
                       help="File to read schedule data from. Default /etc/soma/schedule.conf")
    parser.add_option("--config", dest="config_file", default="/etc/soma/global.conf",
                       help="File to read config data from. Default /etc/soma/global.conf")
    parser.add_option("--start", dest="start_cmd",
                       help="Command to run when schedule says system should be ON. Required.")
    parser.add_option("--stop", dest="stop_cmd",
                       help="Command to run when schedule says system should be OFF. Required.")
    parser.add_option("--status", dest="status_cmd",
                       help="Command to run to find out if sysem is ON or OFF.")
    parser.add_option("--unixtime", dest="timenow",
                       help="In dry run mode, set timestamp of 'current' time")
    parser.add_option("--dry-run", dest="dry_run", default=False, action="store_true",
                       help="Do a dry run")
    parser.add_option("--debug", dest="debug", default=False, action="store_true", 
                       help="Turn debugging printouts on")
    
    options, args = parser.parse_args()
    
    if not options.start_cmd or not options.stop_cmd:
        print "\n*** Start and stop commands required ***\n"
        parser.print_help()
        sys.exit()
    
    if not options.timenow:
        timenow = datetime.datetime.utcnow()
    
    try:
        read_config_file(options.config_file)
        if options.debug:
            print "POSITION:\n", "latitude:", latitude, "longitude:", longitude, "\n"
    except:
        print "Cannot read config file", options.config_file
        sys.exit()
        
    if options.debug:
        print "TIMEZONE:", time.strftime("%z", time.gmtime()), "\n"

        
    try:
        read_schedule_file(options.schedule_file)
        if options.debug:
            print "Schedules are:"
            timeStr = '%m-%d-%Y %I:%M%p'
            for schedule in schedules:
                print "START", datetime.datetime.fromtimestamp(schedule["start"]).strftime(timeStr),\
                     " STOP", datetime.datetime.fromtimestamp(schedule["end"]).strftime(timeStr)
            print "\nDefault schedule for today is:"
            print "START", datetime.datetime.fromtimestamp(default_schedule["start"]).strftime(timeStr),\
                  " STOP", datetime.datetime.fromtimestamp(default_schedule["end"]).strftime(timeStr), "\n"
    except:
        print "Cannot read schedule file", options.schedule_file
        print sys.exc_info()[0]
        sys.exit()
    
    if options.status_cmd:
        status = call(options.status_cmd)
        if options.debug:
            print ("System is currently", status)
        
    if disposition(options.timenow):
        if options.debug:
            print "System should be ON"
        if not options.status_cmd or status != 1:
            if options.dry_run:
                print "I would have run START command", options.start_cmd
            else:
                if options.debug:
                    print "Turning system ON"
                call(options.start_cmd)
    else:
        if options.debug:
            print "System should be OFF"
        if not options.status_cmd or status != 0:
            if options.dry_run:
                print "I would have run STOP command", options.stop_cmd
            else:
                if options.debug:
                    print "Turning system OFF"
                call(options.stop_cmd)
    

'''
__DATA__
2014-04-01	7:32pm	11:00pm
2014-04-02	7:33pm	10:00pm
2014-04-03	7:34pm	2:00am
2014-04-04	sunset	2:00am
2014-04-29	sunset	4:42am
'''
