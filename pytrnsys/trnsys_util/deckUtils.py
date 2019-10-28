
import numpy as num
import pytrnsys.pdata.processFiles as spfUtils


def replaceAllUnits(linesRead ,idBegin ,TrnsysUnits ,filesUnitUsedInDdck ,filesUsedInDdck):

    unitId = idBegin

    for i in range(len(TrnsysUnits)):
        unitId=unitId+1
        replaceUnitNumber(linesRead ,int(TrnsysUnits[i]) ,unitId)


    for i in range(len(filesUnitUsedInDdck)):

        try:
            filesUnitUsedInDdck[i] = int(filesUnitUsedInDdck[i])

            raise ValueError("fileUnit is an integer %d. THIS IS NOT ALLOWED IF AUTOMATIC UNIT NUMBERING IS ACTIVE" % filesUnitUsedInDdck[i])

        except:
            # print ("fileUnit is a string %s. Look for the string unit" % self.filesUnitUsedInDdck[i])
            for j in range(len(linesRead)):
                splitEqual= linesRead[j].split("=")

                if (splitEqual[0].replace(" " ,"") == filesUnitUsedInDdck[i]):
                    unitId = unitId + 1

                    linesRead[j] = "%s = %d\n " %(filesUnitUsedInDdck[i] ,unitId)
                    print ("StringUnit from file %s changed from %s to %d" %
                    (filesUsedInDdck[i], splitEqual[1][:-1], unitId))

    return unitId

def readAllTypes(lines,sort=True):  # lines should be self.linesChanged

    """
        It reads all types and units from a a list of lines readed from a deck file.
        It also reads the files used and which units are used for them. IN order to be able to change automatically the unit numbers afterwards
        we need that each ASSIGN uses a variable for the unit, e.g. unitReadWeather and that this variable is used in the ddck file.

        returns:
        --------
        TrnsysUnitsSorted,TrnsysTypesSorted,filesUsedInDdck,filesUnitUsedInDdck
    """
    TrnsysTypes = []
    TrnsysUnits = []
    filesUsedInDdck = []
    filesUnitUsedInDdck = []

    for i in range(len(lines)):

        splitBlank = lines[i].split()

        if (splitBlank[0] == "ASSIGN"):
            filesUsedInDdck.append(splitBlank[1])
            filesUnitUsedInDdck.append(splitBlank[2])

        try:
            unit = splitBlank[0].replace(" ", "")
            nUnit = splitBlank[1].replace(" ", "")
            types = splitBlank[2].replace(" ", "")
            ntype = splitBlank[3].replace(" ", "")

            if (unit.lower() == "unit".lower() and types.lower() == "Type".lower()):
                #                    print "unit:%s nUnit:%s types:%s ntype:%s"%(unit,nUnit,types,ntype)
                TrnsysTypes.append(int(ntype))
                TrnsysUnits.append(int(nUnit))

        except:
            pass

    # We need to sort them for units. Otherwise when we change unit numbers we can change something already changed
    # for example we replace UNIT 400 for UNIT 20 and at the end we have UNIT 20 again and we change it for UNIT 100

    if(sort==False):
        TrnsysTypesSorted=TrnsysTypes
        TrnsysUnitsSorted=TrnsysUnits
    else:
        TrnsysTypesSorted = []
        TrnsysUnitsSorted = []

        iSort = num.argsort(TrnsysUnits)
        for i in range(len(TrnsysTypes)):
            k = iSort[i]
            TrnsysUnitsSorted.append(TrnsysUnits[k])
            TrnsysTypesSorted.append(TrnsysTypes[k])

    #Check if any value is repeated.

    return TrnsysUnitsSorted,TrnsysTypesSorted,filesUsedInDdck,filesUnitUsedInDdck

def replaceUnitNumber(linesRead,oldUnit,newUnit):

    lines = linesRead

    unitFromTypeChanged=False

    if(oldUnit==newUnit):
        pass
    else:
        for i in range(len(lines)):

            if(unitFromTypeChanged==False):
                oldString = "UNIT %d" % (oldUnit)
                newString = "UNIT %d" % (newUnit)

                newLine= lines[i].replace(oldString, newString)

                if(newLine!=lines[i]):
                    unitFromTypeChanged=True
                    print ("replacement SUCCESS from %s to %s"%(oldString,newString))
                    lines[i]=newLine

        if (unitFromTypeChanged == False):
            print ("replacement FAILURE from %s to %s" % (oldUnit, newUnit))
        else:
            for i in range(len(lines)):

                oldString = "[%d," % (oldUnit)
                newString = "[%d," % (newUnit)
                newLine = lines[i].replace(oldString, newString)
                if(newLine!=lines[i]):
                    # print ("replacement SUCCESS from %s to %s"%(oldString,newString))
                    lines[i] = newLine

def getTypeFromUnit(myUnit,linesReadedNoComments):

    for i in range(len(linesReadedNoComments)):

        splitEquality = linesReadedNoComments[i].split()

        try:
            unit = splitEquality[0].replace(" ", "")
            nUnit = splitEquality[1].replace(" ", "")
            types = splitEquality[2].replace(" ", "")
            ntype = splitEquality[3].replace(" ", "")

            if (unit.lower() == "unit".lower() and types.lower() == "Type".lower()):

                if (nUnit.lower() == myUnit.lower()):
                    print ("UNIT FOUND myUnit:%s type:%s" % (myUnit, ntype))
                    return ntype
        except:
            pass

    return None

def getDataFromDeck(linesReadedNoComments, myName, typeValue="string"):

    value = getMyDataFromDeck(linesReadedNoComments,myName)

    if (value == None):
        return None

    if (typeValue == "double"):
        return float(value)
    elif (typeValue == "int"):
        return int(value)
    elif (typeValue == "string"):
        return value
    else:
        raise ValueError("typeValue must be double,int or string")

def getMyDataFromDeck(linesReadedNoComments,myName):

    for i in range(len(linesReadedNoComments)):

        splitEquality = linesReadedNoComments[i].split('=')

        try:
            name = splitEquality[0].replace(" ", "")
            value = splitEquality[1].replace(" ", "")

            if (name.lower() == myName.lower()):
                return value

        except:
            pass

    return None


def loadDeck(nameDck,eraseBeginComment=True,eliminateComments=True):
    """
    Parameters
    ----------
    nameDck : str
        name of the TRNSYS deck to be loaded
    eraseBeginComment : bool
        True will delete all lines starting with *, !, and blank, but also the comments *********anyComment*********
        False will delete all lines starting with !, and blank, but keep the ones starting with **
    Return
    ------
    lines : str
        list of lines obateined form the deck without the comments
    """

    infile = open(nameDck, 'r')

    lines = infile.readlines()

    #        skypChar = None    #['*'] #This will eliminate the lines starting with skypChar
    if (eraseBeginComment == True):
        skypChar = ['*', '!', '      \n']  # ['*'] #This will eliminate the lines starting with skypChar
    else:
        skypChar = ['!', '      \n']  # ['*'] #This will eliminate the lines starting with skypChar

    replaceChar = None  # [',','\''] #This characters will be eliminated, so replaced by nothing

    linesChanged = spfUtils.purgueLines(lines, skypChar, replaceChar, removeBlankLines=True)

    # Only one comment is erased, so that if we hve ! comment1 ! comment2 only the commen2 will be erased
    if (eliminateComments == True):
        linesChanged = spfUtils.purgueComments(linesChanged, ['!'])

    return linesChanged


def checkEquationsAndConstants(lines):
    # lines=linesChanged
    for i in range(len(lines)):

        splitBlank = lines[i].split()

        if (splitBlank[0].lower() == "EQUATIONS".lower() or splitBlank[0].lower() == "CONSTANTS".lower()):

            lineError = i + 1
            try:
                numberOfValues = int(splitBlank[1])
            except:
                raise ValueError(
                    "checkEquationsAndConstants %s can't be split in line i:%d (missing number?)" % (splitBlank, i))

            countedValues = 0  # start counting
            error = 0
            while (error == 0):
                i = i + 1

                splitEquality = lines[i].split('=')
                error = 1
                #                    print "count=%d"%countedValues
                #                    print splitEquality

                if (len(splitEquality) >= 2):
                    #                        print "counting at %s"%(self.linesChanged[i])
                    error = 0
                    countedValues = countedValues + 1

            if (countedValues != numberOfValues):
                parsedFile = "%s.parse" % self.nameDck
                outfile = open(parsedFile, 'w')
                outfile.writelines(lines)
                outfile.close()

                raise ValueError("FATAL Error in : ", splitBlank[0], " at line ", lineError, " of parsed file =", \
                                 parsedFile, ". Number set is ", numberOfValues, " and there are ", countedValues)

def getTypeName(typeNum):

    if (typeNum == 888):
        return "General Controller (SPF)"
    if (typeNum == 65):
        return "Online plotter (TRNSYS)"
    elif (typeNum == 816):
        return "Averaging"
    elif (typeNum == 862):
        return "TColl control expected for switch (SPF)"
    elif (typeNum == 817):
        return "Time delay"
    elif (typeNum == 863):
        return "Ice controller (SPF)"
    elif (typeNum == 993):
        return "Recall"
    elif (typeNum == 46):
        return "Monthly integrator (TRNSYS)"
    elif (typeNum == 9):
        return "Data reader (TRNSYS)"
    elif (typeNum == 109):
        return "Weather data processor (TRNSYS)"
    elif (typeNum == 33):
        return "Psychrometrics"
    elif (typeNum == 69):
        return "Sky temperature"
    elif (typeNum == 194):
        return "PV module (TRNSYS)"
    elif (typeNum == 320):
        return "PID controller"
    elif (typeNum == 861):
        return "Ice Storage non-deiceable (SPF)"
    elif (typeNum == 25):
        return "User defined printer (TRNSYS)"
    elif (typeNum == 889):
        return "Adapted PD-controller"
    elif (typeNum == 833):
        return "Collector with condensation (SPF)"
    elif (typeNum == 951):
        return "EWS with integrated g-functions (SPF)"
    elif (typeNum == 977):
        return "Parameter fit heat pump (SPF)"
    elif (typeNum == 1925 or typeNum == 1924):
        return "Plug-flow TES (SPF)"
    elif (typeNum == 811):
        return "Tempering valve (SPF)"
    elif (typeNum == 929):
        return "TeePiece (SPF)"
    elif (typeNum == 931):
        return "Type 931 CHECK (SPF)"
    elif (typeNum == 1792):
        return "Radiant floor (SPF)"
    elif (typeNum == 5998):
        return "Building ISO (SPF)"
    elif (typeNum == 2):
        return "Collector controller (TRNSYS)"
    elif (typeNum == 935):
        return "Flow solver (SPF)"
    elif (typeNum == 711):
        return "2D Ground model (SPF)"
    elif (typeNum == 979):
        return "Low temperature Al-reactor (SPF)"

    else:
        return "Unknown"

def readEnergyBalanceVariablesFromDeck(lines):
    """Reading all the variables defined in the deck that follow the energy balance standard.
       This function reads from self.linesChanged filled in the loadDeck function.
       The standard nomenclature of energy balance variables are:
       elSysIn_ for electricity given into the system
       elSysOut_ for electricity going out of the system
       qSysIn_ for heat given into the system
       qSysOut_ for heat going out of the system

       Return
       ------
       eBalance:  a list with all energy balance terms
    """


    eBalance = []
    for i in range(len(lines)):
        splitBlank = lines[i].split()

        if(splitBlank[0][0:7]=="elSysIn"):
            eBalance.append(splitBlank[0])
        if(splitBlank[0][0:8]=="elSysOut"):
            eBalance.append(splitBlank[0])
        if(splitBlank[0][0:6]=="qSysIn"):
            eBalance.append(splitBlank[0])
        if(splitBlank[0][0:7]=="qSysOut"):
            eBalance.append(splitBlank[0])

    return eBalance

def addEnergyBalanceMonthlyPrinter(unit,eBalance):
    """
        Adds a monthly printer in the deck using the energy balance variables.
        It also calulates the most common KPI such as monthly and yearly SPF
    """

    # size = len(self.qBalanceIn)+len(self.qBalanceOut)+len(self.elBalanceIn)+len(self.elBalanceOut)

    lines = []
    line = "***************************************************************\n";lines.append(line)
    line = "**BEGIN energy Balance printer automatically geneated from DDck\n";lines.append(line)
    line = "***************************************************************\n";lines.append(line)
    line = "ASSIGN temp\ENERGY_BALANCE_MO.Prt %d\n"%unit;lines.append(line)
    line = "UNIT %d Type 46\n"%unit;lines.append(line)
    line = "PARAMETERS 6\n";lines.append(line)
    line = "%d !1: Logical unit number\n"%unit;lines.append(line)
    line = "-1 !2: for monthly summaries\n";lines.append(line)
    line = "1  !3: 1:print at absolute times\n";lines.append(line)
    line = "-1 !4 -1: monthly integration\n";lines.append(line)
    line = "1  !5 number of outputs to avoid integration\n";lines.append(line)
    line = "1  !6 output number to avoid integration\n";lines.append(line)
    line = "INPUTS %d\n"%len(eBalance);lines.append(line)
    allvars = "TIME "+" ".join(eBalance)
    line = "%s\n"%allvars;lines.append(line)
    line = "*******************************\n";lines.append(line)
    line = "%s\n"%allvars;lines.append(line)

    # self.linesChanged=self.linesChanged+lines
    return lines
