#!/usr/bin/env python

import os,sys

# load root in batch mode (w/o graphical interface)
sys.argv.append("-b")
import ROOT as rt

# load histogram class
rt.gROOT.ProcessLine(".L " + os.environ["HOME"] + "/anascripts/TernaryPlot.C+")   # change path to your needs

# test
nbins = 40
tern = rt.TernaryPlot(nbins)
tern.axis1.SetTitle("variabel1")
tern.axis2.SetTitle("variabel2")
tern.axis3.SetTitle("variabel3")
tern.zaxis.SetTitle("number of points")

val1 = 1.
val2 = 0.
val3 = 0.
val4 = 1.
tern.Fill(val1,val2,val3,1)

val1 = 0.
val2 = 1.
val3 = 0.
val4 = 1.
tern.Fill(val1,val2,val3,2)

val1 = 0.
val2 = 0.
val3 = 1.
val4 = 1.
tern.Fill(val1,val2,val3,3)

tern.DrawAndPrint("test3.pdf")

