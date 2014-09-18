
#
#   NOAA Improved Sunrise/Sunset Calculations
#   Converted into Python by csw, 2014
#

# import python logging?


import math
import time
import datetime
import calendar
from optparse import OptionParser

#**********************************************************************
#**********************************************************************
#												
# This section contains utility functions used in calculating solar position 
#												
#**********************************************************************
#**********************************************************************

# Convert radian angle to degrees
def radToDeg(angleRad):
    return (180.0 * angleRad / math.pi)

# Convert degree angle to radians
def degToRad(angleDeg):
    return (math.pi * angleDeg / 180.0)




def calcJD(year, month, day):
    ''' Create Julian Day from Calendar Day.
    @year  : 4-digit year
    @month : January = 1
    @day   : 1-31
    Note that return value is the start of the day. Fractional days should be
    added later '''   
    if (month <= 2):
        year -= 1
        month += 12

    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)

    JD = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5;
    return JD


def calcTimeJulianCent(jd) :
    ''' Convert Julian Day to centuries since J2000.0.
        @jd : the Julian Day to convert.
        Returns: the T value corresponding to the Julian Day '''
    T = (jd - 2451545.0) / 36525.0
    return T


def calcJDFromJulianCent(t):
    '''Convert centuries since J2000.0 to Julian Day.
    @t : number of Julian centuries since J2000.0
    Returns: the Julian Day corresponding to the t value'''
    JD = t * 36525.0 + 2451545.0
    return JD


def calcGeomMeanLongSun(t):
    '''Calculate the Geometric Mean Longitude of the Sun
    @t : number of Julian centuries since J2000.0
    Returns: the Geometric Mean Longitude of the Sun in degrees'''
    L0 = 280.46646 + t * (36000.76983 + 0.0003032 * t)
    while (L0 > 360.0):
        L0 -= 360.0
    
    while (L0 < 0.0):
        L0 += 360.0
    
    return L0        # in degrees
    

def calcGeomMeanAnomalySun(t):
    '''Calculate the Geometric Mean Anomaly of the Sun
    @t : number of Julian centuries since J2000.0
    Returns : the Geometric Mean Anomaly of the Sun in degrees'''
    M = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    return M        # in degrees


def calcEccentricityEarthOrbit(t):
    '''Calculate the eccentricity of earth's orbit
    @t : number of Julian centuries since J2000.0
    Returns: the unitless eccentricity'''
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    return e;        # unitless


def calcSunEqOfCenter(t):
    '''Calculate the equation of center for the sun
    @t : number of Julian centuries since J2000.0
    Returns: in degrees'''
    m = calcGeomMeanAnomalySun(t)

    mrad = degToRad(m)
    sinm = math.sin(mrad)
    sin2m = math.sin(mrad + mrad)
    sin3m = math.sin(mrad + mrad + mrad)

    C = sinm * (1.914602 - t * (0.004817 + 0.000014 * t)) + sin2m * (0.019993 - 0.000101 * t) + sin3m * 0.000289
    return C        # in degrees


def calcSunTrueLong(t): 
    '''Calculate the true longitude of the sun
    @t : number of Julian centuries since J2000.0
    Returns : sun's true longitude in degrees'''
    l0 = calcGeomMeanLongSun(t)
    c = calcSunEqOfCenter(t)

    O = l0 + c
    return O        # in degrees
    

def calcSunTrueAnomaly(t): 
    '''Calculate the true anamoly of the sun
    @t : number of Julian centuries since J2000.0
    Returns: sun's true anamoly in degrees'''
    m = calcGeomMeanAnomalySun(t)
    c = calcSunEqOfCenter(t)

    v = m + c
    return v        # in degrees


def calcSunRadVector(t): 
    ''' Calculate the distance to the sun in AU
    @t : number of Julian centuries since J2000.0
    Returns : sun radius vector in AUs'''
    v = calcSunTrueAnomaly(t)
    e = calcEccentricityEarthOrbit(t)

    R = (1.000001018 * (1 - e * e)) / (1 + e * math.cos(degToRad(v)))
    return R        # in AUs
    

def calcSunApparentLong(t): 
    '''Calculate the apparent longitude of the sun
    @t : number of Julian centuries since J2000.0
    Returns : sun's apparent longitude in degrees'''
    o = calcSunTrueLong(t)

    omega = 125.04 - 1934.136 * t
    lmbda = o - 0.00569 - 0.00478 * math.sin(degToRad(omega))
    return lmbda        # in degrees
    

def calcMeanObliquityOfEcliptic(t): 
    '''Calculate the mean obliquity of the ecliptic
    @t : number of Julian centuries since J2000.0
    Returns: mean obliquity in degrees'''
    seconds = 21.448 - t * (46.8150 + t * (0.00059 - t * (0.001813)))
    e0 = 23.0 + (26.0 + (seconds / 60.0)) / 60.0
    return e0        # in degrees
    

def calcObliquityCorrection(t): 
    '''Calculate the corrected obliquity of the ecliptic
    @t : number of Julian centuries since J2000.0
    Returns: corrected obliquity in degrees'''
    e0 = calcMeanObliquityOfEcliptic(t)

    omega = 125.04 - 1934.136 * t
    e = e0 + 0.00256 * math.cos(degToRad(omega))
    return e        # in degrees
    

def calcSunRtAscension(t): 
    '''Calculate the right ascension of the sun
    @t : number of Julian centuries since J2000.0
    Returns : sun's right ascension in degrees'''
    e = calcObliquityCorrection(t)
    lmbda = calcSunApparentLong(t)

    tananum = (math.cos(degToRad(e)) * math.sin(degToRad(lmbda)))
    tanadenom = (math.cos(degToRad(lmbda)))
    alpha = radToDeg(math.atan2(tananum, tanadenom))
    return alpha        # in degrees
    


def calcSunDeclination(t):
    '''Calculate the declination of the sun.
    @t : number of Julian centuries since J2000.0
    Returns : sun's declination in degrees'''
    e = calcObliquityCorrection(t)
    lmbda = calcSunApparentLong(t)

    sint = math.sin(degToRad(e)) * math.sin(degToRad(lmbda))
    theta = radToDeg(math.asin(sint))
    return theta        # in degrees
    

def calcEquationOfTime(t): 
    '''Calculate the difference between true solar time and mean solar time.
    @t : number of Julian centuries since J2000.0
    Returns : equation of time in minutes of time'''
    epsilon = calcObliquityCorrection(t)
    l0 = calcGeomMeanLongSun(t)
    e = calcEccentricityEarthOrbit(t)
    m = calcGeomMeanAnomalySun(t)

    y = math.tan(degToRad(epsilon) / 2.0)
    y *= y

    sin2l0 = math.sin(2.0 * degToRad(l0))
    sinm = math.sin(degToRad(m))
    cos2l0 = math.cos(2.0 * degToRad(l0))
    sin4l0 = math.sin(4.0 * degToRad(l0))
    sin2m = math.sin(2.0 * degToRad(m))

    Etime = y * sin2l0 - 2.0 * e * sinm + 4.0 * e * y * sinm * cos2l0 - 0.5 * y * y * sin4l0 - 1.25 * e * e * sin2m

    return radToDeg(Etime) * 4.0    # in minutes of time
    

def calcHourAngleSunrise(lat, solarDec):
    '''Calculate the hour angle of the sun at sunrise for the latitude
    @lat : latitude of observer in degrees
    @solarDec : declination angle of sun in degrees
    Returns : hour angle of sunrise in radians'''
    latRad = degToRad(lat)
    sdRad = degToRad(solarDec)

    HAarg = (math.cos(degToRad(90.833)) / (math.cos(latRad) * math.cos(sdRad)) - math.tan(latRad) * math.tan(sdRad))

    HA = (math.acos(math.cos(degToRad(90.833)) / (math.cos(latRad) * math.cos(sdRad)) - math.tan(latRad) * math.tan(sdRad)))

    return HA        # in radians
    

def calcHourAngleSunset(lat, solarDec) :
    '''Calculate the hour angle of the sun at sunset for the latitude
    @lat : latitude of observer in degrees
    @solarDec : declination angle of sun in degrees
    Returns : hour angle of sunset in radians'''
    latRad = degToRad(lat)
    sdRad = degToRad(solarDec)

    HAarg = (math.cos(degToRad(90.833)) / (math.cos(latRad) * math.cos(sdRad)) - math.tan(latRad) * math.tan(sdRad))

    HA = (math.acos(math.cos(degToRad(90.833)) / (math.cos(latRad) * math.cos(sdRad)) - math.tan(latRad) * math.tan(sdRad)))

    return -HA        # in radians
    


def calcSunriseUTC(JD, latitude, longitude):
    '''Calculate the Universal Coordinated Time (UTC) of sunrise for the given day 
    at the given location on earth.
    @JD  : julian day
    @latitude : latitude of observer in degrees
    @longitude : longitude of observer in degrees
    Returns : time in minutes from zero Z'''
    t = calcTimeJulianCent(JD)

    # *** Find the time of solar noon at the location, and use
    #     that declination. This is better than start of the
    #     Julian day
    noonmin = calcSolNoonUTC(t, longitude)
    tnoon = calcTimeJulianCent(JD + noonmin / 1440.0)

    # *** First pass to approximate sunrise (using solar noon)
    eqTime = calcEquationOfTime(tnoon)
    solarDec = calcSunDeclination(tnoon)
    hourAngle = calcHourAngleSunrise(latitude, solarDec)

    delta = longitude - radToDeg(hourAngle)
    timeDiff = 4 * delta    # in minutes of time
    timeUTC = 720 + timeDiff - eqTime    # in minutes

    # alert("eqTime = " + eqTime + "\nsolarDec = " + solarDec + "\ntimeUTC = " + timeUTC)

    # *** Second pass includes fractional jday in gamma calc

    newt = calcTimeJulianCent(calcJDFromJulianCent(t) + timeUTC / 1440.0)
    eqTime = calcEquationOfTime(newt)
    solarDec = calcSunDeclination(newt)
    hourAngle = calcHourAngleSunrise(latitude, solarDec)
    delta = longitude - radToDeg(hourAngle)
    timeDiff = 4 * delta
    timeUTC = 720 + timeDiff - eqTime # in minutes

    # alert("eqTime = " + eqTime + "\nsolarDec = " + solarDec + "\ntimeUTC = " + timeUTC)

    return timeUTC  # XXX what about NaN?  This function is allowed to return NaN.
    

def calcSolNoonUTC(t, longitude) :
    '''Calculate the Universal Coordinated Time (UTC) of solar noon for the given day
     at the given location on earth.
    @t : number of Julian centuries since J2000.0
    @longitude : longitude of observer in degrees
    Returns: time in minutes from start of day in UTC'''
    # First pass uses approximate solar noon to calculate eqtime
    tnoon = calcTimeJulianCent(calcJDFromJulianCent(t) + longitude / 360.0)
    eqTime = calcEquationOfTime(tnoon)
    solNoonUTC = 720 + (longitude * 4) - eqTime # min

    newt = calcTimeJulianCent(calcJDFromJulianCent(t) - 0.5 + solNoonUTC / 1440.0)

    eqTime = calcEquationOfTime(newt)
    # var solarNoonDec = calcSunDeclination(newt)
    solNoonUTC = 720 + (longitude * 4) - eqTime # min

    return solNoonUTC
    

def calcSunsetUTC(JD, latitude, longitude):
    '''Calculate the Universal Coordinated Time (UTC) of sunset	for the given day at 
    the given location on earth.
    @JD  : julian day
    @latitude : latitude of observer in degrees	
    @longitude : longitude of observer in degrees
    Retuns : time in minutes from zero Z'''
    t = calcTimeJulianCent(JD)

    # *** Find the time of solar noon at the location, and use
    #     that declination. This is better than start of the
    #     Julian day

    noonmin = calcSolNoonUTC(t, longitude)
    tnoon = calcTimeJulianCent(JD + noonmin / 1440.0)

    # First calculates sunrise and approx length of day

    eqTime = calcEquationOfTime(tnoon)
    solarDec = calcSunDeclination(tnoon)
    hourAngle = calcHourAngleSunset(latitude, solarDec)

    delta = longitude - radToDeg(hourAngle)
    timeDiff = 4 * delta
    timeUTC = 720 + timeDiff - eqTime

    # first pass used to include fractional day in gamma calc

    newt = calcTimeJulianCent(calcJDFromJulianCent(t) + timeUTC / 1440.0)
    eqTime = calcEquationOfTime(newt)
    solarDec = calcSunDeclination(newt)
    hourAngle = calcHourAngleSunset(latitude, solarDec)

    delta = longitude - radToDeg(hourAngle)
    timeDiff = 4 * delta
    timeUTC = 720 + timeDiff - eqTime # in minutes

    return timeUTC



def findRecentSunrise(jd, latitude, longitude): 
    '''Calculate the julian day of the most recent sunrise starting from the given day 
    at the given location on earth.
    @JD  : julian day
    @latitude : latitude of observer in degrees
    @longitude : longitude of observer in degrees
    Returns : julian day of the most recent sunrise'''
    julianday = jd

    time = calcSunriseUTC(julianday, latitude, longitude)
    while ( not isNumber(time)):  # XXX how is this going to work?
        julianday -= 1.0
        time = calcSunriseUTC(julianday, latitude, longitude)

    return julianday


def isNumber(number):
    return not math.isinf(number) and not math.isnan(number)
    

def findRecentSunset(jd, latitude, longitude):
    '''Calculate the julian day of the most recent sunset starting from the given day at 
    the given location on earth.
    @JD  : julian day
    @latitude : latitude of observer in degrees
    @longitude : longitude of observer in degrees
    Returns : julian day of the most recent sunset'''
    julianday = jd

    time = calcSunsetUTC(julianday, latitude, longitude)
    while (not isNumber(time)):
        julianday -= 1.0
        time = calcSunsetUTC(julianday, latitude, longitude)
 
    return julianday
    


def findNextSunrise(jd, latitude, longitude):
    '''Calculate the julian day of the next sunrise starting from the given day at 
    the given location on earth.
    @JD  : julian day
    @latitude : latitude of observer in degrees
    @longitude : longitude of observer in degrees
    Returns : julian day of the next sunrise'''
    julianday = jd

    time = calcSunriseUTC(julianday, latitude, longitude)
    while (not isNumber(time)):
        julianday += 1.0
        time = calcSunriseUTC(julianday, latitude, longitude)

    return julianday
    


def findNextSunset(jd, latitude, longitude):
    '''Calculate the julian day of the next sunset starting from the given day at 
    the given location on earth.
    @JD  : julian day
    @latitude : latitude of observer in degrees
    @longitude : longitude of observer in degrees
    Returns : julian day of the next sunset'''
    julianday = jd

    time = calcSunsetUTC(julianday, latitude, longitude)
    while (not isNumber(time)):
        julianday += 1.0
        time = calcSunsetUTC(julianday, latitude, longitude)

    return julianday
    

def timeString(minutes):
    '''Convert time of day in minutes to a zero-padded string suitable for printing 
    to the form text fields.
    @minutes : time of day in minutes
    Returns : string of the format HH:MM:SS, minutes and seconds are zero padded'''

    floatHour = minutes / 60.0
    hour = math.floor(floatHour)
    floatMinute = 60.0 * (floatHour - math.floor(floatHour))
    minute = math.floor(floatMinute)
    floatSec = 60.0 * (floatMinute - math.floor(floatMinute))
    second = math.floor(floatSec + 0.5)
    if (second > 59):
        second = 0
        minute += 1  

    timeStr = (str(hour)) + ":"
    if (minute < 10):    #	i.e. only one digit
        timeStr += "0" + str(minute) + ":"
    else:
        timeStr += str(minute) + ":"
    if (second < 10):    #	i.e. only one digit
        timeStr += "0" + str(second)
    else:
        timeStr += str(second)

    return timeStr
    
############################################################
# 
# Exported Functions here
# 
#############################################################
def calcNextSun(latitude, longitude, date):
    '''Calculate next sunrise and sunset, after current time, given the entered
    location.  In the special cases near earth's poles the date of nearest sunrise 
    and set are reported.
    @latitude : latitude of observer in degrees
    @longitude : longitude of observer in degrees
    Returns: riseTime, setTime - UTC timestamp tuple'''
    
    # set up base dates for passed in date, as well as next and previous dates  
    oneDay = datetime.timedelta(days=1)

    todayDate = date
    tomorrowDate = todayDate + oneDay
    yesterdayDate = todayDate - oneDay

    todayBaseDate = calendar.timegm([todayDate.year, todayDate.month, todayDate.day,0,0,0])
    tomorrowBaseDate = calendar.timegm([tomorrowDate.year, tomorrowDate.month, tomorrowDate.day,0,0,0])
    yesterdayBaseDate = calendar.timegm([yesterdayDate.year, yesterdayDate.month, yesterdayDate.day,0,0,0])
      
    JDToday     = calcJD(todayDate.year,     todayDate.month,     todayDate.day)
    JDTomorrow  = calcJD(tomorrowDate.year,  tomorrowDate.month,  tomorrowDate.day)
    JDYesterday = calcJD(yesterdayDate.year, yesterdayDate.month, yesterdayDate.day)

    # calculate UTC rise and set times for yesterday, today, and tomorrow
    riseSets = [None] * 10
    riseSets[0] = yesterdayBaseDate + calcSunriseUTC(JDYesterday, latitude, longitude) * 60 #* 1000
    riseSets[1] = yesterdayBaseDate + calcSunsetUTC( JDYesterday, latitude, longitude) * 60 #* 1000

    riseSets[2] = todayBaseDate + calcSunriseUTC(JDToday, latitude, longitude) * 60 #* 1000
    riseSets[3] = todayBaseDate + calcSunsetUTC( JDToday, latitude, longitude) * 60  #* 1000

    riseSets[4] = tomorrowBaseDate + calcSunriseUTC(JDTomorrow, latitude, longitude) * 60 #* 1000
    riseSets[5] = tomorrowBaseDate + calcSunsetUTC( JDTomorrow, latitude, longitude) * 60  #* 1000

    # parse through, looking for the pair right after the current date...    
    overTime = 0
    curUTC = time.time()
    for overTime in range(0,6):
        if (riseSets[overTime] > curUTC):
            break
    
    # XXX - What do you do with overtime == 5? I mean, sure, you're fucked. But what do you do?
    if (overTime < 5):
        if (overTime % 2 == 1):
            riseTime = riseSets[overTime + 1]
            setTime = riseSets[overTime]
        else: 
            riseTime = riseSets[overTime]
            setTime  = riseSets[overTime + 1]

    return riseTime, setTime
    

def calcSun(latitude, longitude, date):
    '''Calculate time of sunrise and sunset for the entered date and location.  In the 
    special cases near earth's poles, the date of nearest sunrise and set are reported.
    @latitude : latitude of observer in degrees
    @longitude : longitude of observer in degrees
    @date : date at which to calculate sunrise and sunset
    Returns: riseTime, setTime - UTC timestamp tuple'''

    baseDate = calendar.timegm([date.year, date.month, date.day,0,0,0]) # UTC time at the beginning of the day

    if ((latitude >= -90) and (latitude < -89)) :
        #if (log.isDebugEnabled()) log.debug("All latitudes between -89 and -90 N\n will be set to -89")
        latitude = -89
    
    if ((latitude <= 90) and (latitude > 89)) :
        #if (log.isDebugEnabled()) log.debug("All latitudes between 89 and 90 N\n will be set to 89")
        latitude = 89
    

    # Calculate the time of sunrise

    JD = calcJD(date.year, date.month, date.day)

    doy = date.timetuple().tm_yday # XXX does this work?

    # these below are not part of the calculation
    #T = calcTimeJulianCent(JD)
    #alpha = calcSunRtAscension(T)
    #theta = calcSunDeclination(T)
    #Etime = calcEquationOfTime(T)
    #eqTime = Etime
    #solarDec = theta

    # Calculate sunrise for this date
    # if no sunrise is found, set flag nosunrise
    nosunrise = False
    riseTimeGMT = calcSunriseUTC(JD, latitude, longitude)
    if (not isNumber(riseTimeGMT)):
        nosunrise = True    

    # Calculate sunset for this date
    # if no sunset is found, set flag nosunset
    nosunset = False
    setTimeGMT = calcSunsetUTC(JD, latitude, longitude)
    if (not isNumber(setTimeGMT)):
        nosunset = True
    

    if (not nosunrise):       # Sunrise was found
        riseTime = baseDate + riseTimeGMT * 60 # * 1000

    if (not nosunset):        # Sunset was found    
        setTime = baseDate + setTimeGMT * 60 # * 1000

    # Calculate solar noon for this date - for printing only here...
#    solNoonGMT = calcSolNoonUTC(T, longitude)
#    utcSolnStr = timeString(solNoonGMT)

#    tsnoon = calcTimeJulianCent(calcJDFromJulianCent(T) - 0.5 + solNoonGMT / 1440.0)

#    eqTime = calcEquationOfTime(tsnoon)
#    solarDec = calcSunDeclination(tsnoon)



#   if (log.isDebugEnabled()) log.debug(" Equation of time is " + (math.floor(100 * eqTime)) / 100)
#    if (log.isDebugEnabled()) log.debug(" Solar dec is  is " + (math.floor(100 * solarDec)) / 100)

    # report special cases of no sunrise

    if (nosunrise):
        # if Northern hemisphere and spring or summer, OR
        # if Southern hemisphere and fall or winter, use
        # previous sunrise and next sunset
        if (((latitude > 66.4) and (doy > 79) and (doy < 267)) or
                ((latitude < -66.4) and ((doy < 83) or (doy > 263)))):
            newjd = findRecentSunrise(JD, latitude, longitude)
            newtime = calcSunriseUTC(newjd, latitude, longitude) # - (60 * zone) + daySavings
            riseTime = baseDate + newtime * 60 # * 1000
        

        # if Northern hemisphere and fall or winter, OR
        # if Southern hemisphere and spring or summer, use
        # next sunrise and previous sunset

        elif (((latitude > 66.4) and ((doy < 83) or (doy > 263))) or
                ((latitude < -66.4) and (doy > 79) and (doy < 267))): 
            newjd = findNextSunrise(JD, latitude, longitude)
            newtime = calcSunriseUTC(newjd, latitude, longitude)#- (60 * zone) + daySavings # nb - time here is in *minutes*

            riseTime = baseDate + newtime * 60 # * 1000
        else:
            riseTime = 0
#					alert("Cannot Find Sunrise!")
        

        # alert("Last Sunrise was on day " + findRecentSunrise(JD, latitude, longitude))
        # alert("Next Sunrise will be on day " + findNextSunrise(JD, latitude, longitude))

    

    if (nosunset): 
        # if Northern hemisphere and spring or summer, OR
        # if Southern hemisphere and fall or winter, use
        # previous sunrise and next sunset
        if (((latitude > 66.4) and (doy > 79) and (doy < 267)) or
                ((latitude < -66.4) and ((doy < 83) or (doy > 263)))):
            newjd = findNextSunset(JD, latitude, longitude)
            newtime = calcSunsetUTC(newjd, latitude, longitude)# - (60 * zone) + daySavings
            setTime = baseDate + newtime * 60 # * 1000
       
        # if Northern hemisphere and fall or winter, OR
        # if Southern hemisphere and spring or summer, use
        # next sunrise and last sunset
        elif (((latitude > 66.4) and ((doy < 83) or (doy > 263))) or
                ((latitude < -66.4) and (doy > 79) and (doy < 267))):
            newjd = findRecentSunset(JD, latitude, longitude)
            newtime = calcSunsetUTC(newjd, latitude, longitude)#- (60 * zone) + daySavings
            setTime = baseDate + newtime * 60 #* 1000
        else:
            setTime = 0
#					alert ("Cannot Find Sunset!")
        
    
    
    return riseTime, setTime


if __name__ == '__main__':
#    latitude = 37.451688
#    longitude = 122.18305
    
    parser = OptionParser()
    parser.add_option("--lat", dest="latitude", default=37.451688, type="float")
                      
    parser.add_option("--long", dest="longitude", default=122.18305, type="float",
                       help="Positive WEST of meridian.")
    parser.description = "Calculates today's sunrise and sunset for a given latitude and longitude (default, San Francisco)"
                     
    opts, args = parser.parse_args()
                   

    #riseTime, setTime = calcNextSun(latitude, longitude, datetime.date.today())
    riseTime, setTime = calcSun(opts.latitude, opts.longitude, datetime.date.today())
    riseTimeStr = datetime.datetime.fromtimestamp(riseTime).strftime('%Y-%m-%d %H:%M:%S')
    setTimeStr  = datetime.datetime.fromtimestamp(setTime).strftime('%Y-%m-%d %H:%M:%S')
#    riseTime, setTime = calcSun(51.48, 0, datetime.date.today())
    timezone = time.strftime("%z", time.gmtime())
    print "Local timezone:", timezone, " Lat:", opts.latitude, " Long:", opts.longitude
    print "Sunrise:", riseTimeStr + "  Sunset:", setTimeStr




#
# NOTE: For latitudes greater than 72 degrees N and S, calculations are
# accurate to within 10 minutes.  For latitudes less than +/- 72&deg accuracy
# is approximately one minute.  See <a href="./calcdetails.html">Solar Calculation
# Details</a> for further explanation.
# by
# <a href="mailto:&#119&#101&#98&#109&#97&#115&#116&#101&#114-&#115&#114&#114&#98&#46gm&#100&#64n&#111&#97&#97&#46&#103&#111&#118">Chris Cornwall</a>,
# Aaron Horiuchi and Chris Lehman<br>
#

