#!/usr/bin/python

"""
Child class from ProcessMonthlyDataBase used for processing all TRNSYS simulations.

Author : Dani Carbonell
Date   : 2018
ToDo :
"""

import os
import string,shutil
import TrnsysTools.processingData.processFiles as spfUtils
import processMonthlyDataBase as monthlyData #changed in order to clean the processing of files
import TrnsysTools.utilities.utilsSpf as utils
import time
import numpy as num
import matplotlib.pyplot as plt
import TrnsysTools.Trnsys.readTrnsysFiles as readTrnsysFiles
import unitConverter as unit
import TrnsysTools.Trnsys.LogTrnsys as LogTrnsys

class ProcessTrnsys(monthlyData.ProcessMonthlyDataBase):

    def __init__(self,_path,_name):
                        
        monthlyData.ProcessMonthlyDataBase.__init__(self,_path,_name)
#        
#        self.fileName = _name.split('.')[0]                                          
#        self.outputPath = _path + "\%s" % self.fileName              

        self.cleanModeLatex = False

        self.tempFolder = "%s\\temp" % self.outputPath
        self.tempFolderEnd = "%s\\temp" % self.outputPath  
              
        self.trnsysVersion = "standard"
        self.yearReadedInMonthylFile = -1 #-1 means the last
        self.firstMonth = "January"

        self.yearlyFactor = 10.  # value to divide yerarly values when plotted along with monthly data
        self.units = unit.UnitConverter()

        # self.qWcpHPPlusAux = num.zeros(12)
        # self.qHpAux = num.zeros(12)
        
        self.loadPCM = False 
        self.solarFileLoaded = False #To erase or to fill up depending on document class
        
        self.multiPort = False # HighIce use Multiport and some symbols are changed. QLoss    
        
        
        self.readTrnsysFiles = readTrnsysFiles.ReadTrnsysFiles(self.tempFolderEnd)

        # self.tInEvapHpMonthlyMax = num.zeros(12,float)
        # self.tInEvapHpMonthlyMin = num.zeros(12,float)
        # self.tInEvapHpMonthlyAv  = num.zeros(12,float)
                     
        self.nameClass = "ProcessTrnsys"
        self.unit = unit.UnitConverter()
        self.trnsysDllPath = False

#    def readTrnsysDeck(self):
        
        
        #the idea is to read the deck and get important information fro processing.
        #area collector, volume ice storage, volume Tes, Area uncovered, nH1, nominal power heat pump, etc...
    def setBuildingArea(self,area):
        self.buildingArea = area

    def setTrnsysDllPath(self,path):

        self.trnsysDllPath = path

    def setBuildingArea(self,area):
        self.buildingArea = area

    def getNameCity(self, nCity):

        utils.getNameCity(nCity)

    def setTrnsysVersion(self,version):
        self.trnsysVersion = version

    def setPrintDataForGle(self,printData):

       self.printDataForGle=printData

    def loadAndProcess(self):

        self.loadFiles()
        self.process()

    def loadFiles(self):
        pass

    def process(self):
        pass

    def loadDll(self):

        self.log = LogTrnsys.LogTrnsys(self.outputPath, self.fileName)
        self.log.loadLog()
        self.log.getMyDataFromLog()
        self.calcTime = self.log.getCalculationTime()

        self.iteErrorMonth = self.log.getIteProblemsForEachMonth

        self.nItProblems = self.log.numberOfFailedIt

    def getVersionsDll(self):
        #
        #        namesDll= ["type860","type1924","type709","type878","type859","Type832","Type833"]

        namesDll = []
        myset = set(self.readTrnsysFiles.TrnsysTypes)  # get the unique names (all repeated ones are excluded)
        print myset

        for number in myset:
            nameType = "type%s" % number
            namesDll.append(nameType)

        self.dllVersions = self.getDllVersionFromType(namesDll)

        self.buildingModel = None
        for dll in self.dllVersions:
            print dll
            if (dll[0:6] == "type56"):
                self.buildingModel = "Type56"
            elif (dll[0:8] == "type5998"):
                self.buildingModel = "ISO"

    def getDllVersionFromType(self,typeNumber):

        if(self.trnsysDllPath==False):

            if(self.trnsysVersion=="standard"):
                trnsysExe  = os.getenv("TRNSYS_EXE")

            else:
                trnsysExe  = os.getenv(self.trnsysVersion)

            print trnsysExe

            mySplit = trnsysExe.split("Exe")
            self.trnsysDllPath = mySplit[0] + "\\UserLib\\ReleaseDLLs"
        else:
            pass

        print "Dll path:%s" % self.trnsysDllPath
        
        listDll= os.listdir(self.trnsysDllPath)
        
        dllVersion = []
        for name in typeNumber:        
            nameFound=False
            for dll in listDll:
                if(dll[-3:]=="dll"):
#                    print "%s %s" % (dll,name)                          
                    if(dll.count(name)==1 and nameFound==False):
                        nameFound = True
                        dllVersion.append(dll)    
                        print "FOUND %s %s" % (dll,name)  
                        break
             
        print dllVersion
#        raise ValueError()
        
        return dllVersion
        
    def getTagLabel(self,label):
        
        return ("#=======================================\n#%s :%s\n#=======================================\n" % (self.nameClass,label))
    
    def setPathReadTrnsysFile(self,_path):
        
        self.readTrnsysFiles.setPath(_path)

    #############################################
    # Section for loading files
    #############################################

    def loadSolar(self,_name):
           
         self.readTrnsysFiles.readMonthlyFiles(_name,firstMonth=self.firstMonth,myYear=self.yearReadedInMonthylFile)
         
         self.numberOfMonthsSimulated = self.readTrnsysFiles.numberOfMonthsSimulated
                  
         self.existSolarLoop   = True    
         self.solarFileLoaded  = True
         
         self.qSolarToSystem = self.readTrnsysFiles.get("Pcoll_KW")                
         self.qSunToCol = self.readTrnsysFiles.get("P_IRRAD_kW")                     
         self.qLossPipeSolarLoop = self.readTrnsysFiles.get("PPiCLoss_kW")
                                        
#         print self.qSolarToSystem
#         print self.qLossPipeSolarLoop
                                
         if(self.parallelSystem):       
             for i in range(self.numberOfMonthsSimulated):
                 self.qSolarToTes[i] = self.qSolarToSystem[i] - self.qLossPipeSolarLoop[i]                            
         else:
             print "Serial system and qSolartoTes must be readed from Storage data"

    def loadWeatherData(self,_name):
           
         self.readTrnsysFiles.readMonthlyFiles(_name,firstMonth=self.firstMonth,myYear=self.yearReadedInMonthylFile)
         self.numberOfMonthsSimulated = self.readTrnsysFiles.numberOfMonthsSimulated

         self.iTHorizontalkWPerM2 = self.readTrnsysFiles.get("IT_H_KW") 
         self.iTColkWPerM2        = self.readTrnsysFiles.get("IT_Coll_kW")
         self.tAmb                = self.readTrnsysFiles.get("tAmb")

    def loadStorage(self,_name):
                              
        self.readTrnsysFiles.readMonthlyFiles(_name,firstMonth=self.firstMonth,myYear=self.yearReadedInMonthylFile)
        self.numberOfMonthsSimulated = self.readTrnsysFiles.numberOfMonthsSimulated              
                      
        self.qTesFromSolar = abs(self.readTrnsysFiles.get("PSC_kW"))     
        self.qOutFromTesToSH = abs(self.readTrnsysFiles.get("PSB_kW"))
        self.qOutFromTesToDHW = abs(self.readTrnsysFiles.get("PSD_kW"))
        self.qLossTes = self.readTrnsysFiles.get("PSt_loss_kW")                              
                  
        self.qTesDhwFromHp  = self.readTrnsysFiles.get("PSA1_kW")        
        self.qTesShFromHp  = self.readTrnsysFiles.get("PSA2_kW")        
        
        self.qTesFromHp  = self.qTesShFromHp + self.qTesDhwFromHp
        
      
        if(abs(sum(self.qTesFromHp) - (sum(self.qTesDhwFromHp)+sum(self.qTesShFromHp))>1)):
            
           print "Something goes wrong QTesFromHp:%f QTesFromHPDhwSh:%f "%(sum(self.qTesFromHp),sum(self.qTesDhwFromHp)+sum(self.qTesShFromHp))

        self.qOutFromTes = num.zeros(12)

        for i in range(12):
            if(self.multiPort):
                self.qLossTes[i] = -self.qLossTes[i]                                    
            self.qOutFromTes[i] = self.qOutFromTesToSH[i] + self.qOutFromTesToDHW[i]

#            print "qOutTnk:%f qOutTnkSH:%f qOutTnkDHW:%f" % (self.qOutFromTes[i],self.qOutFromTesToSH[i],self.qOutFromTesToDHW[i])
                    
        self.qOutFromTesFound = True

    def loadBuilding(self,_name):

        self.readTrnsysFiles.readMonthlyFiles(_name,myYear=self.yearReadedInMonthylFile,firstMonth=self.firstMonth)
        # self.numberOfMonthsSimulated = self.readTrnsysFiles.numberOfMonthsSimulated

        self.qSHDemand = self.readTrnsysFiles.get("PheatBui_kW")      
        self.qRadiator = self.readTrnsysFiles.get("PRdIn_kW",ifNotFoundEqualToZero=True)

        self.qSH = self.qSHDemand #Changed !!

        self.qBuiGroundLosses = self.readTrnsysFiles.get("PBuiGrd_kW",ifNotFoundEqualToZero=True)

        self.qBuiIntGainPeople = self.readTrnsysFiles.get("PBuiGainPers_KW",ifNotFoundEqualToZero=True)
        self.qBuiIntGainEq = self.readTrnsysFiles.get("PBuiGainEq_KW",ifNotFoundEqualToZero=True)
        self.qBuiIntGainLight = self.readTrnsysFiles.get("PBuiLight_kW",ifNotFoundEqualToZero=True)

        self.qBuiSolarGains   = self.readTrnsysFiles.get("PBuiSol_kW",ifNotFoundEqualToZero=True)       
        self.qBuiRadiatorGains = self.readTrnsysFiles.get("PBuiGains_KW",ifNotFoundEqualToZero=True)
        
        self.qBuiTransLosses  = self.readTrnsysFiles.get("PBuiUAstatic_kW") #

            
        self.qBuiInfLosses    = self.readTrnsysFiles.get("PbuiInf_kW",ifNotFoundEqualToZero=True)
        self.qBuiVentLosses   = self.readTrnsysFiles.get("PbuiVent_kW",ifNotFoundEqualToZero=True)

        self.qShFromHp = self.readTrnsysFiles.get("QShFromHp",ifNotFoundEqualToZero=True)
        self.qShFromTes = self.readTrnsysFiles.get("QShFromTes",ifNotFoundEqualToZero=True)        

        self.qAcumRadiator   = self.readTrnsysFiles.get("QAcumRadiator",ifNotFoundEqualToZero=True)

        self.qBuiAcum       = self.readTrnsysFiles.get("PAcumBui_kW",ifNotFoundEqualToZero=True)
                
        self.qBuiHeat = num.zeros(12)            
        self.qBuiCool = num.zeros(12)    


        for i in range(12):
            self.qBuiHeat[i] = max(self.qSH[i],0.0)
            self.qBuiCool[i] = -min(self.qSH[i],0.0)
      
        self.buildingDataLoaded =True
        self.existUserCircuitSH = True

    def readBuildingHourlyDataType56(self,_name):
 
        self.readTrnsysFiles.readHourlyBuildingFile(_name)                  
        self.buildingDataLoaded =True
                                      
        print "READING HORLY DATA FROM BUILDING TYPE 56"
       

#['TIME', 'REL_BAL_ENERGY', '1_B4_QBAL=-', '1_B4_DQAIRdT+', '1_B4_QHEAT-', '1_B4_QCOOL+', '1_B4_QINF+', '1_B4_QVENT+', '1B4_QCOUP+', '1_B4_QTRANS+', '1_B4_QGINT+', '1_B4_QWGAIN+', '1_B4_QSOL+', '1_B4_QSOLAIR+']

        self.qBuiHeatHour = self.readTrnsysFiles.get("1_B4_QHEAT-")        
        self.qBuiCoolHour = self.readTrnsysFiles.get("1_B4_QCOOL+")    
    
        self.qBuiSolarGainsHour  = self.readTrnsysFiles.get("1_B4_QSOL+")            
        self.qBuiIntGainsHour    = self.readTrnsysFiles.get("1_B4_QGINT+")       
        self.qBuiTransLossesHour = self.readTrnsysFiles.get("1_B4_QTRANS+")
        self.qBuiInfLossesHour   = self.readTrnsysFiles.get("1_B4_QINF+")
        self.qBuiVentLossesHour  = self.readTrnsysFiles.get("1_B4_QVENT+")

        #The heat of the buiding readed is zero, so I recalculated it.

#        for i in range(len(self.qBuiSolarGainsHour)):   
#        for i in range(2):   

#            gain   = self.qBuiSolarGainsHour[i]+self.qBuiIntGainsHour[i]
#            loss = self.qBuiTransLossesHour[i]+self.qBuiInfLossesHour[i]+self.qBuiVentLossesHour[i]        
#            self.qBuiHeatHour[i]=-(gain+loss) #kJ/h
#            print "hour%d gain:%f loss:%f"%(i,gain,loss)
            
        self.qBuiHeat = utils.calculateMonthlyValues(self.qBuiHeatHour)                   
        self.qBuiCool = utils.calculateMonthlyValues(self.qBuiCoolHour)                                                             
        self.qBuiSolarGains = utils.calculateMonthlyValues(self.qBuiSolarGainsHour)*self.unit.getJTokWh()*1000.        
        
        #Probably this is the sum of radiator and internal gains
        self.qBuiGains = utils.calculateMonthlyValues(self.qBuiIntGainsHour)*self.unit.getJTokWh()*1000.
        
        self.qBuiTransLosses = utils.calculateMonthlyValues(self.qBuiTransLossesHour)*self.unit.getJTokWh()*1000.
        self.qBuiInfLosses   = utils.calculateMonthlyValues(self.qBuiInfLossesHour)*self.unit.getJTokWh()*1000.

#        print self.qBuiInfLosses
#        raise ValueError("")
        
        self.qBuiVentLosses  = utils.calculateMonthlyValues(self.qBuiVentLossesHour)*self.unit.getJTokWh()*1000.
                
        yearlyHeatDemand = sum(self.qBuiSolarGains)+sum(self.qBuiGains)+sum(self.qBuiTransLosses)+sum(self.qBuiInfLosses)+sum(self.qBuiVentLosses)
        
        print "YEARLY DEMAND IN BUILDING :%f kWh"% yearlyHeatDemand
        
        for i in range(12):
            print "month:%d GAIN solar:%f int(rad+conv):%f LOSS Inf:%f Trns:%f Vent:%f"% (i+1,self.qBuiSolarGains[i],self.qBuiGains[i],self.qBuiInfLosses[i],self.qBuiTransLosses[i],self.qBuiVentLosses[i])

    def loadDHW(self,_name):
        
        self.existUserCircuitDHW = True
        
        self.readTrnsysFiles.readMonthlyFiles(_name,firstMonth=self.firstMonth,myYear=self.yearReadedInMonthylFile)
        self.numberOfMonthsSimulated = self.readTrnsysFiles.numberOfMonthsSimulated 
                
        self.qDHW =  self.readTrnsysFiles.get("Pdhw_kW")                    
        self.qHxLossDHW = self.readTrnsysFiles.get("PhxDloss_kW")       
        # self.qPipeLossDHW = self.readTrnsysFiles.get("PPiDHWLoss_kW") I centralize pipe losses in one file loadPipeLosses (not done at this level yet)
        self.pElDhwPenalty =  self.readTrnsysFiles.get("PpenDHW_kW",ifNotFoundEqualToZero=True)

    def loadElectric(self,_name):
            
        self.readTrnsysFiles.readMonthlyFiles(_name,firstMonth=self.firstMonth,myYear=self.yearReadedInMonthylFile)
        self.numberOfMonthsSimulated = self.readTrnsysFiles.numberOfMonthsSimulated        
        
        self.pumpSH =  self.readTrnsysFiles.get("PelPuSh_kW")
        self.qWcpHPPlusAux = self.readTrnsysFiles.get("PelAuxTot_kW")                    
        self.qWcpHP = self.readTrnsysFiles.get("PelAuxComp_kW") 
           
        self.pumpHPsink = self.readTrnsysFiles.get("PelPuAuxTot_kW",ifNotFoundEqualToZero=True)            
        self.pumpHPsource = self.readTrnsysFiles.get("PelPuBri_kW")                 

        if(self.pumpHPsource == None):
            self.pumpHPsource = self.readTrnsysFiles.get("PelPuGHX_kW",ifNotFoundEqualToZero=True)                   
       
        # if(sum(self.qAuxHeaterSh)==0.0):
        # self.qAuxHeaterSh = self.readTrnsysFiles.get("PelHeater_kW",ifNotFoundEqualToZero=True)
              
        self.pumpSolar = self.readTrnsysFiles.get("PelPuC_kW",ifNotFoundEqualToZero=True)
        self.pumpDHW = self.readTrnsysFiles.get("PelPuDHW_kW",ifNotFoundEqualToZero=True)
        self.pElControllerSolar = self.readTrnsysFiles.get("PelContr_kW",ifNotFoundEqualToZero=True)
        self.pElControllerHp = self.readTrnsysFiles.get("PelContr_kW",ifNotFoundEqualToZero=True)

        #This control is done because in some decks these values are readed from another source.  

        try:
            if(sum(self.pElDhwPenalty)>0):
                pass
            else:
                self.pElDhwPenalty = self.readTrnsysFiles.get("PpenDHW_kW", ifNotFoundEqualToZero=True)
        except:
            self.pElDhwPenalty =  self.readTrnsysFiles.get("PpenDHW_kW",ifNotFoundEqualToZero=True)  

        try:
            if(sum(self.pElShPenalty)>0):
                pass
            else:
                self.pElShPenalty = self.readTrnsysFiles.get("PpenSH_kW", ifNotFoundEqualToZero=True)
        except:
            self.pElShPenalty =  self.readTrnsysFiles.get("PpenSH_kW",ifNotFoundEqualToZero=True)

        self.pElPenalty = num.zeros(12)
        self.pElController = num.zeros(12)

        for i in range(self.numberOfMonthsSimulated):                                                   
            self.pElPenalty[i] = self.pElShPenalty[i]+self.pElDhwPenalty[i]

            #In the results we get the sum of both values so:It may be the case that there is only one pump to Sh so the pumpHpsink=0
            self.pumpHPsink[i] = max(self.pumpHPsink[i] - self.pumpHPsource[i],0.0)
            self.pElController[i] = self.pElControllerSolar[i] + self.pElControllerHp[i]        
            

        
        
#     def loadSystem(self,_name):

    def loadWorkingHoursFromMonthy(self,_name):                    

        self.readTrnsysFiles.readMonthlyFiles(_name,firstMonth=self.firstMonth,myYear=self.yearReadedInMonthylFile)
                    
        self.onOffPumpCol   = self.readTrnsysFiles.get("BoCnoOn",ifNotFoundEqualToZero=True)    
        self.onOffPumpHpDhw = self.readTrnsysFiles.get("BoAuxWWon",ifNotFoundEqualToZero=True)  
        self.onOffPumpHpSh  = self.readTrnsysFiles.get("BoAuxSHOn",ifNotFoundEqualToZero=True)          
        self.onOffPumpSh    = self.readTrnsysFiles.get("BoPumpShOn",ifNotFoundEqualToZero=True)

        self.onOffPumpHp = num.zeros(12)

        for i in range(12):      
            self.onOffPumpHp[i] = self.onOffPumpHpDhw[i]+self.onOffPumpHpSh[i]
            
    def loadWorkingHours(self,_name):
        
       
        self.readTrnsysFiles.readUserDefinedFiles(_name)
        
        self.onOffPumpColUserDefined   = self.readTrnsysFiles.get("BoCnoOn")
        self.onOffPumpHpDhwUserDefined = self.readTrnsysFiles.get("BoAuxWWon")
        self.onOffPumpHpShUserDefined  = self.readTrnsysFiles.get("BoAuxSHOn")        
        
#        BoPumpShOn
        
        for i in range(len(self.onOffPumpColUserDefined)):                                       
            #Domestic hot water priority
            if(self.onOffPumpHpDhwUserDefined[i]==1):
                self.onOffPumpHpShUserDefined[i]=0.

        self.onOffPumpCol = utils.calculateMonthlyValuesFromUserDefinedTimeStep(self.onOffPumpColUserDefined,120)
        self.onOffPumpHpDhw = utils.calculateMonthlyValuesFromUserDefinedTimeStep(self.onOffPumpHpDhwUserDefined,120)
        self.onOffPumpHpSh = utils.calculateMonthlyValuesFromUserDefinedTimeStep(self.onOffPumpHpShUserDefined,120)
        
        for i in range(12):                    
            self.onOffPumpCol[i] = self.onOffPumpCol[i]*(120./3600.) 
            self.onOffPumpHpDhw[i] = self.onOffPumpHpDhw[i]*(120./3600.) 
            self.onOffPumpHpSh[i] = self.onOffPumpHpSh[i]*(120./3600.)             
            self.onOffPumpHp[i] = self.onOffPumpHpDhw[i]+self.onOffPumpHpSh[i]
  
    def loadHP(self,_name):
        
        self.readTrnsysFiles.readMonthlyFiles(_name,firstMonth=self.firstMonth,myYear=self.yearReadedInMonthylFile)
        self.numberOfMonthsSimulated = self.readTrnsysFiles.numberOfMonthsSimulated  
        
        self.existHeatGeneratorLoop = True        
        # self.qPipeLossHPSink = self.readTrnsysFiles.get("PPiAuxLossTot_kW",ifNotFoundEqualToZero=True) #DCAR centralized in loadPipeLosses

        self.qAuxHeaterHp  = num.zeros(12)

        self.qHpToSh          = self.readTrnsysFiles.get("PAuxSH_kW",ifNotFoundEqualToZero=True)                                        
        self.qAirEvapHp       = self.readTrnsysFiles.get("PauxEvapAir_kW",ifNotFoundEqualToZero=True)
        self.qBrineEvapHp     = self.readTrnsysFiles.get("PauxEvapBrine_kW",ifNotFoundEqualToZero=True)
        self.qEvapHP          = self.readTrnsysFiles.get("PauxEvap_kW",ifNotFoundEqualToZero=True)
        self.lossDefrostingHp = self.readTrnsysFiles.get("PauxDefrost_kW",ifNotFoundEqualToZero=True)
        self.lossCyclingHp    = self.readTrnsysFiles.get("PauxLossStart_kW",ifNotFoundEqualToZero=True) 
        self.lossThermalHp    = self.readTrnsysFiles.get("PAuxLossAmb_kW",ifNotFoundEqualToZero=True)        
            
        self.pElVentilatorHP = self.readTrnsysFiles.get("PelAuxVent_kW",ifNotFoundEqualToZero=True)
        self.qCondHP =  self.readTrnsysFiles.get("PauxCond_kW")
        self.qDesuperHeaterHP = self.readTrnsysFiles.get("PauxDesup_kW",ifNotFoundEqualToZero=True)                                            
        
        self.qHpInShMode = self.readTrnsysFiles.get("PauxCondSh_kW")
        self.qHpInDhwMode = self.readTrnsysFiles.get("PauxCondDHW_kW")

        #This value does not include the PiAuxRt !!neither the term QHpToSh
        self.qHpToTesSh  = None #self.readTrnsysFiles.get("PAuxTES_kW")
        
        if(self.qHpToTesSh==None):
            #This includes then the PiAuxRt pipe losses
            self.qHpToTesSh  = self.qHpInShMode - self.qHpToSh
            
            print "QHpInSHMode:%f QHpToTesSH:%f QHpToSHLoop:%f"%(sum(self.qHpInShMode),sum(self.qHpToTesSh),sum(self.qHpToSh))

        self.qHpToTesDhw = self.qHpInDhwMode
        self.qHpToTes    = self.qHpToTesSh+self.qHpToTesDhw

        self.qLossHp = num.zeros(12)

        for i in range(self.numberOfMonthsSimulated):                           
                                                   
            self.qLossHp[i] = self.lossDefrostingHp[i] + self.lossCyclingHp[i] + self.lossThermalHp[i]
            self.qCondHP[i] = self.qCondHP[i] + self.qDesuperHeaterHP[i] 
            # imbSH = self.qHpInShMode[i]-self.qHpToSh[i]-self.qTesShFromHp[i]
            # imbDHW = self.qHpInDhwMode[i]-self.qTesDhwFromHp[i]
            # print "HP SH(mode):%f DHW(mode):%f TO-SH:%f TO-DHWTES:%f TO-SHTES:%f imbSH:%f imbDHW:%f"%(self.qHpInShMode[i],self.qHpInDhwMode[i],self.qHpToSh[i],self.qTesDhwFromHp[i],self.qTesShFromHp[i],imbSH,imbDHW)
       
    def calculateDemand(self):
        
        self.qUseFound=True
        self.qDemandFound=True

        self.pElPenalty = self.pElShPenalty + self.pElDhwPenalty
        self.qUse = self.qDHW + self.qSH
        self.qDemand = self.qUse + self.pElShPenalty + self.pElDhwPenalty
        self.qDemandDhw = self.qDHW + self.pElDhwPenalty
        self.qDemandSh = self.qSH + self.pElShPenalty
        self.qUseDhw = self.qDHW
        self.qUseSh = self.qSH

        # for i in range(self.firstMonthIndex,self.firstMonthIndex+self.numberOfMonthsSimulated):
        #     self.pElPenalty[i] = self.pElShPenalty[i]+self.pElDhwPenalty[i]
        #     self.qUse[i] = self.qDHW[i] + self.qSH[i]
        #     self.qDemand[i] = self.qUse[i]+self.pElShPenalty[i]+self.pElDhwPenalty[i]
        #     self.qDemandDhw[i] =  self.qDHW[i] + self.pElDhwPenalty[i]
        #     self.qDemandSh[i] =  self.qSH[i] + self.pElShPenalty[i]
        #     self.qUseDhw[i] = self.qDHW[i]
        #     self.qUseSh[i] = self.qSH[i]
