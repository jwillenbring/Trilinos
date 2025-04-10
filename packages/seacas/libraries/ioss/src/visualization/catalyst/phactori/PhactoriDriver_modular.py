# Copyright(C) 1999-2020, 2024 National Technology & Engineering Solutions
# of Sandia, LLC (NTESS).  Under the terms of Contract DE-NA0003525 with
# NTESS, the U.S. Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
#     * Neither the name of NTESS nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

try: paraview.simple
except: from paraview.simple import *

from paraview import coprocessing

# ----------------------- Pipeline definition -----------------------

from phactori import *

#do sierra/catalyst logging (from process id 0 only)
#note: logging should be disabled for testing, but enabled for production
if SmartGetLocalProcessId() == 0:
  import os
  import datetime

  loggingIsEnabled = True
  if "SNL_CATALYST_SIERRA_USAGE_LOG_FLAG" in os.environ:
    #print "SNL_CATALYST_SIERRA_USAGE_LOG_FLAG environment variable: " + \
            #os.environ["SNL_CATALYST_SIERRA_USAGE_LOG_FLAG"]
    if os.environ["SNL_CATALYST_SIERRA_USAGE_LOG_FLAG"] == "disable":
      loggingIsEnabled = False

  if loggingIsEnabled:
    #print "I am process 0 doing logging!"
    if "HOSTNAME" in os.environ:
      os.environ["LOG_PLATFORM"] = os.environ["HOSTNAME"]
    else:
      os.environ["LOG_PLATFORM"] = "HOSTNAMEnotset"
    os.environ["LOG_PRODUCT"] = "sierra-catalyst"
    os.environ["CATALYST_VERSION"] = "p4.1.0-s4.31.6-p"
    nowdate = datetime.datetime.now()
    #os.environ["DATE"] = str(nowdate.month) + "/" + str(nowdate.day) + "/" + str(nowdate.year)
    #currently, DATE environment variable is overwritten in logParserScr script
    #print "date is :  " + os.environ["DATE"]
    import subprocess
    try:
      subprocess.call("/projects/viz/catalyst/utilities/logParserScr")
    except:
      print("usage logging warning: logParserScr call failed\n")

    #print "platform: " + os.environ["LOG_PLATFORM"]
    #print "product:  " + os.environ["LOG_PRODUCT"]
    #print "version:  " + os.environ["CATALYST_VERSION"]
    #print "date:     ->" + os.environ["DATE"] + "<-"
    #print "I am process 0 done logging!"
  #else:
    #print "I am process 0, logging disabled in environment variable"

#def UseViewMapB(inViewMapB):
#  PhactoriScript.UseViewMapB_ps(inViewMapB)

#def UseDataSetupMapB(inDataSetupMapB):
#  PhactoriScript.UseDataSetupMapB_ps(inDataSetupMapB)

global gMyInitialUpdateFrequencies
gMyInitialUpdateFrequencies = {}

def CreateCoProcessor():
  def _CreatePipeline(coprocessor, datadescription):
    class Pipeline:
      dummyItem = "blah"
      #global cp_views, cp_writers

      #print "CreatePipeline startup"
      #print "cp_views len is " + str(len(cp_views))

      #rigid_body_impact_6_ff_e = coprocessor.CreateProducer( datadescription, "input" )

      #SetUpCoProcessor(coprocessor)
      #SetCpViewsAndCpWriters(cp_views, cp_writers)

#QQQQQ->we want to do this and CreateProducer once for each output results block,
#reuse same coprocesor instance (?), then have LocalWriteImages3 only do the images for a given output results bloxk:q

      #PhactoriScript.CreatePipeline(datadescription)

    return Pipeline()

  class CoProcessor(coprocessing.CoProcessor):
    def CreatePipeline(self, datadescription):
      self.Pipeline = _CreatePipeline(self, datadescription)

    def LocalWriteImages3(self, datadescription, rescale_lookuptable=False):
      WriteImagesForCurrentPipeAndViewsState(datadescription)

    def LocalExportOperationsData3(self, datadescription, rescale_lookuptable=False):
      ExportOperationsDataForCurrentPipeAndViewsState(datadescription)

    def SetInitialUpdateFrequences(self, datadescription):
      global gMyInitialUpdateFrequencies
      freqsChanged = False
      numInputGrids = datadescription.GetNumberOfInputDescriptions()
      for ii in range(0,numInputGrids):
        oneGridName = datadescription.GetInputDescriptionName(ii)
        if PhactoriDbg():
          myDebugPrint3("SetInitialUpdateFrequences " + str(ii) + " " + str(oneGridName) + "\n")
        if oneGridName not in gMyInitialUpdateFrequencies:
          gMyInitialUpdateFrequencies[oneGridName] = [1]
          freqsChanged = True
      if PhactoriDbg():
        if freqsChanged:
          myDebugPrint3("gMyInitialUpdateFrequencies changed:\n")
        else:
          myDebugPrint3("gMyInitialUpdateFrequencies not changed:\n")
        myDebugPrint3(str(gMyInitialUpdateFrequencies) + "\n")
      if freqsChanged:
        self.SetUpdateFrequencies(gMyInitialUpdateFrequencies)

  coprocessor = CoProcessor()
  #freqs = {'input': [1]}
  #coprocessor.SetUpdateFrequencies(freqs)
  return coprocessor


#--------------------------------------------------------------
# Global variables that will hold the pipeline for each timestep
# Creating the CoProcessor object, doesn't actually create the ParaView pipeline.
# It will be automatically setup when coprocessor.UpdateProducers() is called the
# first time.
#coprocessor = CreateCoProcessor()
coprocessor = None

#--------------------------------------------------------------
# Enable Live-Visualizaton with ParaView
#coprocessor.EnableLiveVisualization(False)

global gDoNewScatterPlotsC
gDoNewScatterPlotsC = True
#gDoNewScatterPlotsC = False

def PerFrameUpdate(datadescription):
  PerRendersetInitialization(datadescription)
  UpdateAllOperationsWhichMayChangeWithData()
  UpdateAllImagesetViewsWhichMayChangeWithData()

  #we are now updating color range stuff right before WriteImage
  #UpdateDataRangesForColorValues()

  myDebugPrint3('PerFrameUpdate entered\n')
  #GetAndReduceViewControl()
  global tearListPersistent
  global deathListPersistent

  global gDoNewScatterPlotsC
  if gDoNewScatterPlotsC:
    myDebugPrint3('doing UpdateAllScatterPlots (C)\n')
    UpdateAllScatterPlots()
    myDebugPrint3('doing UpdateAllPlotsOverTime\n')
    UpdateAllPlotsOverTime()
    myDebugPrint3('did plot updates\n')

  #currentFrameTearList = CollectCells1('TEAR_DOUBLE', 0.01, 1)
  #tearListPersistent = mergeCurrentIntoPersistent(tearListPersistent,
  #                       currentFrameTearList)
  #currentFrameDeathList = CollectCells1('STATUS', 0.8, -1)
  #deathListPersistent = mergeCurrentIntoPersistent(deathListPersistent,
  #                        currentFrameDeathList)
  #compareTearDeath(tearListPersistent, deathListPersistent)

  myDebugPrint3('PerFrameUpdate exiting\n')


#begin tear/death persistence; not used now but may be useful later
global tearListPersistent
tearListPersistent = []
global deathListPersistent
deathListPersistent = []

def mergeCipCompare(item1, item2):
  if item1[1] > item2[1]:
   return 1
  if item1[1] < item2[1]:
   return -1
  if item1[2] > item2[2]:
   return 1
  if item1[2] < item2[2]:
   return -1
  return 0

def mergeCurrentIntoPersistent(pList, cList):
  myDebugPrint2('mergeCurrentIntoPersistent entered\n')
  pListLen = len(pList)
  cListLen = len(cList)
  myDebugPrint2('  pList has ' + str(pListLen) + ' elements, cList has ' + str(cListLen) + ' elements\n')
  pIndex = 0
  cIndex = 0
  mergeList = []
  while (pIndex < pListLen) or (cIndex < cListLen):
    if(pIndex >= pListLen):
      mergeList.append(cList[cIndex])
      #myDebugPrint2('  pIndex ' + str(pIndex) + ' cIndex ' + str(cIndex) + '\n')
      #myDebugPrint2('  (p ended) [cIndex] ' + str(cList[cIndex]) + '\n')
      cIndex += 1
      continue
    if(cIndex >= cListLen):
      mergeList.append(pList[pIndex])
      #myDebugPrint2('  pIndex ' + str(pIndex) + ' cIndex ' + str(cIndex) + '\n')
      #myDebugPrint2('  (c ended) [pIndex] ' + str(cList[pIndex]) + '\n')
      pIndex += 1
      continue
    compareResult = mergeCipCompare(cList[cIndex], pList[pIndex])
    #myDebugPrint2('  pIndex ' + str(pIndex) + ' cIndex ' + str(cIndex) + '\n')
    #myDebugPrint2('  [pIndex] ' + str(pList[pIndex]) + ' [cIndex] ' + str(cList[cIndex]) + '\n')
    if compareResult == 1:
      #myDebugPrint2('  item from pList is less\n')
      mergeList.append(pList[pIndex])
      pIndex += 1
    if compareResult == -1:
      #myDebugPrint2('  item from cList is less\n')
      mergeList.append(cList[cIndex])
      cIndex += 1
    if compareResult == 0:
      #myDebugPrint2('  items from cList and pList are same element\n')
      mergeList.append(pList[pIndex])
      pIndex += 1
      cIndex += 1
  myDebugPrint2('  merged list has ' + str(len(mergeList)) + ' elements\n')
  myDebugPrint2('mergeCurrentIntoPersistent returning\n')
  return mergeList

def compareTearDeath(tList, dList):
  myDebugPrint2('compareTearDeath entered\n')
  myDebugPrint2('compareTearDeath returning\n')
#end tear/death persistence; not used now but may be useful later


# ---------------------- Data Selection method ----------------------

global gFirstTimeInDoCoProcessing
gFirstTimeInDoCoProcessing = True
global gSkipCountdown
#gSkipCountdown = 3
gSkipCountdown = 0

global gCatchAllExceptionsAndPassUpFlag
gCatchAllExceptionsAndPassUpFlag = True
#gCatchAllExceptionsAndPassUpFlag = False

def RequestDataDescription(datadescription):
  myDebugPrint3("PhactoriDriver.RequestDataDescription entered: " + str(gDoCoProcessingCount)+ "\n");
  if PhactoriDbg():
    numInputGrids = datadescription.GetNumberOfInputDescriptions()
    for ii in range(0,numInputGrids):
      oneGridName = datadescription.GetInputDescriptionName(ii)
      myDebugPrint3("RequestDataDescription " + str(ii) + " " + str(oneGridName) + "\n")

  TestUserDataForBypassScript(datadescription)

  if GetBypassUserDataFlag() == False:
    fd = datadescription.GetUserData()

    if fd == None:
      myDebugPrint2("no user data, returning {}\n")
      returnViewMapC = {}
      return returnViewMapC

  global gCatchAllExceptionsAndPassUpFlag
  if gCatchAllExceptionsAndPassUpFlag:
    try:
      return RequestDataDescriptionSub(datadescription)
    except:
      import traceback
      tb = traceback.format_exc()
      IssueErrorOrWarningThroughSierraIO(datadescription, tb, True)
  else:
    return RequestDataDescriptionSub(datadescription)

def RequestDataDescriptionSub(datadescription):
    myDebugPrint("PhactoriDriver.RequestDataDescriptionSub entered\n");
    "Callback to populate the request for current timestep"

    TestUserDataForBypassScript(datadescription)

    if GetBypassUserDataFlag() == False:
      fd = datadescription.GetUserData()

      if fd == None:
        myDebugPrint2("no user data, returning {}\n")
        returnViewMapC = {}
        return returnViewMapC

    global coprocessor

    global gFirstTimeInDoCoProcessing
    global gSkipCountdown

    if gFirstTimeInDoCoProcessing == True:
      myDebugPrint2("RequestDataDescription doing gFirstTimeInDoCoProcessing\n")
      myDebugPrint2(" skip countdown is " + str(gSkipCountdown) + "\n")
      if gSkipCountdown > 0:
        gSkipCountdown = gSkipCountdown - 1
        return 0
      coprocessor = CreateCoProcessor()
      coprocessor.SetInitialUpdateFrequences(datadescription)
      coprocessor.EnableLiveVisualization(False)
      gFirstTimeInDoCoProcessing = False
    else:
      coprocessor.SetInitialUpdateFrequences(datadescription)

    #import pdb
    #pdb.set_trace()

    InitializePerPipeRoot(datadescription, coprocessor)

    if datadescription.GetForceOutput() == True:
        # We are just going to request all fields and meshes from the simulation
        # code/adaptor.
        for i in range(datadescription.GetNumberOfInputDescriptions()):
            datadescription.GetInputDescription(i).AllFieldsOn()
            datadescription.GetInputDescription(i).GenerateMeshOn()
        return 1

    # setup requests for all inputs based on the requirements of the
    # pipeline.
    coprocessor.LoadRequestedData(datadescription)
    return 1




# ------------------------ Processing method ------------------------

global tripleBufferCount
tripleBufferCount = 0

global gDoCoProcessingCount
gDoCoProcessingCount = 0

def DoCoProcessing(datadescription):
  myDebugPrint3("PhactoriDriver.DoCoProcessing entered: " + str(gDoCoProcessingCount)+ "\n");
  if PhactoriDbg():
    numInputGrids = datadescription.GetNumberOfInputDescriptions()
    for ii in range(0,numInputGrids):
      oneGridName = datadescription.GetInputDescriptionName(ii)
      myDebugPrint3("DoCoProcessing " + str(ii) + " " + str(oneGridName) + "\n")


  fd = datadescription.GetUserData()

  if GetBypassUserDataFlag() == False:
    if fd == None:
      myDebugPrint2("no user data, returning {}\n")
      returnViewMapC = {}
      return returnViewMapC

  global gCatchAllExceptionsAndPassUpFlag
  if gCatchAllExceptionsAndPassUpFlag:
    try:
      DoCoProcessingSub(datadescription)
    except:
      import traceback
      tb = traceback.format_exc()
      IssueErrorOrWarningThroughSierraIO(datadescription, tb, True)
  else:
    DoCoProcessingSub(datadescription)

def DoCoProcessingSub(datadescription):
    "Callback to do co-processing for current timestep"

    global gDoCoProcessingCount
    myDebugPrint3("PhactoriDriver.DoCoProcessingSub entered: " + str(gDoCoProcessingCount)+ "\n");

    gDoCoProcessingCount += 1


    fd = datadescription.GetUserData()

    if GetBypassUserDataFlag() == False:
      if fd == None:
        myDebugPrint2("no user data, returning {}\n")
        returnViewMapC = {}
        return returnViewMapC

    global coprocessor
    global gFirstTimeInDoCoProcessing
    global gSkipCountdown

    if gFirstTimeInDoCoProcessing == True:
      myDebugPrint2("DoCoProcessing doing gFirstTimeInDoCoProcessing\n")
      myDebugPrint2(" skip countdown is " + str(gSkipCountdown) + "\n")
      if gSkipCountdown > 0:
        return
      coprocessor = CreateCoProcessor()
      coprocessor.SetInitialUpdateFrequences(datadescription)
      coprocessor.EnableLiveVisualization(False)
      gFirstTimeInDoCoProcessing = False
    else:
      coprocessor.SetInitialUpdateFrequences(datadescription)

    #import pdb
    #pdb.set_trace()

    InitializePerPipeRoot(datadescription, coprocessor)

    "Callback to do co-processing for current timestep"
    timestep = datadescription.GetTimeStep()

    myDebugPrint("timestep is: " + str(timestep) + "\n");

    SmartGetLocalProcessId()

    # Load the Pipeline if not created yet
    #if not pipeline:
    #   myDebugPrint("PhactoriDriver.DoCoProcessing creating pipeline\n");
    #   pipeline = CreatePipeline(datadescription)
    #else:
    #   myDebugPrint("PhactoriDriver.DoCoProcessing updating pipeline\n");
    #   # update to the new input and time
    #   UpdateProducers(datadescription)
    #   PerFrameUpdate(datadescription)


    # Update the coprocessor by providing it the newly generated simulation data.
    # If the pipeline hasn't been setup yet, this will setup the pipeline.
    coprocessor.UpdateProducers(datadescription)

    PerFrameUpdate(datadescription)

    # check for simulation-data-based i/o filtering--skip image creation
    # and writing if criteria has been set up to determine whether to
    # create images, such as 'maximum of variable X above 80.0'
    result = WriteOutImagesTest(datadescription, coprocessor)
    if result == False:
      #don't write images
      return

    # Write output data, if appropriate.
    #coprocessor.WriteData(datadescription);

    # Write output data
    #WriteAllData(datadescription, cp_writers, timestep);

    # Write image capture (Last arg: rescale lookup table)
    #myDebugPrint("PhactoriDriver.DoCoProcessing writing images\n");
    #LocalWriteAllImages(datadescription, cp_views, timestep, False)
    #WriteAllImages(datadescription, cp_views, timestep, False)

    # Live Visualization
    #if (len(cp_views) == 0) and live_visu_active:
    #   DoLiveInsitu(timestep, pv_host, pv_port)

    # Write output data, if appropriate.
    coprocessor.WriteData(datadescription)

    coprocessor.LocalExportOperationsData3(datadescription)

    # Write image capture (Last arg: rescale lookup table), if appropriate.
    coprocessor.LocalWriteImages3(datadescription,
        rescale_lookuptable=False)

    #test and allow for looping when doing user vis interaction while
    #pausing simulation
    continueWriteAndInteractionCheckLoop = True
    while continueWriteAndInteractionCheckLoop:
      interactionTestResult = \
          DoUserInteractionWithSimulationPausedIfEnabled()
      if interactionTestResult == 0:
        #looping interaction is not or is no longer on; allow simulation to
        #continue
        continueWriteAndInteractionCheckLoop = False
      elif interactionTestResult == 1:
        #looping interaction is on, but there were no changes to the vis
        #(i.e. no trigger was given to update vis).  Therefore do not write
        #images, but continue looping and waiting for vis change trigger
        continueWriteAndInteractionCheckLoop = True
      elif interactionTestResult == 2:
        #there was a vis change triggered; update the images for the new
        #vis, write out the images, and continue looping
        continueWriteAndInteractionCheckLoop = True
        imagesNeedWriting = True
        if imagesNeedWriting:
          UpdateAllImagesetViewsWhichMayChangeWithData()
          coprocessor.LocalExportOperationsData3(datadescription)
          coprocessor.LocalWriteImages3(datadescription,
          rescale_lookuptable=False)

    #coprocessor.WriteImages(datadescription, rescale_lookuptable=True)

    # Live Visualization, if enabled.
    coprocessor.DoLiveVisualization(datadescription, "localhost", 22222)

