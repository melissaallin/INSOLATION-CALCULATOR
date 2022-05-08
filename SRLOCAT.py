import math
import csv
import datetime

def SRLOCAT():
    #THIS IS THE PYTHONIZED VERSION OF NASA'S FORTRAN CODE SRLOCAT.FOR
    #CALCULATES INSOLATION AT SPECIFIED LOCATION
    #MODIFICATION LOOKS FOR BEGINNING AND END OF DAYLIGHT SAVINGS TIME
    #SO THAT TIME IS ADJUSTED FOR DST.  JUST BLOCK THAT OUT IF YOU WANT
    #TO STAY WITH STANDARD TIME YEAR ROUND.

    TWOPI = 6.283185307179586477
    EDAYzY = 365.2425
    RSUNd = 0.267   #mean radius of sun in degrees
    REFRAC = 0.583  #effctive sun disk increase
    DAYzMO = [31,28,31,30,31,30,31,31,30,31,30,31]

    #READ INPUT FROM CONSOLE
    print("ENTER LATITUDE IN DEGREES:\n")
    RLAT = float(input())
    while abs(RLAT) > 90:
        print("SPECIFIED LATITUDE IS OUT OF RANGE, MUST BE < 90 DEGREES.\n")
        print("ENTER LATITUDE IN DEGREES:\n")
        RLAT = float(input())
    print("ENTER LONGITUDE IN DEGREES:\n")
    RLON = float(input())
    if RLON > 187.5:
        RLON = RLON - 360
    if RLON < -187.5:
        RLON = RLON + 360
    while abs(RLON) > 187.5:
        print("SPECIFIED LONGITUDE IS OUT OF RANGE:\n")
        print("ENTER LONGITUDE IN DEGREES:\n")
        RLON = float(input())
    print("ENTER YEAR TO BE ANALYZED:\n")
    JYEAR = int(input())
    print("ENTER NUMBER OF MONTH TO BE ANALYZED OR 0 FOR FULL YEAR:\n")
    MONTH = int(input())
    while MONTH < 0 or MONTH > 12:
        print("MONTH VALUE MUST BE IN RANGE 1 TO 12.\n")
        print("ENTER NUMBER OF MONTH TO BE ANALYZED OR 0 FOR FULL YEAR:\n")
        MONTH = int(input())
    if MONTH == 0:
        MONMIN = 0
        MONMAX = 12
    else:
        MONMAX = MONTH
        MONMIN = MONTH - 1

    #DETERMINE TIMEZONE
    ITZONE = int(RLON/15)

    #DETERMINE ORBITAL PARAMETERS
    orb_list = ORBPAR(JYEAR,TWOPI)
    OBLIQ = orb_list[0]
    ECCEN = orb_list[1]
    OMEGVP = orb_list[2]

    #WRITE HEADER INFORMATION TO FILE
    f = open('insolation_data.csv','w')
    writer = csv.writer(f)
    DATA = [RLAT,RLON,JYEAR]
    writer.writerow(DATA)
    colnames = ['YEAR','MONTH','DAY','SUNRISE','SUNSET','DAILY AVERAGE SUNLIGHT (W/m2)','Sunlight Weighted Cosine of Zenith Angle']
    writer.writerow(colnames)
    f.close()
    count = 1

    #LOOP OVER MONTHS
    for MONTH in range(MONMIN,MONMAX):
        DATMAX = DAYzMO[MONTH]
        SUNM = 0
        SUNN = 0
        if MONTH == 1 and QLEAPY(JYEAR):
            DATMAX = 29
        for JDATE in range(1,DATMAX+1):
            DATE = JDATE - 1 + 0.5 - RLON/360
            DAY = YMDtoD(JYEAR,MONTH,DATE)
            orbit_list = ORBIT(ECCEN,OBLIQ,OMEGVP,DAY,TWOPI,EDAYzY)
            SIND = orbit_list[0]
            COSD = orbit_list[1]
            SUNDIS = orbit_list[2]
            EQTIME = orbit_list[3]
            cos_list = COSZIJ(RLAT,SIND,COSD,TWOPI)
            COSZT = cos_list[0]
            COSZS = cos_list[1]
            RSMEZM = (REFRAC + RSUNd/SUNDIS)*TWOPI/360
            DUSK = SUNSET(RLAT,SIND,COSD,RSMEZM,TWOPI)
            JMONTH = MONTH+1
            DDATE = datetime.date(JYEAR,JMONTH,JDATE)
            if MONTH == 2 and DDATE.weekday() == 6:
                SUNM += 1
            if MONTH == 10 and DDATE.weekday() == 6:
                SUNN += 1
            if DUSK >= 999999:  #DAYLIGHT AT ALL TIMES AT THIS LOCATION ON THIS DAY
                SRINC = 1367*COSZT/(SUNDIS*SUNDIS)
                if JDATE == 1:
                    DATA = [JYEAR,JMONTH,JDATE,'','',SRINC,COSZS]
                if JDATE > 1:
                    DATA = ["","",JDATE,'','',SRINC,COSZS] 
            elif DUSK <= -999999: #NIGHT TIME AT ALL TIMES AT THIS LOCATION ON THIS DAY.
                SRINC = 1367*COSZT/(SUNDIS*SUNDIS)
                if JDATE == 1:
                    DATA = [JYEAR,JMONTH,JDATE,'','',SRINC,COSZS]
                if JDATE > 1:
                    DATA = ["","",JDATE,'','',SRINC,COSZS]    
            else: #DAYLIGHT AND NIGHT TIME AT THIS LOCATION ON THIS DAY.
                DAWN = (-DUSK - EQTIME)*24/TWOPI + 12 - RLON/15 + ITZONE
                DUSK = (DUSK - EQTIME)*24/TWOPI + 12 - RLON/15 + ITZONE
                #ADJUST TIMES THAT ARE PRINTED OUT TO DAYLIGHT SAVINGS TIME IF APPLICABLE
                if SUNM == 2 and MONTH <= 10 and SUNN < 1:
                    DAWN = DAWN - 1
                    DUSK = DUSK - 1
                DAWNH = int(DAWN)
                DUSKH = int(DUSK)
                DAWNM = int((DAWN*60)%60)
                DUSKM = int((DUSK*60)%60)
                DAWNT = datetime.time(hour = DAWNH, minute = DAWNM).strftime('%H:%M')
                DUSKT = datetime.time(hour= DUSKH, minute=DUSKM).strftime('%H:%M')
                SRINC = 1367*COSZT/(SUNDIS*SUNDIS)
                if JDATE == 1:
                    DATA = [JYEAR,JMONTH,JDATE,DAWNT,DUSKT,SRINC,COSZS]
                if JDATE > 1:
                    DATA = ['','',JDATE,DAWNT,DUSKT,SRINC,COSZS]
            f = open('insolation_data.csv','a')
            writer = csv.writer(f)
            writer.writerow(DATA)
            f.close()         

def SUNSET(RLAT,SIND,COSD,RSMEZM,TWOPI):
    #INPUT: RLAT = LATITUDE (DEGREES)
    #SIND,COSD = SINE AND COSINE OF THE DECLINATIONANGLE
    #RSMEZM = (SUN RADIUS - EARTH RADIUS)/(DISTANCE TO SUN)

    #OUTPUT:DUSK = TIME OF DUSK (TEMPORAL RADIANS) AT MEAN LOCAL TIME

    SINJ = math.sin(TWOPI*RLAT/360)
    COSJ = math.cos(TWOPI*RLAT/360)
    SJSD = SINJ*SIND
    CJCD = COSJ*COSD
    if SJSD + RSMEZM + CJCD <= 0:
        DUSK = -999999
        return(DUSK)
    if SJSD + RSMEZM - CJCD >= 0:
        DUSK = 999999
        return(DUSK)
    
    #COMPUTE DUSK (AT LOCAL TIME)
    CDUSK = -(SJSD + RSMEZM)/CJCD
    DUSK = math.acos(CDUSK)
    return(DUSK)

def COSZIJ(RLAT, SIND,COSD,TWOPI):
    #CALCULATES THE DAILY AVERAGE COSINE OF THE ZENITH ANGLE
    #WEIGHTED BY TIME AND WEIGHTED BY SUNLIGHT.

    #INPUTS: RLAT = LATITUDE (DEGREES)
    #SIND,COSD = SINE AND COSINE OF THE DECLINATION ANGLE

    #OUTPUTS: COSZT = SUM(COSZ*DT)/SUM(DT)
    #COSZS = SUM(COSZ*COSZ*DT)/SUM(COSZ*DT)

    SINJ = math.sin(TWOPI*RLAT/360)
    COSJ = math.cos(TWOPI*RLAT/360)
    SJSD = SINJ*SIND
    CJCD = COSJ*COSD
    if SJSD + CJCD <= 0:
        DAWN = 999999
        DUSK = 999999
        COSZT = 0
        COSZS = 0
        cos_list = [COSZT,COSZS]
        return(cos_list)
    if SJSD - CJCD >= 0:
        DAWN = -999999
        DUSK = -999999
        ECOSZ = SJSD*TWOPI
        QCOSZ = SJSD*ECOSZ + 0.5*CJCD*CJCD*TWOPI
        COSZT = SJSD
        COSZS = QCOSZ/ECOSZ
        cos_list = [COSZT,COSZS]
        return(cos_list)
    
    #COMPUTE DAWN AND DUSK (AT LOCAL TIME) AND THEIR SINES

    CDUSK = -SJSD/CJCD
    DUSK = math.acos(CDUSK)
    SDUSK = math.sqrt(CJCD*CJCD-SJSD*SJSD)/CJCD
    S2DUSK = 2*SDUSK*CDUSK
    DAWN = -DUSK
    SDAWN = -SDUSK
    S2DAWN = -S2DUSK

    #NIGHT TIME AT INITIAL AND FINAL TIMES WITH DAYLIGHT IN BETWEEN
    ECOSZ = SJSD*(DUSK - DAWN) + CJCD*(SDUSK - SDAWN)
    QCOSZ = SJSD*ECOSZ + CJCD*(SJSD*(SDUSK - SDAWN) + 0.5*CJCD*(DUSK - DAWN + 0.5*(S2DUSK - S2DAWN)))
    COSZT = ECOSZ/TWOPI
    COSZS = QCOSZ/ECOSZ
    cos_list = [COSZT,COSZS]
    return(cos_list)


def ORBIT(ECCEN,OBLIQ,OMEGVP,DAY,TWOPI,EDAYzY):
    #ORBIT RECEIVES ORBITAL PARAMETERS AND TIME OF YEAR, AND RETURNS
    #DISTANCE FROM SUN, DECLINATION ANGLE, AND SUN'S OVERHEAD POSITION.
    #REFERENCE FOR FOLLOWING CALCULATIONS IS: V.M.BLANCO AND 
    #S.W.MCCUSKEY, 1961, "BASIC PHYSICS OF THE SOLAR SYSTEM", PAGES
    #135-151.  EXISTENCE OF MOON AND HEAVENLY BODIES OTHER THAN
    #EARTH AND SUN ARE IGNORED.  EARTH IS ASSUMED TO BE SPHERICAL.

    #PROGRAM AUTHOR: GARY L. RUSSELL
    #ANGLES, LONGITUDE AND LATITUDE ARE MEASURED IN RADIANS

    #INPUTS:  ECCEN =ECCENTRICITY OF THE ORBITAL ELLIPSE
    #OBLIQ = LATITUDE OF TROPIC OF CANCER
    #OMEGVP = LONGITUDE OF PERIHELION (SOMETIMES PI IS ADDED) =
    #SPATIAL ANGLE FROM VERNAL EQUINOX TO PERIHELION WITH 
    #SUN AS ANGLE VERTEX
    #DAY = DAYS MEASURED SINCE JANUARY 1 2000, HOUR 0

    #OUTPUT: SIND = SINE OF DECLINATION ANGLE = SIN(SUNLAT)
    #COSD = COSINE OF THE DECLINATION ANGLE = COS(SUNLAT)
    #SUNDIS = DISTANCE TO SUN IN UNITS OF SEMI MAJOR AXIS
    #SUNLON = LONGITUDE OF POINT ON EARTH DIRECTLY BENEATH SUN
    #SUNLAT = LATITUDE OF POINT ON EARTH DIRECTLY BENEATH SUN
    #EQTIME = EQUATION OF TIME = LONGTIDUE OF FICTITIOUS MEAN SUN MINUS SUNLON

    #FROM ABOVE REF:
    #(4-54): [1 - ECCEN*COS(EA)]*[1 + ECCN*COS(TA)] = 1-ECCEN^2
    #(4-55): TAN(TA/2) = SQRT[(1 + ECCEN)/(1 - ECCEN)]*TAN(EA/2)
    #YIELD: TAN(EA) = SIN(TA)*SQRT(1 - ECCEN^2)/(COS(TA) + ECCEN)
    #OR: TAN(TA) = SIN(EA)*SQRT(1 - ECCEN^2)/(COS(EA) - ECCEN)

    VE2000 = 79.3125    #DAYS FROM JANUARY 1, 2000, HOUR 0 UNTIL 
    #VERNAL EQUINOX OF YEAR 2000 = 31 + 29 + 19 + 7.5/24

    #DETERMINE EA OF VE FROM GEOMETRY: TAN(EA) = B*SIN(TA)/(E + COS(TA))
    #DETERMINE MA OF VE FROM KEPLER'S EQUATION:  MA = EA - E*SIN(EA)
    #DETERMINE MA KNOWING TIME FROM VERNAL EQUINOX TO CURRENT DAY

    BSEMI = math.sqrt(1 - ECCEN*ECCEN)
    TAOFVE = -OMEGVP
    EAOFVE = math.atan2(BSEMI*math.sin(TAOFVE),ECCEN + math.cos(TAOFVE))
    MAOFVE = EAOFVE - ECCEN*math.sin(EAOFVE)
    MA = (TWOPI*(DAY - VE2000)/EDAYzY + MAOFVE) % TWOPI
    DEA = 1

    #NUMERICALLY INVERT KEPLER'S EQUATION: MA = EA - E*SIN(EA)
    EA = MA + ECCEN*(math.sin(MA) + ECCEN*math.sin(2*MA)/2)
    while DEA > 1e-10:
        DEA = (MA - EA + ECCEN*math.sin(EA))/(1 - ECCEN*math.cos(EA))
        EA = EA + DEA

    #CALCULATE DISTANCE TO SUN AND TRUE ANOMALY
    SUNDIS = 1 - ECCEN*math.cos(EA)
    TA = math.atan2((BSEMI*math.sin(EA)),(math.cos(EA) - ECCEN))

    #CHANGE REFERENCE FRAME TO BE NONROTATING REFERENCE FRAME, ANGLES
    #FIXED ACCORDING TO STARS, WITH EARTH AT CENTER AND POSITIVE X
    #AXIS BE RAY FROM EARTH TO SUN WERE EARTH AT VERNAL EQUINOX, AND
    #X-Y PLANE BE EARTH'S EQUATORIAL PLANE.  DISTANCE FROM CURRENT SUN
    #TO THIS X AXIS IS SUNDIS SIN(TA - TAOFVE).  AT VERNAL EQUINOX, SUN
    #IS LOCATED AT (SUNDIS,0,0).  AT OTHER TIMES, SUN IS LOCATED AT:
    #SUN = (SUNDIS COS(TA - TAOFVE), SUNDIS SIN(TA - TAOFVE) COS(OBLIQ), SUNDIS SIN(TA - TAOFVE) SIN(OBLIQ))

    SIND = math.sin(TA - TAOFVE)*math.sin(OBLIQ)
    COSD = math.sqrt(1 - SIND*SIND)
    SUNX = math.cos(TA - TAOFVE)
    SUNY = math.sin(TA - TAOFVE)*math.cos(OBLIQ)
    SLNORO = math.atan2(SUNY,SUNX)

    #DETERMINE SUN LOCATION IN EARTH'S ROTATING REFERENCE FRAME
    #(NORMAL LONGITUDE AND LATITUDE)

    VEQLON = TWOPI*VE2000 - TWOPI/2 + MAOFVE - TAOFVE
    ROTATE = TWOPI*(DAY - VE2000)*(EDAYzY + 1)/EDAYzY
    SUNLON = (SLNORO - ROTATE - VEQLON) % TWOPI
    if SUNLON > TWOPI/2:
        SUNLON = SUNLON - TWOPI
    SUNLAT = math.asin(math.sin(TA - TAOFVE)*math.sin(OBLIQ))

    #DETERMINE LONGITUDE OF FICTITIOUS MEAN SUN
    #CALCULATE EQUATION OF TIME

    SLMEAN = TWOPI/2 - TWOPI*(DAY - math.floor(DAY))
    EQTIME = (SLMEAN - SUNLON) % TWOPI
    if EQTIME > TWOPI/2:
        EQTIME = EQTIME - TWOPI
    orbit_list = [SIND,COSD,SUNDIS,EQTIME]
    return(orbit_list)


def YMDtoD(YEAR,MONTH,DATE):
    #FOR A GIVEN YEAR (A.D.), MONTH AND DATE (BETWEEN 0 AND 31),
    #CALCULATE NUMBER OF DAYS MEASURED FROM JANUARY 1, 2000, HOUR 0.

    JDAY4C = 365*400 + 97   #NUMBER OF DAYS IN 4 CENTURIES
    JDAY1C = 365*100 + 24   #NUMBER OF DAYS IN 1 CENTURY
    JDAY4Y = 365*4 + 1      #NUMBER OF DAYS IN 4 YEARS
    JDAY1Y = 365            #NUMBER OF DAYS IN 1 YEAR
    JDSUMN = [0,31,59,90,120,151,181,212,243,273,304,334]
    JDSUML = [0,31,60,91,121,152,182,213,244,274,305,335]
    N4CENT = math.floor((YEAR-2000)/400)
    IYR4C = YEAR-2000 - N4CENT*400
    N1CENT = IYR4C/100
    IYR1C = IYR4C - N1CENT*100
    N4YEAR = IYR1C/4
    IYR4Y = IYR1C - N4YEAR*4
    N1YEAR = IYR4Y
    DAY = N4CENT*JDAY4C
    if N1CENT > 0: #SECOND TO FOURTH OF EVERY FOURTH CENTURY: 21XX,22XX,23XX,ETC.
        DAY = DAY + JDAY1C + 1 + (N1CENT - 1)*JDAY1C
        if N4YEAR > 0:  #SUBSEQUENT 4 YEARS OF EVERY SECOND TO 4TH CENTURY WHEN
                        #THERE IS A LEAP YEAR:  2104-2107,2108-2111, ETC.
            DAY = DAY + JDAY4Y - 1 + (N4YEAR-1)*JDAY4Y
            if N1YEAR > 0:  #CURRENT YEAR IS NOT A LEAP YEAR
                DAY = DAY + JDAY1Y + 1 + (N1YEAR - 1)*JDAY1Y
                DAY = DAY + JDSUMN[MONTH] + DATE
            else:   #CURRENT YEAR IS A LEAP YEAR
                DAY = DAY + JSUML[MONTH] + DATE
        else:   #FIRST 4 YEARS OF EVERY 2ND TO 4TH CENTURY WHEN THERE IS
                #NO LEAP YEAR DURING THE FOUR YEARS: 2100-2103, 2200-2203, ETC.
            DAY = DAY + N1YEAR*JDAY1Y
            DAY = DAY + JDSUMN[MONTH] + DATE  
    else:   #FIRST OF EVERY 4TH CENTURY: 16XX,20XX,24XX,ETC.
        DAY = DAY + N4YEAR*JDAY4Y
        if N1YEAR > 0:  #CURRENT YEAR IS A LEAP YEAR
            DAY = DAY + JDAY1Y + 1 +(N1YEAR-1)*JDAY1Y
            DAY = DAY + JDSUMN(MONTH) + DATE
        else:
            DAY = DAY + JDSUML[MONTH] + DATE
    return(DAY)     


def QLEAPY(YEAR):
    #DETERMINE WHETHER THE GIVEN YEAR IS A LEAP YEAR

    LEAPY = False
    LEAPY = LEAPY or YEAR % 4 == 0
    LEAPY = LEAPY and YEAR % 100 != 0
    LEAPY = LEAPY or YEAR % 400 == 0
    return(LEAPY)

def ORBPAR(YEAR,TWOPI):
    #CALCULATES AND RETURN THE 3 ORBITAL  PARAMETERS AS A FUNCTION OF
    #THE YEAR.  tHE SOURCE OF THESE CALCULATIONS IS ANDRE L. BERGER,
    #1978, "LONG-TERM VARIATIONS OF DAILY INSOLATION AND QUATERNARY
    # CLIMATE CHANGES", JAS, V.35, P.2362.  ALSO USEFUL IS: ANDRE L.
    #BERGER, MAY 1978, "A SIMPLE ALGORITHM TOCOMPUTE LONG TERM
    #VARIATIONS OF DAILY INSOLATION", PUBLISHED BY INSTITUT
    #D'ASTRONOMIE DE GEOPHYSIQUE, UNIVERSITE CATHOLIQUE DE LOUVAIN,
    #LOUVAIN-LA NEUVE, NO. 18.

    #TABLES AND EQUATIONS REFER TO THE FIRST REFERNECE (JAS). THE
    #CORRESPONDING TABLE OR EQUATION IN THE SECOND REFERENCE IS ENCLOSED
    #IN PARENTHESES.  THE COEFFICIENTS USED IN THIS SUBROUTINE ARE
    #SLIGHTLY MORE PRECISE THAN THOSE USED IN EITHER OF THE REFERENCES.
    #THE GENERATED ORBITAL PARAMETERS ARE PRECISE WITHIN PLUS OR MINUS
    #1000000 YEARS FROM PRESENT.

    #INPUT:  YEAR (POSITIVE IS AD, NEBATIVE IS BC)
    #OUTPUTS:  ECCEN - ECCENTRICITY OF ORBITAL ELLIPSE
    #OBLIQ = LATITUDE OF TROPIC OF CANCER IN RADIANS
    #OMEGVP = LONGITUDE OF PERIHELION = SPATIAL ANGLE FROM VERNAL
    #EQUINOX TO PERIHELION IN RADIANS WITH SUN AS ANGLE VERTEX

    PIz180 = TWOPI/360
    #TABLE1 CONTAINS OBLIQUITY RELATIVE TO MEAN ECLIPTIC OF DATE: OBLIQD
    TABLE1 = [[-2462.2214466,31.609974,251.9025],
                [-857.3232075,32.620504,280.8325],
                [-629.3231835,24.172203,128.3057],
                [-414.2804924,31.983787,292.7252],
                [-311.7632587,44.828336,15.3747],
                [308.9408604,30.973257,263.7951],
                [-162.5533601,43.668246,308.4258],
                [-116.1077911,32.246691,240.0099],
                [101.1189923,30.599444,222.9725],
                [-67.6856209,42.681324,268.76809],
                [24.9079067,43.836462,316.7998],
                [22.5811241,47.439436,319.6024],
                [-21.1648355,63.219948,143.8050],
                [-15.6549876,64.230478,172.7351],
                [15.3936813,1.01053,28.9300],
                [14.6660938,7.437771,123.5968],
                [-11.7273029,55.782177,20.2082],
                [10.2742696,0.373813,40.8226],
                [6.4914588,13.218362,123.4722],
                [5.8539148,62.583231,155.6977],
                [-5.4872205,63.593761,184.6277],
                [-5.4290191,76.438310,267.2772],
                [5.160957,45.815258,55.0196],
                [5.0786314,8.448301,152.5268],
                [-4.0735782,56.792707,49.1382],
                [3.7227167,49.747842,204.6609],
                [3.3971932,12.058272,56.5233],
                [-2.8347004,75.278220,200.3284],
                [-2.6550721,65.241008,201.6651],
                [-2.5717867,64.604291,213.5577],
                [-2.4712188,1.647247,17.0374],
                [2.462541,7.811584,164.4194],
                [2.2464112,12.207832,94.5422],
                [-2.0755511,63.856665,131.9124],
                [-1.9713669,56.15599,61.0309],
                [-1.8813061,77.44884,296.2073],
                [-1.8468785,6.801054,135.4894],
                [1.8186742,62.209418,114.8750],
                [1.7601888,20.656133,247.0691],
                [-1.5428851,48.344406,256.6114],
                [1.4738838,55.14546,32.1008],
                [-1.4593669,69.000539,143.6804],
                [1.4192259,11.07135,16.8784],
                [-1.181898,74.291298,160.6835],
                [1.1756474,11.047742,27.5932],
                [-1.1316126,0.636717,348.1074],
                [1.0896928,12.844549,82.6496]]   

    #TABLE4 CONTAINS FUNDAMENTAL ELEMENTS OF THE ECLIPTIC: ECCEN SIN(PI)
    TABLE4 = [[.01860798,  4.207205,  28.620089],
                  [.01627522,  7.346091, 193.788772],
                 [-.01300660, 17.857263, 308.307024],
                  [.00988829, 17.220546, 320.199637],
                 [-.00336700, 16.846733, 279.376984],
                  [.00333077,  5.199079,  87.195000],
                 [-.00235400, 18.231076, 349.129677],
                  [.00140015, 26.216758, 128.443387],
                  [.00100700,  6.359169, 154.143880],
                  [.00085700, 16.210016, 291.269597],
                  [.00064990,  3.065181, 114.860583],
                  [.00059900, 16.583829, 332.092251],
                  [.00037800, 18.493980, 296.414411],
                 [-.00033700,  6.190953, 145.769910],
                  [.00027600, 18.867793, 337.237063],
                  [.00018200, 17.425567, 152.092288],
                 [-.00017400,  6.186001, 126.839891],
                 [-.00012400, 18.417441, 210.667199],
                  [.00001250,  0.667863,  72.108838]]

    #TABLE5 CONTAINS GENERAL PRECESSION IN LONGITUDE: PSI
    TABLE5 = [[7391.0225890, 31.609974, 251.9025],
                  [2555.1526947, 32.620504, 280.8325],
                  [2022.7629188, 24.172203, 128.3057],
                 [-1973.6517951,  0.636717, 348.1074],
                  [1240.2321818, 31.983787, 292.7252],
                   [953.8679112,  3.138886, 165.1686],
                  [-931.7537108, 30.973257, 263.7951],
                   [872.3795383, 44.828336,  15.3747],
                   [606.3544732,  0.991874,  58.5749],
                  [-496.0274038,  0.373813,  40.8226],
                   [456.9608039, 43.668246, 308.4258],
                   [346.9462320, 32.246691, 240.0099],
                  [-305.8412902, 30.599444, 222.9725],
                   [249.6173246,  2.147012, 106.5937],
                  [-199.1027200, 10.511172, 114.5182],
                   [191.0560889, 42.681324, 268.7809],
                  [-175.2936572, 13.650058, 279.6869],
                   [165.9068833,  0.986922,  39.6448],
                   [161.1285917,  9.874455, 126.4108],
                   [139.7878093, 13.013341, 291.5795],
                  [-133.5228399,  0.262904, 307.2848],
                   [117.0673811,  0.004952,  18.9300],
                   [104.6907281,  1.142024, 273.7596],
                    [95.3227476, 63.219948, 143.8050],
                    [86.7824524,  0.205021, 191.8927],
                    [86.0857729,  2.151964, 125.5237],
                    [70.5893698, 64.230478, 172.7351],
                   [-69.9719343, 43.836462, 316.7998],
                   [-62.5817473, 47.439436, 319.6024],
                    [61.5450059,  1.384343,  69.7526],
                   [-57.9364011,  7.437771, 123.5968],
                    [57.1899832, 18.829299, 217.6432],
                   [-57.0236109,  9.500642,  85.5882],
                   [-54.2119253,  0.431696, 156.2147],
                    [53.2834147,  1.160090,  66.9489],
                    [52.1223575, 55.782177,  20.2082],
                   [-49.0059908, 12.639528, 250.7568],
                   [-48.3118757,  1.155138,  48.0188],
                   [-45.4191685,  0.168216,   8.3739],
                   [-42.2357920,  1.647247,  17.0374],
                   [-34.7971099, 10.884985, 155.3409],
                    [34.4623613,  5.610937,  94.1709],
                   [-33.8356643, 12.658184, 221.1120],
                    [33.6689362,  1.010530,  28.9300],
                   [-31.2521586,  1.983748, 117.1498],
                   [-30.8798701, 14.023871, 320.5095],
                    [28.4640769,  0.560178, 262.3602],
                   [-27.1960802,  1.273434, 336.2148],
                    [27.0860736, 12.021467, 233.0046],
                   [-26.3437456, 62.583231, 155.6977],
                    [24.7253740, 63.593761, 184.6277],
                    [24.6732126, 76.438310, 267.2772],
                    [24.4272733,  4.280910,  78.9281],
                    [24.0127327, 13.218362, 123.4722],
                    [21.7150294, 17.818769, 188.7132],
                   [-21.5375347,  8.359495, 180.1364],
                    [18.1148363, 56.792707,  49.1382],
                   [-16.9603104,  8.448301, 152.5268],
                   [-16.1765215,  1.978796,  98.2198],
                    [15.5567653,  8.863925,  97.4808],
                    [15.4846529,  0.186365, 221.5376],
                    [15.2150632,  8.996212, 168.2438],
                    [14.5047426,  6.771027, 161.1199],
                   [-14.3873316, 45.815258,  55.0196],
                    [13.1351419, 12.002811, 262.6495],
                    [12.8776311, 75.278220, 200.3284],
                    [11.9867234, 65.241008, 201.6651],
                    [11.9385578, 18.870667, 294.6547],
                    [11.7030822, 22.009553,  99.8233],
                    [11.6018181, 64.604291, 213.5577],
                   [-11.2617293, 11.498094, 154.1631],
                   [-10.4664199,  0.578834, 232.7153],
                    [10.4333970,  9.237738, 138.3034],
                   [-10.2377466, 49.747842, 204.6609],
                    [10.1934446,  2.147012, 106.5938],
                   [-10.1280191,  1.196895, 250.4676],
                    [10.0289441,  2.133898, 332.3345],
                   [-10.0034259,  0.173168,  27.3039]]

    YM1950 = YEAR - 1950

    #GET OBLIQUITY FROM TABLE1 (2):
    #OBLIQ = 23.320556 (DEGREES)    #ECLIPTIC PLANE EQ. 5.5 (15)
    #OBLIQD = OBLIQ + SUM[A COST(FT + DELTA)]   EQUATION 1 (5)
    SUMC = 0
    for i in range(0,47):
        ARG = PIz180*(YM1950*TABLE1[i][1]/3600 + TABLE1[i][2])
        SUMC = SUMC + TABLE1[i][0]*math.cos(ARG)
        OBLIQD = 23.320556 + SUMC/3600
        OBLIQ = OBLIQD*PIz180

    #GET ECCENTRICITY FROMT TABLE4 (1):
    #ECCEN SIN(PI) = SUM[M SIN(GT+BETA)]    EQUATION 4 (1)
    #ECCEN COS(PI) = SUM[M COS(GT+BETA)]    EQUATION 4 (1)
    #ECCEN = ECCEN SQRT[SIN(PI)^2 + COS(PI)^2]
    ESINPI = 0
    ECOSPI = 0
    for i in range(0,19):
        ARG = PIz180*(YM1950*TABLE4[i][1]/3600 + TABLE4[i][2])
        ESINPI = ESINPI + TABLE4[i][0]*math.sin(ARG)
        ECOSPI = ECOSPI + TABLE4[i][0]*math.cos(ARG)
        ECCEN = math.sqrt(ESINPI*ESINPI + ECOSPI*ECOSPI)

    #PERIHELION FROM EQUATION 4,6,7 (9) AND TABLE4/TABLE5 (1,3):
    #PSI = 50.439273 (SECONDS OF DEGREE)    EQUATION 7.5 (16)
    #ZETA = 3.392506 (DEGREES)              EQUATION 7.5 (17)
    #PSI = PSI*T + ZETA + SUM[F SIN(FT+DELTA)]  EQUATION 7 (9)
    #PIE = ATAN[ECCEN SIN(PI)]/ECCEN COS(PI)]
    #OMEGVP = PIE + PSI + PI        EQUATION 6 (4.5)

    PIE = math.atan2(ESINPI,ECOSPI)
    FSINFD = 0
    for i in range(0,78):
        ARG = PIz180*(YM1950*TABLE5[i][1]/3600 + TABLE5[i][2])
        FSINFD = FSINFD + TABLE5[i][0]*math.sin(ARG)
        PSI = PIz180*(3.392506 + (YM1950*50.439273 + FSINFD)/3600)
        PP = PIE + PSI + 0.5*TWOPI
        OMEGVP = PP % TWOPI

    orb_list = [OBLIQ,ECCEN,OMEGVP]
    return(orb_list)