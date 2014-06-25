#!/usr/bin/env python

import os

import ROOT as rt
rt.gROOT.ProcessLine(".L " + os.environ["HOME"] + "/anascripts/TernaryPlot.C+")   # change path to your needs

nbins = 40
tern = rt.TernaryPlot(nbins)
tern.axis1.SetTitle("variabel1")
tern.axis2.SetTitle("variabel2")
tern.axis3.SetTitle("variabel3")
tern.zaxis.SetTitle("number of points")
for i2 in range(0,nbins):
    val2 = (0.5 + i2)/nbins;
    y = val2*tern.sin60
    for i1 in range(1,nbins*2):
      x = 1.*i1/nbins/2
      val1 = x - y/tern.sin60*tern.cos60
      val3 = 1.-val1-val2
      if val3 >0 and val1 > 0:
	tern.Fill(val1,val2,val3,val1)
tern.DrawAndPrint("test.pdf")

