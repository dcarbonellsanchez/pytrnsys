#!/usr/bin/python

"""
Child class from ProcessMonthlyDataBase used for processing all TRNSYS simulations.

Author : Dani Carbonell
Date   : 2018
ToDo :
"""

import os
import string, shutil
import pytrnsys.pdata.processFiles as spfUtils
import pytrnsys.psim.processMonthlyDataBase as  monthlyData  # changed in order to clean the processing of files
import pytrnsys.utils.utilsSpf as utils
import time
import numpy as num
import matplotlib.pyplot as plt
import pytrnsys.trnsys_util.readTrnsysFiles as readTrnsysFiles
import pytrnsys.utils.unitConverter as unit
import pytrnsys.trnsys_util.LogTrnsys as LogTrnsys
from pytrnsys.psim.simulationLoader import SimulationLoader
import pandas as pd
import pytrnsys.report.latexReport as latex
import pytrnsys.plot.plotMatplotlib as plot
import json
# from collections import OrderedDict


class ProcessTrnsysDf():

    def __init__(self, _path, _name):

        self.fileName = _name
        self.outputPath = _path + "\%s" % self.fileName
        self.executingPath = _path

        # Internal data

        self.fileNameWithExtension = _name
        self.titleOfLatex = "$%s$" % self.fileName
        self.folderName = self.fileName

        self.rootPath = os.getcwd()

        self.doc = latex.LatexReport(self.outputPath, self.fileName)

        self.plot = plot.PlotMatplotlib()
        self.plot.setPath(self.outputPath)

        self.cleanModeLatex = False

        self.tempFolder = "%s\\temp" % self.outputPath
        self.tempFolderEnd = "%s\\temp" % self.outputPath

        self.trnsysVersion = "standard"
        self.yearReadedInMonthlyFile = -1  # -1 means the last
        self.firstMonth = "January"

        self.yearlyFactor = 10.  # value to divide yerarly values when plotted along with monthly data
        self.units = unit.UnitConverter()


        self.readTrnsysFiles = readTrnsysFiles.ReadTrnsysFiles(self.tempFolderEnd)

        # self.tInEvapHpMonthlyMax = num.zeros(12,float)
        # self.tInEvapHpMonthlyMin = num.zeros(12,float)
        # self.tInEvapHpMonthlyAv  = num.zeros(12,float)

        self.nameClass = "ProcessTrnsys"
        self.unit = unit.UnitConverter()
        self.trnsysDllPath = False


    def setInputs(self,inputs):
        self.inputs=inputs

    # the idea is to read the deck and get important information fro processing.
    # area collector, volume ice storage, volume Tes, Area uncovered, nH1, nominal power heat pump, etc...
    def setBuildingArea(self, area):
        self.buildingArea = area

    def setTrnsysDllPath(self, path):

        self.trnsysDllPath = path

    def setBuildingArea(self, area):
        self.buildingArea = area

    def setTrnsysVersion(self, version):
        self.trnsysVersion = version

    def setPrintDataForGle(self, printData):

        self.printDataForGle = printData

    def loadAndProcess(self):

        self.loadFiles()
        self.process()
        self.doLatexPdf()
        self.addResultsFile()

    def setLoaderParameters(self):

        self.monthlyUsed = True
        self.hourlyUsed = True
        self.timeStepUsed = True

        self.fileNameListToRead = False
        self.loadMode = "complete"

        if 'firstMonth' in self.inputs.keys():
            self.firstMonth = self.inputs['firstMonth']
        else:
            self.firstMonth = "January"
        if 'yearReadedInMonthlyFile' in self.inputs.keys():
            self.yearReadedInMonthlyFile = self.inputs['yearReadedInMonthlyFile']
        else:
            self.yearReadedInMonthlyFile = -1

    def loadFiles(self):

        self.setLoaderParameters()


        self.loader = SimulationLoader(self.outputPath + '//temp', fileNameList=self.fileNameListToRead,
                                       mode=self.loadMode, monthlyUsed=self.monthlyUsed, hourlyUsed=self.hourlyUsed,
                                       timeStepUsed=self.timeStepUsed,firstMonth=self.firstMonth, year = self.yearReadedInMonthlyFile)
        # self.monData = self.loader.monData
        self.monDataDf = self.loader.monDataDf
        self.houDataDf = self.loader.houDataDf
        self.steDataDf = self.loader.steDataDf

        self.myShortMonths = utils.getShortMonthyNameArray(self.monDataDf["Month"].values)

        print ("loadFiles completed using SimulationLoader")

    def process(self):

        pass

    def executeLatexFile(self):

        self.doc.executeLatexFile(moveToTrnsysLogFile=True, runTwice=True)

    def doLatexPdf(self, documentClass="SPFShortReportIndex"):

        self.createLatex(documentClass=documentClass)

        self.executeLatexFile()

    def addLatexContent(self):

        raise ValueError("process needs to be defined in each particuar child class")

    def createLatex(self, documentClass="SPFShortReportIndex"):

        self.doc.documentClass = documentClass

        self.doc.setTitle(self.titleOfLatex)
        self.doc.setSubTitle("TRNSYS results")
        self.doc.setCleanMode(self.cleanModeLatex)
        self.doc.addBeginDocument()

        self.addLatexContent()

        self.doc.addEndDocumentAndCreateTexFile()

    def calculateDemands(self):

        self.qDemandVector = []
        self.elDemandVector = []
        self.qDemandDf = pd.DataFrame()
        self.legendEl = []
        self.legendQ = []
        # self.elDemandDf = pd.DataFrame()

        for name in self.monDataDf.columns:

            if (len(name) > 9 and name[0:9] == "elSysOut_"):

                if (name[-6:] == "Demand"):
                    self.elDemandVector.append(self.monDataDf[name])
                    self.legendEl.append(self.getNiceLatexNames(name))

            elif (len(name) > 8 and name[0:8] == "qSysOut_"):

                if (name[-6:] == "Demand"):
                    self.qDemandVector.append(self.monDataDf[name].values)
                    self.qDemandDf = self.qDemandDf + self.monDataDf[name]
                    self.legendQ.append(self.getNiceLatexNames(name))

        self.qDemand = num.zeros(12)

        for i in range(len(self.qDemandVector)):
            self.qDemand = self.qDemand + self.qDemandVector[i]

    def addDemands(self):

        legend = ["Month"] + self.legendQ + ["Total"]

        caption = "Heat Demand"
        nameFile = "HeatDemand"
        addLines = False

        var = self.qDemandVector
        var.append(self.qDemand)

        self.doc.addTableMonthlyDf(var, legend, "kWh", caption, nameFile, self.myShortMonths, sizeBox=15,
                                   addLines=addLines)

    def calculateSPFSystem(self):

        self.SpfShpDis = num.zeros(13)

        for i in range(len(self.qDemand)):
            if (self.elHeatSysTotal[i] == 0):
                self.SpfShpDis[i] = 0.
            else:
                self.SpfShpDis[i] = self.qDemand[i] / self.elHeatSysTotal[i]

        self.yearSpfShpDis = sum(self.qDemand) / sum(self.elHeatSysTotal)
        self.SpfShpDis[12] = self.yearSpfShpDis

    def addSPFSystem(self, printData=False):

        var = []

        qD = self.qDemand
        qD = num.append(qD, sum(self.qDemand))

        var.append(qD)

        el = self.elHeatSysTotal
        el = num.append(el, sum(self.elHeatSysTotal))

        var.append(el)

        var.append(self.SpfShpDis)

        nameFile = "SPF_SHP"
        legend = ["Month", "$Q_{demand}$", "$El_{Heat,Sys}$", "$SPF_{SHP}$"]
        caption = "Seasonal performance factor of the complete system"
        self.doc.addTableMonthlyDf(var, legend, ["", "kWh", "kWh", "-"], caption, nameFile, self.myShortMonths,
                                   sizeBox=15)

        yearlyFactor = 10.

        namePdf = self.plot.plotMonthlyDf(self.SpfShpDis, "$SPF_{SHP}$", nameFile, yearlyFactor, self.myShortMonths,
                                          myTitle=None, printData=printData)

        self.doc.addPlotShort(namePdf, caption=caption, label=nameFile)

        self.SPFShpWeighted = num.zeros(12)

        for i in range(len(self.qDemand)):
            self.SPFShpWeighted[i]=self.SpfShpDis[i]*self.qDemand[i]/sum(self.qDemand)

        nameFile = "SPF_SHP_weighted"

        namePdf = self.plot.plotMonthlyDf(self.SPFShpWeighted, "$\widetilde{SPF_{SHP}}$", nameFile, yearlyFactor, self.myShortMonths,
                                          myTitle=None, printData=printData)

        self.doc.addPlotShort(namePdf, caption=caption, label=nameFile)


    def addHeatBalance(self, printData=False):

        inVar = []
        outVar = []
        legendsIn = []
        legendsOut = []

        # for name in self.monData.keys():
        for name in self.monDataDf.columns:

            found = False

            try:
                if (name[0:7] == "qSysIn_" or name[0:10] == "elSysIn_Q_"):
                    # inVar.append(self.monData[name])
                    inVar.append(self.monDataDf[name].values)
                    legendsIn.append(self.getNiceLatexNames(name))


                elif (name[0:8] == "qSysOut_"):
                    # outVar.append(self.monData[name])
                    outVar.append(self.monDataDf[name].values)

                    legendsOut.append(self.getNiceLatexNames(name))
            except:
                pass

        nameFile = 'HeatMonthly'

        niceLegend = legendsIn + legendsOut

        # firstMonthId = self.monDataDf["Month"].index[0]

        # firstMonthId = utils.getMonthNameIndex(self.monDataDf["Month"].index)
        # startMonth = firstMonthId

        namePdf = self.plot.plotMonthlyBalanceDf(inVar, outVar, niceLegend, "Energy Flows", nameFile, "kWh",
                                                 self.myShortMonths, yearlyFactor=10,
                                                 useYear=False, printData=printData)

        for i in range(len(outVar)):
            outVar[i] = -outVar[i]

        var = inVar + outVar
        var.append(sum(inVar) + sum(outVar))

        names = ["Month"] + niceLegend + ["Imb"]

        caption = "System Heat Balance"

        totalDemand = sum(self.qDemand)

        imb = sum(var[len(var) - 1])

        addLines = ""
        symbol = "\%"
        line = "\\hline \\\\ \n";
        addLines = addLines + line
        line = "$Q_D$ & %.2f & MWh \\\\ \n" % (totalDemand / 1000.);
        addLines = addLines + line
        line = "Imb & %.1f & %s \\\\ \n" % (100 * imb / totalDemand, symbol);
        addLines = addLines + line

        self.doc.addTableMonthlyDf(var, names, "kWh", caption, nameFile, self.myShortMonths, sizeBox=15,
                                   addLines=addLines)
        self.doc.addPlotShort(namePdf, caption=caption, label=nameFile)

    def calculateElConsumption(self, printData=False):

        inVar = []
        outVar = []
        self.legendsElConsumption = []
        self.elHeatSysTotal = []  # vector of a sum of all electricity consumption used for the heating system
        self.elHeatSysMatrix = []  # matrix with all vectors included in the el consumption. For table printing and plot

        for name in self.monDataDf.columns:

            found = False

            try:
                if (name[0:9] == "elSysOut_" or name[0:10] == "elSysIn_Q_"):
                    el = self.monDataDf[name].values
                    self.elHeatSysMatrix.append(el)
                    # self.elHeatSysTotal = self.elHeatSysTotal + el
                    self.legendsElConsumption.append(self.getNiceLatexNames(name))
            except:
                pass

        self.elHeatSysTotal = sum(self.elHeatSysMatrix)

    def addElConsumption(self, printData=False):

        nameFile = 'elHeatSysMonthly'

        legend = self.legendsElConsumption
        inVar = self.elHeatSysMatrix
        outVar= []


        namePdf = self.plot.plotMonthlyBalanceDf(inVar, outVar, legend, "El heat system", nameFile, "kWh",
                                                 self.myShortMonths, yearlyFactor=10,
                                                 useYear=False, printImb=False, printData=printData)

        var = inVar
        self.elHeatSysTotal = sum(inVar)
        var.append(self.elHeatSysTotal)

        names = ["Month"] + legend + ["Total"]

        caption = "System El Heat Balance"

        self.doc.addTableMonthlyDf(var, names, "kWh", caption, nameFile, self.myShortMonths, sizeBox=15)
        self.doc.addPlotShort(namePdf, caption=caption, label=nameFile)

    def getListOfNiceLatexNames(self, legends):

        legendOut = []
        for name in legends:
            legendOut.append(self.getNiceLatexNames(name))

        return legendOut

    def getNiceLatexNames(self, name):

        name = name.lower()
        if (name == "qSysOut_DhwDemand".lower()):  # DHW demand
            niceName = "$Q_{DHW}$"

        elif (name == "qSysOut_BuiDemand".lower()):  # SH demand
            niceName = "$Q_{SH}$"

        elif (name == "qSysIn_BuiDemand".lower()):  # SC demand
            niceName = "$Q_{SC}$"

        elif (name == "qSysIn_Collector".lower()):  # Q solar
            niceName = "$Q_{col}$"

        elif (name == "elSysIn_Q_HpComp".lower()):  # Heat pump compressor
            niceName = "$El_{Hp,comp}$"

        elif (name == "elSysOut_PuCond".lower()):  # pump condenser
            niceName = "$El_{pu}^{cond}$"

        elif (name == "elSysOut_PuEvap".lower()):  # pump evaporator
            niceName = "$El_{pu}^{evap}$"

        elif (name == "elSysOut_PuSH".lower()):  # pump evaporator
            niceName = "$El_{pu}^{SH}$"

        elif (name == "qSysOut_TesLoss".lower()):  # losses TES
            niceName = "$Q^{Tes}_{loss}$"

        elif (name == "qSysOut_TesDhwLoss".lower()):  # losses TES DHW
            niceName = "$Q^{TesDhw}_{loss}$"

        elif (name == "qSysOut_TesShLoss".lower()):  # losses TES SH
            niceName = "$Q^{TesSh}_{loss}$"

        elif (name == "qSysOut_PipeLoss".lower()):  # losses pipes
            niceName = "$Q^{pipe}_{loss}$"

        elif (name == "elSysOut_HHDemand".lower()):  # Household Electricity demand
            niceName = "$El_{HH}$"

        elif (name == "elSysIn_PV".lower()):  # PV to the system
            niceName = "$El_{PV}$"

        elif (name == "elSysOut_InvLoss".lower()):  # Inverter losses
            niceName = "$El^{inv}_{loss}$"

        elif (name == "elSysOut_BatLoss".lower()):  # Batrtery losses
            niceName = "$El^{bat}_{loss}$"

        elif (name == "elSysIn_Grid".lower()):  # GRID to the system
            niceName = "$El_{grid}$"

        elif (name == "elSysOut_PvToGrid".lower()):  # Pv to GRID
            niceName = "$El_{Pv2Grid}$"

        elif (name == "elSysIn_Q_TesShAux".lower()):  # Auxiliar back up in Tes SH
            niceName = "$El_{Aux}^{TesSh}$"

        elif (name == "elSysIn_Q_TesAux".lower()):  # Auxiliar back up in Tes SH
            niceName = "$El_{Aux}^{Tes}$"

        elif (name == "elSysIn_Q_TesDhwAux".lower()):  # Auxiliar back up in Tes DHW
            niceName = "$El_{Aux}^{TesDhw}$"

        elif (name == "qSysIn_Ghx".lower()):  # Heat inputs grom GHX
            niceName = "$Q_{GHX}$"

        else:
            niceName = self.getCustomeNiceLatexNames(name)
            if(niceName==None):
                niceName = "$%s$" % name

        return niceName

    def getCustomeNiceLatexNames(self,name):
        return None

    def loadDll(self):

        self.log = LogTrnsys.LogTrnsys(self.outputPath, self.fileName)
        self.log.loadLog()
        self.log.getMyDataFromLog()
        self.calcTime = self.log.getCalculationTime()

        self.iteErrorMonth = self.log.getIteProblemsForEachMonth

        self.nItProblems = self.log.numberOfFailedIt

    def getVersionsDll(self):

        if (0):
            raise ValueError("Deprecated. File created in simulaiton folder. To be improved")
            #
            #        namesDll= ["type860","type1924","type709","type878","type859","Type832","Type833"]

            namesDll = []
            myset = set(self.readTrnsysFiles.TrnsysTypes)  # get the unique names (all repeated ones are excluded)
            print (myset)

            for number in myset:
                nameType = "type%s" % number
                namesDll.append(nameType)

            self.dllVersions = self.getDllVersionFromType(namesDll)

            self.buildingModel = None
            for dll in self.dllVersions:
                print (dll)
                if (dll[0:6] == "type56"):
                    self.buildingModel = "Type56"
                elif (dll[0:8] == "type5998"):
                    self.buildingModel = "ISO"

    def getDllVersionFromType(self, typeNumber):

        if (self.trnsysDllPath == False):

            if (self.trnsysVersion == "standard"):
                trnsysExe = os.getenv("TRNSYS_EXE")

            else:
                trnsysExe = os.getenv(self.trnsysVersion)

            print (trnsysExe)

            mySplit = trnsysExe.split("Exe")
            self.trnsysDllPath = mySplit[0] + "\\UserLib\\ReleaseDLLs"
        else:
            pass

        print ("Dll path:%s" % self.trnsysDllPath)

        listDll = os.listdir(self.trnsysDllPath)

        dllVersion = []
        for name in typeNumber:
            nameFound = False
            for dll in listDll:
                if (dll[-3:] == "dll"):
                    #                    print "%s %s" % (dll,name)
                    if (dll.count(name) == 1 and nameFound == False):
                        nameFound = True
                        dllVersion.append(dll)
                        print ("FOUND %s %s" % (dll, name))
                        break

        print (dllVersion)
        #        raise ValueError()

        return dllVersion

    def getTagLabel(self, label):

        return ("#=======================================\n#%s :%s\n#=======================================\n" % (
        self.nameClass, label))

    def setPathReadTrnsysFile(self, _path):

        self.readTrnsysFiles.setPath(_path)

    def addResultsFile(self):
        """
        Save results to a results.json file.

        Function uses results stringArray from config file to provide keys that will be saved
        :return:
        """
        print("creating results.json file")

        self.resultsDict = {}

        for key in self.inputs['results']:
            if type(self.__dict__[key]) == num.ndarray:
                value = list(self.__dict__[key])
            else:
                value = self.__dict__[key]
            self.resultsDict[key] = value

        fileName = self.fileName+'-results.json'
        fileNamePath = os.path.join(self.outputPath, fileName)
        with open(fileNamePath, 'w') as fp:
            json.dump(self.resultsDict, fp, indent = 2, separators=(',', ': '),sort_keys=True)