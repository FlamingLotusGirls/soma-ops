README - new_schedule.py

I've reworked the original scheduler in python for a couple reasons -
a) More people know python than know perl, which makes maintenance easier. (this includes me)
b) I wanted to modify it so that we wouldn't need a sunset/sunrise file, and could simply calculate the sunrise and sunset off of the latitude and longitude. (Note that this does create a dependency on having the correct timezone)

I've also added the concept of a 'default' schedule, one that will automatically match the current day. For SOMA, this means that the schedule file can now reduce to
default  sunset-20 2:00am

The new scheduler takes as inputs two files, a schedule file (same as before), and a lat/long configuration file so that it can properly calculate the current day's sunrise and sunset time. These two files can be found in the conf directory. Note that the longitude is *negative* to the west, opposite of what most of the world uses. Um. Maybe the person who first wrote the code at NOAA was left-handed? Speaking of the NOAA code, a separate Python library, sunCalcs.py, is required. It's been translated from old NOAA Javascript into python, and should be checked into this repo. You can just run sunCalcs.py stand alone if you'd like to convince yourself that it really can determine sunrise and sunset.

--CSW, 9/2014

