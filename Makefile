
.PHONY: all
all: compareroot daq_readfilemain

compareroot:
	g++ Compare/compareroot.cpp -o Compare/compareroot `root-config --libs --cflags` 

daq_readfilemain:
	g++ Generate/daq_readfilemain.C -o Generate/daq_readfilemain `root-config --libs --cflags` -L $(WCSIM_BUILD_DIR)/lib -lWCSimRoot -I $(WCSIM_BUILD_DIR)/include/WCSim

clean:
	$(RM) Generate/daq_readfilemain Compare/compareroot
