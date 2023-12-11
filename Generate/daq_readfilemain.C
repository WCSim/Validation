#include <iostream>
#include <algorithm>
#include <vector>
#include <stdio.h>     
#include <stdlib.h>    
#include <TCanvas.h>
#include <TFile.h>
#include <TString.h>
#include <TTree.h>
#include <TBranch.h>
#include <TSystem.h>
#include <TStyle.h>
#include <TLegend.h>
#include <TROOT.h>
#include <sstream>

#include "WCSimRootEvent.hh"
#include "WCSimRootGeom.hh"
#include "WCSimEnumerations.hh"

using namespace std;

TString create_filename(const char * suffix, TString& filename_string, const char * format = ".pdf")
{
  //std::cout<< "Creating filename from suffix " << suffix << " and filename_string " << filename_string << std::endl;
  TString suffix_string = TString::Format("_%s%s", suffix, format);
  TString format_string(format);
  TString outfilename = filename_string.ReplaceAll(format_string.Data(), suffix_string.Data());
  return outfilename;
}

// Simple example of reading a generated Root file
int daq_readfile(const char *filename=NULL,
		 bool verbose=false,
		 const char * inbranch="wcsimrootevent",
		 Long64_t max_nevents = 999999999999,
		 int max_ntriggers = -1)
{
  cout << filename << "\t " << inbranch << endl;
  // Open the input file
  TFile *file;
  if (filename==NULL){
    file = new TFile("../wcsim.root","read");
  }else{
    std::stringstream tmp;
    tmp<<"./"<<filename;
    file = new TFile(tmp.str().c_str(),"read");
  }
  if (!file->IsOpen()){
    cout << "Error, could not open input file: " << filename << endl;
    return -1;
  }
  // Get the a pointer to the tree from the file
  TTree *tree = (TTree*)file->Get("wcsimT");
  if(!tree) {
    cout << "Couldn't find TTree wcsimT. Exiting..." << endl;
    return -1;
  }

  // Get the number of events
  Long64_t nevent = tree->GetEntries();
  printf("nevent %lld\n",nevent);
  nevent = TMath::Min(nevent, max_nevents); //cut the loop earlier
 
  // Create a WCSimRootEvent to put stuff from the tree in
  WCSimRootEvent* wcsimrootsuperevent = new WCSimRootEvent();

  // Set the branch address for reading from the tree
  TBranch *branch = tree->GetBranch(inbranch);
  if(!branch) {
    cout << "Branch " << inbranch << " does not exist in this code base. Exiting..." << endl;
    return 1;
  }
  branch->SetAddress(&wcsimrootsuperevent);
  if(branch->GetEntries() == 0) {
    cout << "Branch " << inbranch << " has no entries. Exiting..." << endl;
    return 1;
  }

  // Force deletion to prevent memory leak 
  tree->GetBranch(inbranch)->SetAutoDelete(kTRUE);

  // Geometry tree - only need 1 "event"
  TTree *geotree = (TTree*)file->Get("wcsimGeoT");
  WCSimRootGeom *geo = 0; 
  geotree->SetBranchAddress("wcsimrootgeom", &geo);
  if(verbose) std::cout << "Geotree has " << geotree->GetEntries() << " entries" << std::endl;
  if(geotree->GetEntries() == 0) {
    cout << "geotree not found!" << endl;
      exit(9);
  }
  geotree->GetEntry(0);
  // start with the main "subevent", as it contains most of the info
  // and always exists.
  WCSimRootTrigger* wcsimrootevent;

  //The 0th trigger contains:
  // - track information
  // - raw hit information
  // - digit information (for trigger 0)
  //Subsequent triggers contain:
  // - digit information (for that trigger) only
  //Therefore if you want to do truth matching on trigger >= 1,
  // you need to keep a copy of trigger 0 to read the track/hit info
  // Store it here
  WCSimRootTrigger* wcsimroottrigger0;

  //create output file for storing tree
  cout << filename << endl;
  TString filenameout(filename);
  TFile * fout = new TFile(create_filename(TString::Format("analysed_%s", inbranch), filenameout, ".root").Data(), "RECREATE");
  fout->cd();

  //create tree to save information on an event-by-event basis
  TTree * tout_file = new TTree("validation_per_file", "File by file validation variables");
  TTree * tout = new TTree("validation_per_event", "Event by event validation variables");
  TTree * tout_trig = new TTree("validation_per_trigger", "Trigger by trigger validation variables");
  //event id variables
  int teventnumber, ttriggernumber;
  tout->Branch("eventnumber", &teventnumber);
  tout_trig->Branch("eventnumber", &teventnumber);
  tout_trig->Branch("triggernumber", &ttriggernumber);
  //per file variables
  int npmt20, npmtm, npmtod;
  tout_file->Branch("npmt20", &npmt20);
  tout_file->Branch("npmtm", &npmtm);
  tout_file->Branch("npmtod", &npmtod);
  //per event variables
  double tvtx0, tvtx1, tvtx2;
  int    tntriggers, tntracks, tnrawhits, tntubeshitraw;
  vector<double> tvhittime, tvhittime_noise, tvhittime_photon;
  vector<int> tvtrack_ipnu, tvtrack_flag;
  vector<float> tvtrack_energy;
  vector<double> tvtrack_time;
  vector<TVector3> tvtrack_startpos, tvtrack_stoppos;
  tout->Branch("vtx0", &tvtx0);
  tout->Branch("vtx1", &tvtx1);
  tout->Branch("vtx2", &tvtx2);
  tout->Branch("ntriggers", &tntriggers);
  tout->Branch("ntracks", &tntracks);
  tout->Branch("nrawhits", &tnrawhits);
  tout->Branch("ntubeshitraw", &tntubeshitraw);
  tout->Branch("hittime", &tvhittime);
  tout->Branch("hittime_noise", &tvhittime_noise);
  tout->Branch("hittime_photon", &tvhittime_photon);
  tout->Branch("track_ipnu", &tvtrack_ipnu);
  tout->Branch("track_flag", &tvtrack_flag);
  tout->Branch("track_energy", &tvtrack_energy);
  tout->Branch("track_time", &tvtrack_time);
  //tout->Branch("track_startpos", &tvtrack_startpos);
  //tout->Branch("track_stoppos", &tvtrack_stoppos);
  //per trigger variables
  int ttriggertype;
  int tndigihits, tntubeshitdigi, tndigihitstrigger;
  double ttriggertime;
  double tdigipeperdigi, tdigitimeperdigi;
  double ttotaldigipe;
  double ttotaldiginoisefrac;
  vector<double> tvdigipe;
  vector<double> tvdigitime, tvdigitime_noise, tvdigitime_photon, tvdigitime_mix;
  vector<double> tvdigiplustriggertime;
  vector<double> tvdiginoisefrac;
  tout_trig->Branch("triggertype", &ttriggertype);
  tout_trig->Branch("ndigihits", &tndigihits);
  tout_trig->Branch("ntubeshitdigi", &tntubeshitdigi);
  tout_trig->Branch("ndigihitstrigger", &tndigihitstrigger);
  tout_trig->Branch("triggertime", &ttriggertime);
  tout_trig->Branch("digipeperdigi", &tdigipeperdigi);
  tout_trig->Branch("digitimeperdigi", &tdigitimeperdigi);
  tout_trig->Branch("totaldigipe", &ttotaldigipe);
  tout_trig->Branch("totaldiginoisefrac", &ttotaldiginoisefrac);
  tout_trig->Branch("digipe", &tvdigipe);
  tout_trig->Branch("digitime", &tvdigitime);
  tout_trig->Branch("digitime_noise", &tvdigitime_noise);
  tout_trig->Branch("digitime_photon", &tvdigitime_photon);
  tout_trig->Branch("digitime_mix", &tvdigitime_mix);
  tout_trig->Branch("digiplustriggertime", &tvdigiplustriggertime);
  tout_trig->Branch("diginoisefrac", &tvdiginoisefrac);


  npmt20 = geo->GetWCNumPMT();
  npmtm = geo->GetWCNumPMT(true);
  npmtod = geo->GetODWCNumPMT();
  tout_file->Fill();
  
  int num_trig = 0;
  
  // Now loop over events
  for (int ev=0; ev<nevent; ev++)
  {
    teventnumber = ev;

    //Reset per event tree variables
    tvtx0                 = -999999;
    tvtx1                 = -999999;
    tvtx2                 = -999999;
    tntriggers            = -1;
    tntracks              = -1;
    tnrawhits             = -1;
    tntubeshitraw         = -1;
    tvhittime.clear();
    tvhittime_noise.clear();
    tvhittime_photon.clear();
    tvtrack_ipnu.clear();
    tvtrack_flag.clear();
    tvtrack_energy.clear();
    tvtrack_time.clear();
    tvtrack_startpos.clear();
    tvtrack_stoppos.clear();


    // Read the event from the tree into the WCSimRootEvent instance
    if(verbose)
      printf("\n********************************************************\n");
    Int_t nbytes = tree->GetEntry(ev);
    if(nbytes == 0) {
      cerr << "Event " << ev << " reads no bytes!" << endl;
      continue;
    }
    else if(nbytes == -1) {
      cerr << "Event " << ev << " had an I/O error" << endl;
      continue;
    }
    wcsimrootevent = wcsimrootsuperevent->GetTrigger(0);

    const int ntriggers = wcsimrootsuperevent->GetNumberOfEvents();
    tntriggers = ntriggers;

    if(verbose || ((ev % 100) == 0))
      cout << "Event " << ev << " of " << nevent << " has " << ntriggers << " triggers" << endl;
    const double vtx0 = wcsimrootevent->GetVtx(0);
    const double vtx1 = wcsimrootevent->GetVtx(1);
    const double vtx2 = wcsimrootevent->GetVtx(2);
    if(verbose){
      printf("Evt, date %d %ld\n", wcsimrootevent->GetHeader()->GetEvtNum(),
	     wcsimrootevent->GetHeader()->GetDate());
      printf("Mode %d\n", wcsimrootevent->GetMode());
      printf("Number of subevents %d\n",
	     wcsimrootsuperevent->GetNumberOfSubEvents());
      
      printf("Vtxvol %d\n", wcsimrootevent->GetVtxvol());
      printf("Vtx %f %f %f\n", vtx0, vtx1, vtx2);
    }
    tvtx0 = vtx0;
    tvtx1 = vtx1;
    tvtx2 = vtx2;
    if(verbose){
      printf("Jmu %d\n", wcsimrootevent->GetJmu());
      printf("Npar %d\n", wcsimrootevent->GetNpar());
    }
    // Now read the tracks in the event

    // Get the number of tracks
    const int ntracks = wcsimrootevent->GetNtrack();
    if(verbose) printf("ntracks=%d\n",ntracks);
    tntracks = ntracks;

    // Loop through elements in the TClonesArray of WCSimTracks
    for (int itrack = 0; itrack < ntracks; itrack++)
    {
      TObject *element = (wcsimrootevent->GetTracks())->At(itrack);      
      WCSimRootTrack *wcsimroottrack = dynamic_cast<WCSimRootTrack*>(element);
      tvtrack_ipnu.push_back(wcsimroottrack->GetIpnu());
      tvtrack_flag.push_back(wcsimroottrack->GetFlag());
      tvtrack_energy.push_back(wcsimroottrack->GetE());
      tvtrack_time.push_back(wcsimroottrack->GetTime());
      tvtrack_startpos.push_back(TVector3(wcsimroottrack->GetStart(0),
					  wcsimroottrack->GetStart(1),
					  wcsimroottrack->GetStart(2)));
      tvtrack_stoppos.push_back(TVector3(wcsimroottrack->GetStop(0),
					 wcsimroottrack->GetStop(1),
					 wcsimroottrack->GetStop(2)));
      if(verbose){
	printf("Track ipnu: %d\n",wcsimroottrack->GetIpnu());
	printf("Track parent ID: %d\n",wcsimroottrack->GetParenttype());
	for (int j=0; j<3; j++)
	  printf("Track dir: %d %f\n", j, wcsimroottrack->GetDir(j));
      }
    }  //itrack // End of loop over tracks
    
    //get number of hits and digits
    const int ncherenkovhits      = wcsimrootevent->GetNcherenkovhits();
    const int ncherenkovhittimes  = wcsimrootevent->GetNcherenkovhittimes();
    const int ntubeshit           = wcsimrootevent->GetNumTubesHit();
    const int ncherenkovdigihits0 = wcsimrootevent->GetNcherenkovdigihits(); 
    const int ntubesdigihit0      = wcsimrootevent->GetNumDigiTubesHit();
    if(verbose){
      printf("node id: %i\n", ev);
      printf("Ncherenkovhits (unique PMTs with hits)  %d\n", ncherenkovhits);
      printf("Ncherenkovhittimes (number of raw hits) %d\n", ncherenkovhittimes);
      printf("Ncherenkovdigihits (number of digits) in trigger 0   %d\n", ncherenkovdigihits0);
      printf("NumTubesHit       %d\n", wcsimrootevent->GetNumTubesHit());
      printf("NumDigitizedTubes in trigger 0 %d\n", wcsimrootevent->GetNumDigiTubesHit());
    }
    tnrawhits     = ncherenkovhittimes;
    tntubeshitraw = ntubeshit;

    //
    // Now look at the raw Cherenkov+noise hits
    //
    if(verbose)
      cout << "RAW HITS:" << endl;

    // Grab the big arrays of times and parent IDs
    TClonesArray *timeArray = wcsimrootevent->GetCherenkovHitTimes();
    
    //calculate total p.e. in event
    int totalPe = 0;
    // Loop through elements in the TClonesArray of WCSimRootCherenkovHits
    for(int ipmt = 0; ipmt < ncherenkovhits; ipmt++) {
      TObject * Hit = (wcsimrootevent->GetCherenkovHits())->At(ipmt);
      WCSimRootCherenkovHit * wcsimrootcherenkovhit =
	dynamic_cast<WCSimRootCherenkovHit*>(Hit);
      int timeArrayIndex = wcsimrootcherenkovhit->GetTotalPe(0);
      int peForTube      = wcsimrootcherenkovhit->GetTotalPe(1);
      int tubeNumber     = wcsimrootcherenkovhit->GetTubeID();
      WCSimRootPMT pmt   = geo->GetPMT(tubeNumber-1);
      totalPe += peForTube;
      if(verbose)
	printf("Total pe for tube %d: %d times( ", tubeNumber, peForTube);
      for(int irawhit = 0; irawhit < peForTube; irawhit++) {
	TObject * HitTime = (wcsimrootevent->GetCherenkovHitTimes())->At(timeArrayIndex + irawhit);
	WCSimRootCherenkovHitTime * wcsimrootcherenkovhittime =
	  dynamic_cast<WCSimRootCherenkovHitTime*>(HitTime);
	double truetime = wcsimrootcherenkovhittime->GetTruetime();
	if(verbose)
	  printf("%6.2f ", truetime);
	tvhittime.push_back(truetime);
	if(wcsimrootcherenkovhittime->GetParentID() == -1) {
	  tvhittime_noise.push_back(truetime);
	}
	else {
	  tvhittime_photon.push_back(truetime);
	}
      }//irawhit
      if(verbose)
	cout << ")" << endl;
    }//ipmt
    if(verbose)
      cout << "Total Pe : " << totalPe << endl;

    //    
    // Now look at digitized hit info
    //
    if(verbose)
      cout << "DIGITIZED HITS:" << endl;

    //
    // Digi hits are arranged in subevents, so loop over these first
    //
    const int ntriggers_loop = max_ntriggers > 0 ? TMath::Min(max_ntriggers, ntriggers) : ntriggers;

   //save a pointer to the 0th WCSimRootTrigger, so can access track/hit information in triggers >= 1
   wcsimroottrigger0 = wcsimrootevent;



    for (int itrigger = 0 ; itrigger < ntriggers_loop; itrigger++) {

      ttriggernumber = itrigger;

      //Reset per trigger tree variables
      ttriggertype          = -1;
      tndigihits            = -1;
      tntubeshitdigi        = -1;
      tndigihitstrigger     = -1;
      ttriggertime          = -999999;
      tdigipeperdigi        = -1;
      tdigitimeperdigi      = -999999;
      ttotaldigipe          = -1;
      ttotaldiginoisefrac   = -1;
      tvdigipe.clear();
      tvdigitime.clear();
      tvdigitime_noise.clear();
      tvdigitime_photon.clear();
      tvdigitime_mix.clear();
      tvdigiplustriggertime.clear();
      tvdiginoisefrac.clear();

      //count the number of noise/photon hits making up all the digits in this trigger
      int n_noise_hits_total = 0, n_photon_hits_total = 0;

      wcsimrootevent = wcsimrootsuperevent->GetTrigger(itrigger);
      if(verbose)
	cout << "Sub event number = " << itrigger << "\n";
      const int ncherenkovdigihits = wcsimrootevent->GetNcherenkovdigihits();
      const int ntubeshitdigi      = wcsimrootevent->GetNumDigiTubesHit();
      if(verbose) {
	printf("Ncherenkovdigihits %d\n", ncherenkovdigihits);
	printf("NumDigiTubesHit %d\n", ntubeshitdigi);
      }
      
      const int            trigger_time = wcsimrootevent->GetHeader()->GetDate();
      const TriggerType_t  trigger_type = wcsimrootevent->GetTriggerType();
      std::vector<Double_t> trigger_info = wcsimrootevent->GetTriggerInfo();

      if(trigger_info.size() > 0) {
	tndigihitstrigger = trigger_info[0];
      }

      if(verbose) {
	cout << "Passed trigger "
	     << WCSimEnumerations::EnumAsString(trigger_type)
	     << " with timestamp " << trigger_time
	     << " and " << ncherenkovdigihits
	     << " hits in the saved subevent region";
	if(trigger_info.size() > 0) {
	  if((trigger_type == kTriggerNDigits) || (trigger_type == kTriggerNDigitsTest))
	    cout << " (" << trigger_info[0]
		 << " in the 200nsec region)";
	}
	cout << endl;
      }
      ttriggertype   = (int)trigger_type;
      tndigihits     = ncherenkovdigihits;
      tntubeshitdigi = ntubeshitdigi;
      ttriggertime   = trigger_time;

      if(ncherenkovdigihits > 0)
	num_trig++;

      // Loop through elements in the TClonesArray of WCSimRootCherenkovDigHits
      float totaldigipe = 0, totaldigitime = 0;
      for(int idigipmt = 0; idigipmt < ncherenkovdigihits; idigipmt++) {
	//get the digit
	if(verbose)
	  cout << "Getting digit " << idigipmt << endl;
	TObject *element = (wcsimrootevent->GetCherenkovDigiHits())->At(idigipmt);
    	WCSimRootCherenkovDigiHit *wcsimrootcherenkovdigihit = 
    	  dynamic_cast<WCSimRootCherenkovDigiHit*>(element);
	
	std::vector<int> rawhit_ids=wcsimrootcherenkovdigihit->GetPhotonIds();
	if(verbose)
	  cout << " " << rawhit_ids.size() << " rawhits made up this digit" << endl;

	// loop over photons within the digit
	int rawhit_id=0;
	int n_noise_hits = 0, n_photon_hits = 0, n_unknown_hits = 0;
	for(auto therawhitid : rawhit_ids){
	  if(therawhitid < 0)
	    continue;
	  if(verbose)
	    cout << "  rawhitid " << therawhitid << endl;
	  WCSimRootCherenkovHitTime *wcsimrootcherenkovhittime =
	    dynamic_cast<WCSimRootCherenkovHitTime*>(timeArray->At(therawhitid));
	  if(wcsimrootcherenkovhittime == nullptr)
	    continue;
	  //now look in the WCSimRootCherenkovHitTime array to count the number of photon / dark noise hits
	  const double hittime  = wcsimrootcherenkovhittime->GetTruetime();
	  const int    parentid = wcsimrootcherenkovhittime->GetParentID();
	  if(verbose)
	    cout << " hit time " << hittime << " " << parentid << endl;
	  if(parentid == -1) {
	    n_noise_hits++;
	  }
	  else if(parentid < 0) {
	    n_unknown_hits++;
	  }
	  else {
	    n_photon_hits++;
	  }
	}//therawhitid //loop over rawhit_ids

	const double digitime = wcsimrootcherenkovdigihit->GetT();
	const double digipe   = wcsimrootcherenkovdigihit->GetQ();
	if(verbose) 
	  cout << " Digit time: " << digitime << endl
	       << " Digit pe:   " << digipe << endl;
	tvdigipe.push_back(digipe);
	tvdigitime.push_back(digitime);
	tvdigiplustriggertime.push_back(digitime + trigger_time);

	if(verbose){
	  printf("q, t, tubeid, nphotonhits, nnoisehits, nunknownhits: %f %f %d  %d %d %d\n",
		 digipe,
		 digitime,
		 wcsimrootcherenkovdigihit->GetTubeId(),
		 n_photon_hits,
		 n_noise_hits,
		 n_unknown_hits);
	}
	if(n_noise_hits && !n_photon_hits) {
	  tvdigitime_noise.push_back(digitime);
	}
	else if(!n_noise_hits && n_photon_hits) {
	  tvdigitime_photon.push_back(digitime);
	}
	else {
	  tvdigitime_mix.push_back(digitime);
	}
	totaldigipe   += digipe;
	totaldigitime += digitime;
	float noise_fraction = (float)n_noise_hits / (float)(n_noise_hits + n_photon_hits + n_unknown_hits);
	noise_fraction = -1;
	tvdiginoisefrac.push_back(noise_fraction);
	n_noise_hits_total += n_noise_hits;
	n_photon_hits_total += n_photon_hits;
      }//idigipmt // End of loop over Cherenkov digihits
      ttotaldigipe = totaldigipe;
      if(ncherenkovdigihits) {
	double peperdigi   = totaldigipe   / ncherenkovdigihits;
	double timeperdigi = totaldigitime / ncherenkovdigihits;
	tdigipeperdigi   = peperdigi;
	tdigitimeperdigi = timeperdigi;
      }
      float noise_fraction_total = (float)n_noise_hits_total / (float)(n_noise_hits_total + n_photon_hits_total);
      //well-defined default for events with no digits
      if(! (n_noise_hits_total + n_photon_hits_total))
	noise_fraction_total = -1;
      ttotaldiginoisefrac = noise_fraction_total;
      //fill the per trigger output tree
      tout_trig->Fill();
    }//itrigger // End of loop over triggers
    
    wcsimroottrigger0 = 0;

    // reinitialize super event between loops.
    wcsimrootsuperevent->ReInitialize();

    //fill the per event output tree
    tout->Fill();
  }//ev // End of loop over events
 
 cout << "---------------------------------" << endl
       << "Run summary" << endl
       << "nevent (run over) " << nevent << endl
       << "num_trig (run over) " << num_trig << endl;

  //write the trees
  fout->cd();
  tout_file->Write();
  tout->Write();
  tout_trig->Write();
  fout->Close();

  //cleanup memory
  //input
  delete wcsimrootsuperevent;
  delete file;
  //output
  delete fout;

  return 0;
}

void usage(string * branches){
  std::cerr << "Usage: daq_readfilemain <FILENAME> <VERBOSE> <PMTTYPE>" << std::endl
	    << "    VERBOSE = 0 or 1" << std::endl
	    << "    PMTTYPE =" << std::endl;
  for(int i = 0; i < 3; i++)
    std::cerr << "        " << i << "  " << branches[i] << std::endl;
}

int main(int argc, char *argv[]){
  string branches[3] = {"wcsimrootevent",
			"wcsimrootevent2",
			"wcsimrootevent_OD"};

  if(argc != 4) {
    std::cerr << "Invalid number of arguments: " << argc << std::endl
	      << std::endl;
    usage(branches);
    return 1;
  }
    
  const int jobtodo = atoi(argv[3]);
  if(jobtodo < 0 || jobtodo >= 3) {
    std::cerr << "Invalid PMT type " << jobtodo << std::endl
	      << std::endl;
    usage(branches);
    return 1;
  }
  daq_readfile(argv[1], atoi(argv[2]), branches[jobtodo].c_str());
  
  return 0;

}
