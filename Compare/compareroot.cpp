#include "TFile.h"
#include "TTree.h"
#include "TLeaf.h"
#include "TObject.h"
#include "TCanvas.h"


#include <iostream>
#include <fstream>

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


 index<<"<!doctype html><html><head><title>Index Page</title></head><frameset rows=\"8%,*\"><frame name=\"title\" src=\"title.html\"scrolling=\"no\" noresize><frameset cols=\"18%,*\"><frame name=\"menu\" src=\"menu.html\"scrolling=\"auto\" noresize><frame name=\"content\" src=\"content.html\"scrolling=\"yes\" noresize></frameset><body></body></html>" ;
 index.close();

 menu<<"<!doctype html><html><head><base target=\"content\"></head><body>";

 title<<"<!doctype html><html><head></head><body><H1><b><u>"<<argv[2]<<" Plots</u></b></H1></body></html>";
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
	bool same=true;
	
	TLeaf *leaf=(TLeaf*)obj;
	TLeaf *leaf2=tree2->GetLeaf(obj->GetName());
	
	long entries1=tree->GetEntriesFast();
	long entries2=tree2->GetEntriesFast();
	
	if (entries1==entries2){
	  for (long i=0;i<entries1;i++){
	    leaf->GetBranch()->GetEntry(i);
	    leaf2->GetBranch()->GetEntry(i);
	    if(leaf->GetLen()==leaf2->GetLen()){
	      for(long j=0;j<leaf->GetLen();j++){
		same*= leaf->GetValue(j)==leaf2->GetValue(j);
	      }
	    }
	  }
	}
	char buff2[256];
	if (!same){
	  sprintf(buff2,"%s Error!!!",obj->GetName());
	  fullsame*=same;
	}
	else {sprintf(buff2,"%s",obj->GetName());}
	Plots.cd();
	TCanvas tmp(buff2,buff2,500,500);
	tree->Draw(obj->GetName()); 
	tree2->Draw(obj->GetName(),"","same *H");
	tmp.Write();
	menu<<" <a href=\""<<buff2<<".gif\" class=\"menu\">"<<buff2<<"</a><br />";
	sprintf(buff,"%s/%s.gif",argv[1],buff2);
	tmp.SaveAs(buff);
      }
      
    }
  }
  
  Plots.Write();
  Plots.Close();


  menu<<" </body></html>";
  menu.close();

  fullsame=(!fullsame);
  return fullsame;
}
