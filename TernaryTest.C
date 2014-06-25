#include "TernaryPlot.C"

void TernaryTest()
{
  int nbins = 20;
  TernaryPlot test(nbins);
  test.axis1.SetTitle("variable 1");
  test.axis2.SetTitle("variable 2");
  test.axis3.SetTitle("variable 3");
  test.zaxis.SetTitle("number of points");
  for(int i2 = 0;i2<nbins;i2++){
    double val2 = (0.5 + i2)/nbins;
    double y = val2*test.sin60;
    for(int i1 = 1;i1<nbins*2;i1++){
      double x = 1.*i1/nbins/2;
      double val1 = x - y/test.sin60*test.cos60;
      double val3 = 1.-val1-val2;
      if(val3 >0 && val1 > 0){
	test.Fill(val1,val2,val3,val1);
      }
    }
  }
  test.DrawAndPrint("test.pdf");
}
