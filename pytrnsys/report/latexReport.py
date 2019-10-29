
#!/usr/bin/python

"""
Class to produce automatic reports using LaTeX
Author : Daniel Carbonell
Date   : 2016
ToDo :
"""

import string, os
import pytrnsys.utils.utilsSpf as utils
import shutil

class LatexReport():
    
    def __init__(self,_outputPath,_name):

        self.outputPath = _outputPath    
        self.fileName = _name+"-report"
        self.fileNameTex = "%s.tex" % self.fileName
        self.fileNameTexWithPath = '%s\\%s' % (self.outputPath,self.fileNameTex)

        self.lines =""
        self.nameAuthor = utils.getNameFromUserName()
        self.email = utils.getEmailFromUserName()
        self.title = "unknown"
        self.subTitle = "unknown"
        self.documentClass = "SPFShortReport"

        self.latexExePath = "enviromentalVariable"

        # Every time we add a plot we increase this vector and it is used
        # to remove them after pdf creation if cleanMode=True


        pathReport = os.path.join(os.path.dirname(__file__),'latex_doc')

        if 'TEXINPUTS' in os.environ:
            texinputs = os.environ['TEXINPUTS']
            if pathReport not in texinputs:
                os.environ['TEXINPUTS']+=os.pathsep + pathReport
        else:
            os.environ['TEXINPUTS'] =pathReport
        
        self.cleanMode=False
        self.plotsAdded = [] 

    def resetTexName(self,name):

        self.fileName = name
        self.fileNameTex = "%s.tex" % self.fileName
        self.fileNameTexWithPath = '%s\\%s' % (self.outputPath,self.fileNameTex)

    def setCleanMode(self,_mode):
        self.cleanMode = _mode
        
    def setDocumentClass(self,_name):
        
         self.documentClass = _name
         
    def setAuthor(self,_name):
        self.nameAuthor = _name
        
    def setEMail(self,_name):
        self.email = _name    
    
    def setTitle(self,_name):
        self.title = _name
        
    def setSubTitle(self,_name):
        self.subTitle = _name

    def cleanFiles(self):
        
        for plotName in self.plotsAdded:
            pdfWithPath = "%s\\%s" % (self.outputPath,plotName)
            
            print ("Cleaning Latex Mode file %s"% pdfWithPath)
            os.remove(pdfWithPath)
            
            
    def executeLatexFile(self,removeAuxFiles=False,pathLatexExe=False,moveToTrnsysLogFile=False,runTwice=False,LatexPackage="pdflatex"):
        'function to execute latex file, the function can use either "pdflatex" or "texify" to create pdf.'

        logFile = '%s\%s.log' % (self.outputPath,self.fileName)
        logFileEnd = logFile
        
        if(moveToTrnsysLogFile==True):
            
            logFileEnd = '%s\%s.TRNSYS.log' % (self.outputPath,self.fileName)
            
            try:
                shutil.copy(logFile,logFileEnd)      
                print ("copy file %s to %s" % (logFile,logFileEnd))
            except:
                print ("FAIL to copy the file %s to %s" % (logFile,logFileEnd))

        if pathLatexExe==False:
            latexExe = os.getenv("LATEX_EXE")

            latexExe ='"%s"'% latexExe
        else:
            latexExe = '"%s"' % pathLatexExe


#        fileNameTexWithPath = '"%s\\%s"'%(self.outputPath,self.fileNameTex)
        if LatexPackage=="texify":
            cmd = "%s --pdf  --tex-option=-synctex=1 --tex-option=-aux-directory=\"%s\" --clean --tex-option=-output-directory=\"%s\" --silent \"%s\"" % (latexExe,self.outputPath,self.outputPath,self.fileNameTexWithPath)
        elif LatexPackage=="pdflatex":
#            cmd = "pdflatex --silent --output-directory=\"%s\" %s.tex" %(self.outputPath, self.fileName)
            cmd = "pdflatex --silent --output-directory=\"%s\" %s" %(self.outputPath, self.fileNameTex)
        else:
            raise ValueError('The specified LatexPackage \"%s\" is not implemented yet or does not exist.'%LatexPackage)

#        print cmd
        myCmd ='"%s"'%cmd #for blank spaces in paths
        os.system(myCmd)  
        
        if(runTwice): #necessary to generate table of contents
            os.system(myCmd)

        if(moveToTrnsysLogFile==True and removeAuxFiles):
            os.remove(logFileEnd)
        name='%s\%s.log' % (self.outputPath,self.fileName)
        
        try:
            os.remove(name)        
        except:
            print (name + " could not be removed, maybe there was a problem with the Latex File...")
            
        name='%s\%s.aux' % (self.outputPath,self.fileName)
        try:
            os.remove(name)        
        except:
            print (name + " could not be removed, maybe there was a problem with the Latex File...")

        
        if LatexPackage=="texify":
            name='%s\%s.synctex.gz' % (self.outputPath,self.fileName)
            try:
                os.remove(name)        
            except:
                print (name + " could not be removed, maybe there was a problem with the Latex File...")
            
        if os.path.isfile(self.outputPath + "\\" + self.fileName + ".pdf"):
           print ("Latex File created sucessfully")
        else:
            raise ValueError('PDF was not generated, or not saved in the right directory')
          
        
        if(self.cleanMode):
            print ("Eraising plots because cleanMode is True")
            self.cleanFiles()
        
    def addBeginDocument(self):                              
        
        line="\\documentclass[english]{%s}\n" % (self.documentClass) ; self.lines = self.lines + line               
        line="\\usepackage{subfigure}\n" ; self.lines = self.lines + line 
        line="\\usepackage{longtable}\n" ; self.lines = self.lines + line

        line="\\usepackage{url}\n" ; self.lines = self.lines + line
        line="\\usepackage{gensymb}\n" ; self.lines = self.lines + line

        line="\\usepackage{booktabs}\n" ; self.lines = self.lines + line


        line="\\usepackage[yyyymmdd,hhmmss]{datetime}\n" ; self.lines = self.lines + line 

        line="\\reportName{%s}\n" % self.title ; self.lines = self.lines + line
        line="\\reportSubName{%s} \n" % self.subTitle ; self.lines = self.lines + line
        line="\\reportDate{\\today \hspace{0.1cm} at: \\currenttime \hspace{0.1cm} h} \n" ; self.lines = self.lines + line
#        line="\\reportDate{\\currenttime \hspace{0.1cm} h} \n" ; self.lines = self.lines + line
        line="\\author{%s}\n" % self.nameAuthor ; self.lines = self.lines + line

        line="\\address{%s}\n" % self.email ; self.lines = self.lines + line        
        line="\\begin{document}\n" ; self.lines = self.lines + line         
    
    def addEndDocumentAndCreateTexFile(self):
        
        line="\\end{document}\n" ; self.lines = self.lines + line    

#        print self.fileNameTexWithPath
        
        outfile=open(self.fileNameTexWithPath,'w')   

        outfile.writelines(self.lines)
        outfile.close() 

    def addSection(self,line):
        
        lines = "\\section{%s}\n" % line
        self.lines = self.lines + lines                
                
    def addUserTex(self,lines):
        
        self.lines = self.lines + lines                
        
    def clearPage(self):
        
        line=" \\clearpage \n" 
        
        self.lines = self.lines + line
        
    def addPlot(self,namePdf,caption,label,size):
                
        self.plotsAdded.append(namePdf)
        
        line="\\begin{figure}[!ht]\n";self.lines = self.lines + line 
        line="\\begin{center}\n";self.lines = self.lines + line 
        line="\\includegraphics[width=1\\textwidth]{%s/%s}\n" % (utils.filterPath(self.outputPath),namePdf);self.lines = self.lines + line
        line="\\caption{%s}\n"%caption;self.lines = self.lines + line 
        line="\\label{%s}\n"%label;self.lines = self.lines + line 
        line="\\end{center}\n";self.lines = self.lines + line 
        line="\\end{figure}\n";self.lines = self.lines + line
        
    def addTable(self,_caption,_sizeBox,_names,_units,_label,_linesResults,useFormula=False,addCaptionLines=False):


        line="\\begin{table}[!ht]\n" ; self.lines = self.lines + line

        line="\\begin{small}\n" ; self.lines = self.lines + line 
        line="\\caption{%s}\n" % _caption ; self.lines = self.lines + line 
        line="\\begin{center}\n" ; self.lines = self.lines + line 
        if(_sizeBox != None):
            line="\\resizebox{%dcm}{!} \n" % _sizeBox;self.lines = self.lines + line 
        line="{\n" ;self.lines = self.lines + line 
        
        line="\\begin{tabular}{l | "; self.lines = self.lines + line 
        
            
        for i in range(len(_names)-1):
             line = "c "; self.lines = self.lines + line 
                 
        line = "} \n" ; self.lines = self.lines + line 
        line="\\hline\n" ; self.lines = self.lines + line 
        line="\\hline\n" ; self.lines = self.lines + line 

        if(addCaptionLines != False):
            self.lines = self.lines + addCaptionLines
            line="\\hline\n" ; self.lines = self.lines + line

        for i in range(len(_names)):

            if(useFormula):
                 _names[i] = "$%s$" % _names[i]

            if(i==len(_names)-1):
                line = "%s " % _names[i]; self.lines = self.lines + line
            else:
                line = "%s &" % _names[i]; self.lines = self.lines + line
                
        line = "\\\\ \n"; self.lines = self.lines + line

        if(_units != None):
            if(len(_units) == len(_names)):
                for i in range(len(_units)):
                    if (useFormula):
                        _units[i] = "$%s$" % _units[i]

                    if(i==len(_units)-1):
                        line = "%s" % _units[i]; self.lines = self.lines + line
                    else:
                        line = "%s &" % _units[i]; self.lines = self.lines + line
            else:
                print ("Units size differ from names, so we use the first one for all")

                for i in range(len(_names)):
                    if(i==0):
                        line = "&" #first columns I assume no unit
                    else:
                        if (useFormula):
                            line = "$%s$" % _units[0];
                        else:
                            line = "%s" % _units[0];

                        if (not i == len(_names) - 1):
                            line = line + " &"

                    self.lines = self.lines + line


            line = "\\\\ \n"; self.lines = self.lines + line

        line="\\hline\n" ; self.lines = self.lines + line 
        
        self.lines = self.lines + _linesResults
        
            
        line="\\hline\n" ; self.lines = self.lines + line 
        line="\\hline\n" ; self.lines = self.lines + line
        line ="\\end{tabular}\n";self.lines = self.lines + line
        line="}\n" ; self.lines = self.lines + line 
        line="\\label{%s}\n" % _label; self.lines = self.lines + line 
        line="\\end{center}\n" ; self.lines = self.lines + line 
        line="\\end{small}\n" ; self.lines = self.lines + line
        line="\\end{table}\n" ; self.lines = self.lines + line

    def addPandasTable(self, _caption, _sizeBox, _units, _label, _pandasTable, useFormula=False,
                 addCaptionLines=False):

        line = "\\begin{table}[!ht]\n";
        self.lines = self.lines + line

        line = "\\begin{small}\n";
        self.lines = self.lines + line
        line = "\\caption{%s}\n" % _caption;
        self.lines = self.lines + line
        line = "\\begin{center}\n";
        self.lines = self.lines + line
        if (_sizeBox != None):
            line = "\\resizebox{%dcm}{!} \n" % _sizeBox;
            self.lines = self.lines + line
        line = "{\n";
        self.lines = self.lines + line

        self.lines = self.lines + _pandasTable

        line = "}\n";
        self.lines = self.lines + line
        line = "\\label{%s}\n" % _label;
        self.lines = self.lines + line
        line = "\\end{center}\n";
        self.lines = self.lines + line
        line = "\\end{small}\n";
        self.lines = self.lines + line
        line = "\\end{table}\n";
        self.lines = self.lines + line


    def addLongTable(self,_caption, _sizeBox, _names, _units, _label, _linesResults, useFormula=False,
                     addCaptionLines=False,lenghName=0.47,lenghRest=0.05):

        line = "\\begin{tiny}\n";
        self.lines = self.lines + line

        line = "\\begin{longtable}{";
        self.lines = self.lines + line

        for i in range(len(_names)):
            if(i==0):
                line = " p{%.2f\\textwidth}"%lenghName;
            else:
                line = " | p{%.2f\\textwidth}"%lenghRest;
            self.lines = self.lines + line
        line = "} \n";
        self.lines = self.lines + line


        line = "\\hline\n";
        self.lines = self.lines + line

        if (addCaptionLines != False):
            self.lines = self.lines + addCaptionLines
            line = "\\hline\n";
            self.lines = self.lines + line

        for i in range(len(_names)):

            if (useFormula):
                _names[i] = "$%s$" % _names[i]

            if (i == len(_names) - 1):
                line = "%s " % _names[i];
                self.lines = self.lines + line
            else:
                line = "%s &" % _names[i];
                self.lines = self.lines + line

        line = "\\\\ \n";
        self.lines = self.lines + line

        line = "\\hline\n";
        self.lines = self.lines + line

        if (_units != None):
            if (len(_units) == len(_names)):
                for i in range(len(_units)):
                    if (useFormula):
                        _units[i] = "$%s$" % _units[i]

                    if (i == len(_units) - 1):
                        line = "%s" % _units[i];
                        self.lines = self.lines + line
                    else:
                        line = "%s &" % _units[i];
                        self.lines = self.lines + line
            else:
                print ("Units size differ from names, so we use the first one for all")

                for i in range(len(_names)):
                    if (i == 0):
                        line = "&"  # first columns I assume no unit
                    else:
                        if (useFormula):
                            line = "$%s$" % _units[0];
                        else:
                            line = "%s" % _units[0];

                        if (not i == len(_names) - 1):
                            line = line + " &"

                    self.lines = self.lines + line

            line = "\\\\ \n";
            self.lines = self.lines + line

        line = "\\hline\n";
        self.lines = self.lines + line

        ################ RESULTS #######################

        self.lines = self.lines + _linesResults

        line = "\\hline\n";
        self.lines = self.lines + line

        line = "\\caption{%s}\n" % _caption;
        self.lines = self.lines + line

        line = "\\label{%s}\n" % _label;
        self.lines = self.lines + line
        line = "\\end{longtable}\n";
        self.lines = self.lines + line
        line = "\\end{tiny}\n";
        self.lines = self.lines + line

    def addTableMonthly(self,var,names,_units,caption,label,begin=0,nMonth=12,addLines=False,sizeBox=None):
                    
        if(len(names) != len(_units)): 
            units= []
            for i in range(len(names)):
                if(i==0):
                    units.append("") #motnh
                else:
                    units.append(_units)
                    
        lines = ""        
        
        for n in range(begin,begin+nMonth):                    
            line = "%s"%utils.getMonthKey(n+1);lines=lines+line                     
            for i in range(len(var)):
                line = "&%.1f"%var[i][n];lines = lines + line
            line="\\\\ \n";lines = lines + line            
            
        line="\\hline\n" ; lines = lines + line                          
        
        if(len(var[0])<=12):
            for i in range(len(var)):
                line = "&%.1f"%sum(var[i]);lines = lines + line
            line="\\\\ \n";lines = lines + line            
        else: 
            if(var[0]!=13):
                raise ValueError("size should be either either below 12 or 13.")
                
            for i in range(len(var)):
                line = "&%.1f"%var[i][12];lines = lines + line
            line="\\\\ \n";lines = lines + line            

        if(addLines!=False):
            lines=lines+addLines

        self.addTable(caption,sizeBox,names,units,label,lines,useFormula=False)
   
        return lines
       