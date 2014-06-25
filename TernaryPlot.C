#include "vector"
#include "iostream"
#include "algorithm"

#include "TGraph2D.h"
#include "TCanvas.h"
#include "TMath.h"
#include "TGaxis.h"
#include "TPolyLine.h"
#include "TStyle.h"
#include "TColor.h"

class TernaryPlot{

public:

  TernaryPlot(size_t nbins);
  ~TernaryPlot(){};

  void Fill(double v1,double v2,double v3,double w=1);
  void DrawAndPrint(string filepath);

  TGaxis axis1;
  TGaxis axis2;
  TGaxis axis3;
  TGaxis zaxis;

  double sin60;
  double cos60;
  
private:
  
  size_t nbins_;
  double binwidth_;
  vector<vector<double> > bincontent_;
  
};

TernaryPlot::TernaryPlot(size_t nbins)
{
  nbins_ = nbins;
  binwidth_ = 1./nbins;
  for(size_t row = 0;row<nbins_;row++){
    bincontent_.push_back(vector<double>(2*(nbins_-row)-1,0.));
  }
  sin60 = TMath::Sqrt(3.)/2.;
  cos60 = TMath::Sqrt(1.-sin60*sin60);

  axis1 = TGaxis(0., 0., 1., 0., 0., 1.,510,"-");
  axis1.SetLabelOffset(-0.08);
  axis1.SetTitleOffset(-1.8);
  axis1.CenterTitle();

  axis2 = TGaxis(1., 0., 0.5, sin60, 0., 1.,510,"-");
  axis2.SetLabelOffset(-0.08);
  axis2.SetTitleOffset(-2.2);
  axis2.CenterTitle();

  axis3 = TGaxis(0.5, sin60, 0., 0., 0., 1.,510,"-");
  axis3.SetLabelOffset(-0.08);
  axis3.SetTitleOffset(-2.2);
  axis3.CenterTitle();

  zaxis = TGaxis(1.25,0.0,1.25,sin60,0,1,510,"+"); // final values set while drawing
  zaxis.SetLabelOffset(0.06);
  zaxis.SetTitleOffset(1.2);
  zaxis.CenterTitle();

}

void TernaryPlot::Fill(double v1,double v2,double v3,double w){
  // normalize
  double tot = v1+v2+v3;
  if(v1 < 0 || v2 < 0 || v3 < 0){
    cout << "ERROR in TernaryPlot::Fill : non of given values should be smaller than 1" << endl;
    exit(1);
  }
  if(tot == 0){
    cout << "ERROR in TernaryPlot::Fill : sum of given values should not equal 0" << endl;
    exit(1);
  }
  v1/=tot;
  v2/=tot;
  // get row and col numbers
  size_t row = v2/binwidth_;
  size_t col = v1/binwidth_; // refine later
  // get x and y coordinates
  double y = v2*sin60;                    // global
  double x = v1 + y*cos60/sin60;          // global
  // in upward or downward pointing triangle?
  double xlimit = binwidth_*row/2 + binwidth_*(1+col) - (y-binwidth_*sin60*row)/sin60*cos60;
  col *= 2;
  if(x > xlimit)
    col+=1;
  // add weight
  bincontent_[row][col]+=w;
}

void TernaryPlot::DrawAndPrint(string filepath){

    
  // define triangular bins
  vector<vector<TPolyLine> > triangles;
  double _x[5]; // 5 because we re-use for rectangles (see further)
  double _y[5];
  for(size_t row = 0;row < nbins_;++row){
    triangles.push_back(vector<TPolyLine>());
    for(size_t col = 0;col< nbins_-row;++col){
      // triangle pointing up
      _x[0] = 1./nbins_*(0.5*row + col);
      _y[0] = sin60/nbins_*row;
      _x[1] = _x[0] + 1./nbins_;
      _y[1] = _y[0];
      _x[2] = _x[0] + 0.5/nbins_;
      _y[2] = _y[0] + sin60/nbins_;
      _x[3] = _x[0];
      _y[3] = _y[0];
      triangles[row].push_back(TPolyLine(4,_x,_y));
      // triangle pointing down
      if(col<nbins_-row-1){
	triangles[row].push_back(TPolyLine(triangles[row].back()));
	for(int i = 0;i<4;i++){
	  // half a step to the left
	  triangles[row].back().GetX()[i] += binwidth_/2;
	  // one step up
	  triangles[row].back().GetY()[i] += binwidth_*sin60;
	}
	// and make it point down
	triangles[row].back().GetY()[2] -= 2*binwidth_*sin60;
      }
    }
  }

  // canvas
  //TCanvas *cnv = new TCanvas("cnv", "Ternary plot", 800, 800*sin60);
  TCanvas *cnv = new TCanvas("cnv", "Ternary plot", 600*1.15, 600*sin60);
  cnv->Range(-0.2,-0.2*sin60,1.2+1.4*0.15,1.2*sin60);
  //cnv->Range(-margin, -margin*sin60,1.+margin, sin60*(1.+margin));
  
  // get max,min bincontent
  double _max = bincontent_[0][0];
  double _min = bincontent_[0][0];
  for(size_t row = 0;row<triangles.size();row++){
    _max = max(_max,*max_element(bincontent_[row].begin(),bincontent_[row].end()));
    _min = min(_min,*min_element(bincontent_[row].begin(),bincontent_[row].end()));
  }
  if(_min == _max){
    _max += 1.;
  }
  
  // set triangle colors and draw
  int ncolors = TColor::GetNumberOfColors();
  for(size_t row = 0;row<triangles.size();row++){
    for(size_t col = 0;col<triangles[row].size();col++){
      int _color = max(0.,(bincontent_[row][col] - _min)/(_max - _min)*(ncolors-1));
      triangles[row][col].SetFillColor(gStyle->GetColorPalette(_color));
      triangles[row][col].SetLineWidth(1);
      triangles[row][col].Draw("f");
    }
  }

  // draw axes
  axis1.Draw();
  axis2.Draw();
  axis3.Draw();

  // colred z-axis
  zaxis.SetWmin(_min);
  zaxis.SetWmax(_max);
  vector<TPolyLine> rectangles;
  for(int c = 0;c<ncolors;c++){
    _x[0] = zaxis.GetX1() - 0.1;
    _x[1] = _x[0] + 0.1;
    _x[2] = _x[1];
    _x[3] = _x[0];
    _x[4] = _x[0];
    _y[0] = sin60/ncolors*c;
    _y[1] = _y[0];
    _y[2] = _y[0] + sin60/ncolors;
    _y[3] = _y[2]; 
    _y[4] = _y[0];
    rectangles.push_back(TPolyLine(5,_x,_y));
    rectangles[c].SetFillColor(gStyle->GetColorPalette(c));
  }
  // for one reason or another,
  // drawing only works outside the previous loop
  for(int c= 0;c<ncolors;c++)
    rectangles[c].Draw("f");
  zaxis.Draw();

  // und print
  gPad->Print(filepath.c_str());

}
