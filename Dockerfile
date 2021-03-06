### Download base image from cern repo on docker hub
FROM cern/slc6-base:latest

### Run the following commands as super user (root):
USER root

#######################
### GCC ENVIRONMENT ###
#######################

### Required package for ROOT
RUN yum install -y \
    wget \
    tar \
    cmake \
    gcc-c++ \
    gcc \
    binutils \
    libX11-devel \
    libXpm-devel \
    libXft-devel \
    libXext-devel \
    time \
    libpng \
    libjpeg

### Git and OpenGL for WCSim
RUN yum install -y \
    git \
    mesa-libGL-devel \
    mesa-libGLU-devel \
    libXmu-devel \
    libXi-devel \
    expat-devel

### Setup environment
RUN mkdir /root/HyperK
ENV HYPERKDIR /root/HyperK
RUN export HYPERKDIR

### Downloading ROOT
RUN cd $HYPERKDIR \
    && wget https://root.cern.ch/download/root_v5.34.36.Linux-slc6-x86_64-gcc4.4.tar.gz \
    && tar -xvzf root_v5.34.36.Linux-slc6-x86_64-gcc4.4.tar.gz \
    && rm -f root_v5.34.36.Linux-slc6-x86_64-gcc4.4.tar.gz

### Downloading Geant4
RUN cd $HYPERKDIR \
    && wget http://geant4.web.cern.ch/geant4/support/source/lib4.10.1.p03/Linux-g++4.4.7-SLC6.tar.gz \
    && tar -xvzf Linux-g++4.4.7-SLC6.tar.gz \
    && rm -f Linux-g++4.4.7-SLC6.tar.gz

### Data files for Geant4
ENV G4DATA $HYPERKDIR/Geant4-10.1.3-Linux/share/Geant4-10.1.3/data
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4ABLA.3.0.tar.gz \
    && tar -xvzf G4ABLA.3.0.tar.gz \
    && rm -f G4ABLA.3.0.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4NDL.4.5.tar.gz \
    && tar -xvzf G4NDL.4.5.tar.gz \
    && rm -f G4NDL.4.5.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4EMLOW.6.41.tar.gz \
    && tar -xvzf G4EMLOW.6.41.tar.gz \
    && rm -f G4EMLOW.6.41.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4PhotonEvaporation.3.1.tar.gz \
    && tar -xvzf G4PhotonEvaporation.3.1.tar.gz \
    && rm -f G4PhotonEvaporation.3.1.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4RadioactiveDecay.4.2.tar.gz \
    && tar -xvzf G4RadioactiveDecay.4.2.tar.gz \
    && rm -f G4RadioactiveDecay.4.2.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4SAIDDATA.1.1.tar.gz \
    && tar -xvzf G4SAIDDATA.1.1.tar.gz \
    && rm -f G4SAIDDATA.1.1.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4NEUTRONXS.1.4.tar.gz \
    && tar -xvzf G4NEUTRONXS.1.4.tar.gz \
    && rm -f G4NEUTRONXS.1.4.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4PII.1.3.tar.gz \
    && tar -xvzf G4PII.1.3.tar.gz \
    && rm -f G4PII.1.3.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/RealSurface.1.0.tar.gz \
    && tar -xvzf RealSurface.1.0.tar.gz \
    && rm -f RealSurface.1.0.tar.gz
RUN cd $G4DATA \
    && wget http://geant4.web.cern.ch/geant4/support/source/G4ENSDFSTATE.1.0.tar.gz \
    && tar -xvzf G4ENSDFSTATE.1.0.tar.gz \
    && rm -f G4ENSDFSTATE.1.0.tar.gz

### ENV Geant4
ENV G4WORKDIR $HYPERKDIR/WCSim/exe
ENV WCSIMDIR $HYPERKDIR/WCSim
ENV G4INSTALL $HYPERKDIR/Geant4-10.1.3-Linux
ENV G4LIB $G4INSTALL/lib
RUN export G4WORKDIR
RUN export WCSIMDIR
RUN export G4INSTALL
RUN export G4LIB

ADD env-WCSim.sh $HYPERKDIR/

###Adding Validation
#RUN cd /root \
#    && git clone https://github.com/wcsimtravis/Validation.git

#ENV ValidationPath /root/Validation
#RUN export ValidationPath

#RUN cd $ValidationPath/Compare \
#    && source $HYPERKDIR/env-WCSim.sh \
#    && g++ compareroot.cpp -o compareroot `root-config --libs --cflags` 

#ENV LD_LIBRARY_PATH=$WCSIM:$LD_LIBRARAY_PATH
#RUN export LD_LIBRARAY_PATH



### Open terminal
CMD ["/bin/bash"]
 