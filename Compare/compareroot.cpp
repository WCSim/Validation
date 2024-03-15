#include "TFile.h"
#include "TTree.h"
#include "TLeaf.h"
#include "TObject.h"
#include "TCanvas.h"
#include "TH1F.h"
#include "TPaveStats.h"

#include <iostream>
#include <fstream>

using namespace std;

/*
  argv[1]: path to webpage directory
  argv[2]: path to new file with TTree(s) to compare with the reference
  argv[3]: path to reference file with TTree(s)
 */

int main(int argc,char *argv[]){
  char buff[256];
  

  ofstream index;
  ofstream content;
  ofstream menu;
  ofstream title;

  sprintf(buff,"%s/index.html",argv[1]);
  index.open(buff);
  sprintf(buff,"%s/content.html",argv[1]);
  content.open(buff);
  sprintf(buff,"%s/menu.html",argv[1]);
  menu.open(buff);
  sprintf(buff,"%s/title.html",argv[1]);
  title.open(buff);


  index<<"<!doctype html><html><head><title>Index Page</title></head><frameset rows=\"15%,*\"><frame name=\"title\" src=\"title.html\"scrolling=\"no\" noresize><frameset cols=\"18%,*\"><frame name=\"menu\" src=\"menu.html\"scrolling=\"auto\" noresize><frame name=\"content\" src=\"content.html\"scrolling=\"yes\" noresize></frameset><body></body></html>" ;
  index.close();

  menu<<"<!doctype html><html><head><base target=\"content\"></head><body>";

  title<<"<!doctype html><html><head></head><body><H3><b><u>"<<argv[2]<<" Plots</u></b></H3><p>Red line/marker is from the reference in WCSim/Validation. Dark blue line is from the current code run. It is possible for the dark blue to be completely hidden<p></body></html>";
  title.close();

  content<<"<!doctype html><html><head></head><body><H1><------Click a link in the menu on the left to see the plot.</H1></body></html>";
  content.close();
 
  bool fullsame=true;
  sprintf(buff,"%s/Plots.root",argv[1]);
  TFile Plots(buff,"RECREATE");
  TFile file(argv[2]);
  TFile file2(argv[3]);
  
  TTree* tree=0;
  TTree *tree2;
  TList* tl = file.GetListOfKeys();
  TIter itr(tl);
  
  
  for(itr.Begin();itr!=TIter::End();++itr){
    if( (tree = (TTree*)file.GetObjectChecked((*itr)->GetName(),"TTree")) && (tree2 = (TTree*)file2.GetObjectChecked((*itr)->GetName(),"TTree")) ){
      
      
      
      //TTree *tree=(TTree*)file.Get("EventTree");
      
      //  TTree *tree2=(TTree*)file.Get("EventTree");
      
      
      
      
      TIterator* i = tree->GetIteratorOnAllLeaves();
      TObject* obj=0;
      while( (obj=i->Next()) ){
	cout << obj->GetName() << endl;
	bool same=true;
	
	TLeaf *leaf=(TLeaf*)obj;
	TLeaf *leaf2=tree2->GetLeaf(obj->GetName());
	
	long entries1=tree->GetEntriesFast();
	long entries2=tree2->GetEntriesFast();
	
	//First check if there's a difference on this leaf
	int branch_type = -1;
	bool found_non_empty_vector = false;
	if (entries1==entries2){
	  for (long i=0;i<entries1;i++){
	    leaf->GetBranch()->GetEntry(i);
	    leaf2->GetBranch()->GetEntry(i);
	    TString type1(leaf ->GetTypeName());
	    TString type2(leaf2->GetTypeName());
	    //special cases when the leaf doesn't contain something simple (e.g. double, or double[])
	    if(type1.EqualTo("vector<double>") && type2.EqualTo("vector<double>")) {
	      branch_type = 1;
	      vector<double> * vec1 = (vector<double>*)leaf ->GetValuePointer();
	      vector<double> * vec2 = (vector<double>*)leaf2->GetValuePointer();
	      const size_t size1 = vec1->size();
	      const size_t size2 = vec2->size();

	      if(size1 || size2) found_non_empty_vector = true;
	      if(size1 == size2) {
		for(size_t j = 0; j < size1; j++) {
		  //same *= vec1->at(j) == vec2->at(j);
		  //Double comparison
		  same *= std::fabs( vec1->at(j)-vec2->at(j) ) <= std::min( 1e-8 * std::max( std::fabs( vec1->at(j) ), std::fabs( vec2->at(j) ) ), 1e-8 );
		}//j - loop over vector
	      }//check vector size
	      else same=false;
	    }//TLeafElement
	    else if(type1.EqualTo("vector<float>") && type2.EqualTo("vector<float>")) {
	      branch_type = 1;
	      vector<float> * vec1 = (vector<float>*)leaf ->GetValuePointer();
	      vector<float> * vec2 = (vector<float>*)leaf2->GetValuePointer();
	      const size_t size1 = vec1->size();
	      const size_t size2 = vec2->size();

	      if(size1 || size2) found_non_empty_vector = true;
	      if(size1 == size2) {
		for(size_t j = 0; j < size1; j++) {
		  //same *= vec1->at(j) == vec2->at(j);
		  //Float comparison
		  same *= std::fabs( vec1->at(j)-vec2->at(j) ) <= std::min( 1e-8 * std::max( std::fabs( vec1->at(j) ), std::fabs( vec2->at(j) ) ), 1e-8 );
		}//j - loop over vector
	      }//check vector size
	      else same=false;
	    }//TLeafElement
	    else if(type1.EqualTo("vector<int>") && type2.EqualTo("vector<int>")) {
	      branch_type = 1;
	      vector<int> * vec1 = (vector<int>*)leaf ->GetValuePointer();
	      vector<int> * vec2 = (vector<int>*)leaf2->GetValuePointer();
	      const size_t size1 = vec1->size();
	      const size_t size2 = vec2->size();

	      if(size1 || size2) found_non_empty_vector = true;
	      if(size1 == size2) {
		for(size_t j = 0; j < size1; j++) {
		  //same *= vec1->at(j) == vec2->at(j);
		  //Double comparison
		  same *= std::fabs( vec1->at(j)-vec2->at(j) ) <= std::min( 1e-8 * std::max( std::fabs( vec1->at(j) ), std::fabs( vec2->at(j) ) ), 1e-8 );
		}//j - loop over vector
	      }//check vector size
	      else same=false;
	    }//TLeafElement
	    else {
	      branch_type = 0;
	      //"simple" case
	      if(leaf->GetLen()==leaf2->GetLen()){
		for(long j=0;j<leaf->GetLen();j++){
		  //same*= leaf->GetValue(j)==leaf2->GetValue(j);
		  //Double comparison
		  same *= std::fabs( leaf->GetValue(j)-leaf2->GetValue(j) ) <= std::min( 1e-8 * std::max( std::fabs( leaf->GetValue(j) ), std::fabs( leaf2->GetValue(j) ) ), 1e-8 );
		}//j - loop over leaf array
	      }//check leaf array size
	      else same=false;
	    }//!TLeafElement
	  }//i - loop over number of entries
	}//check number of entries
	else same=false;

	if(branch_type == -1) {
	  fullsame = false;
	  cerr << "Unknown branch type " << leaf->GetTypeName()
	       << "for leaf " << obj->GetName() << endl
	       << "Will attempt to draw, but this function will return an error code" << endl;
	}
	else if(branch_type == 1) {
	  //check if we want to skip making the plot
	  // we do this if we have entirely empty vectors in all tree entries
	  if(!found_non_empty_vector) {
	    cout << "No non-empty vector entries for leaf " << obj->GetName() << endl
		 << "Will skip drawing this plot" << endl;
	    continue;
	  }
	}

	char buff2[256];
	if (!same){
	  sprintf(buff2,"%s Error!!!",obj->GetName());
	  fullsame*=same;
	}
	else {sprintf(buff2,"%s",obj->GetName());}

	//Now start drawing
	Plots.cd();
	TCanvas tmp(buff2,buff2,1000,500);
	tmp.Divide(2, 1);
	//first get the histogram ranges
	tree ->Draw(TString::Format("%s>>htemp1", obj->GetName()), "", "goff");
	tree2->Draw(TString::Format("%s>>htemp2", obj->GetName()), "", "goff");
	TH1F *htemp1 = (TH1F*)gDirectory->Get("htemp1");
	const int n1 = htemp1->GetNbinsX();
	const float lo1 = htemp1->GetXaxis()->GetBinLowEdge(1);
	const float hi1 = htemp1->GetXaxis()->GetBinUpEdge(n1);
	const float width1 = (hi1 - lo1) / n1;
	TH1F *htemp2 = (TH1F*)gDirectory->Get("htemp2");
	const int n2 = htemp2->GetNbinsX();
	const float lo2 = htemp2->GetXaxis()->GetBinLowEdge(1);
	const float hi2 = htemp2->GetXaxis()->GetBinUpEdge(n2);
	const float width2 = (hi2 - lo2) / n2;
	// and combine them into a sensible global range
	const float lo = min(lo1, lo2);
	const float hi = max(hi1, hi2);
	const float width = min (width1, width2);
	const int nbins = TMath::Min(100, (int)ceil((hi - lo) / width));
	//now actually draw the histograms
	tmp.cd(1);
	tree ->Draw(TString::Format("%s>>hnew(%d,%f,%f)", obj->GetName(), nbins, lo, hi));
	tree2->Draw(TString::Format("%s>>href(%d,%f,%f)", obj->GetName(), nbins, lo, hi),"","sames *H");
	TH1F *hnew = (TH1F*)gDirectory->Get("hnew");
	TH1F *href = (TH1F*)gDirectory->Get("href");
	hnew->GetXaxis()->SetTitle(obj->GetName());
	href->GetXaxis()->SetTitle(obj->GetName());
	hnew->SetLineColor(602);
	hnew->SetMarkerColor(602);
	href->SetLineColor(kRed);
	href->SetMarkerColor(kRed);
	//switch the draw order if required
	if(href->GetMaximum() > hnew->GetMaximum()) {
	  href->Draw("*H");
	  hnew->Draw("SAMES");
	}
	//sort the stat box
	tmp.Update();
	TPaveStats *st = (TPaveStats*)href->FindObject("stats");
	st->SetY1NDC(0.615);
	st->SetY2NDC(0.775);
	//draw the ratio
	tmp.cd(2);
	TH1F *hdiv = new TH1F(*hnew);
	hdiv->SetName("hdiv");
	//A straight forward Divide will set 0/0=0,
	// making this ratio histogram hard to check for issues
	//hdiv->Divide(href, hnew);
	//Therefore, do division by hand
	double w, cnew, cref;
        for(int ix = 0; ix <= href->GetNbinsX() + 1; ix++) {
          cnew  = hnew->GetBinContent(ix);
          cref  = href->GetBinContent(ix);
          if(cref) {
	    w = cnew / cref;
	    if(w != 1)
	      cout << cnew << " / " << cref << " = " << w << " in bin " << ix << " with center " << hdiv->GetXaxis()->GetBinCenter(ix) << endl;
	  }
          else if(!cref && !cnew)
	    w = 1;
          else
	    w = 0;
          hdiv->SetBinContent(ix, w);
        }//ix
	hdiv->SetTitle(TString::Format("Division;%s;New / Reference", obj->GetName()));
	hdiv->Draw();
	//add text with the mean difference
	double mean_new  = hnew->GetMean();
	double mean_ref  = href->GetMean();
	double mean_diff = 100. * (mean_new - mean_ref) / mean_ref;
	string mean_diff_unit = "%";
	//acount for 0 denominator
	if(TMath::Abs(mean_ref) < 1E-10) {
	  mean_diff = mean_new - mean_ref;
	  mean_diff_unit = "";
	}
	TText * text = nullptr;
	if(TMath::Abs(mean_diff) > 1E-6) {
	  tmp.cd(0);
	  text = new TText();
	  text->SetNDC();
	  //draw it top, middle-ish
	  text->SetText(0.45, 0.95, TString::Format("%+.4f%s", mean_diff, mean_diff_unit.c_str()));
	  text->Draw();
	}
	//save the canvas results
	tmp.Write();
	menu<<" <a href=\""<<buff2<<".gif\" class=\"menu\">"<<buff2<<"</a><br />";
	sprintf(buff,"%s/%s.gif",argv[1],buff2);
	tmp.SaveAs(buff);
	//cleanup
	delete hdiv;
	delete hnew;
	delete href;
	delete htemp1;
	delete htemp2;
	if(text)
	  delete text;
      }//loop over TLeaf's
      
    }
  }
  Plots.Write();
  Plots.Close();


  menu<<" </body></html>";
  menu.close();

  fullsame=(!fullsame);
  return fullsame;
}
