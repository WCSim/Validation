#! /bin/env python

import glob
import os
import subprocess
import shutil
from pprint import pprint

validation_dir = os.path.expandvars('$WCSIM_VALIDATION_DIR')
build_dir = os.path.expandvars("$WCSIM_BUILD_DIR")
macs = sorted(glob.glob(f'{validation_dir}/Generate/macReference/*.mac'))
macs_short = [x.rsplit('/',1)[-1] for x in macs]
assert(os.path.isdir(validation_dir))
assert(os.path.isdir(build_dir))
assert(len(macs))

print(f'Creating reference WCSim output from: {build_dir}')

def GetSHA():
    os.chdir(f'{build_dir}/../src')
    command = f'git rev-list HEAD -1 > {validation_dir}/Compare/Reference/WCSimSHA'
    os.system(command)
    with open(f'{validation_dir}/Compare/Reference/WCSimSHA') as f:
        print(f'Using WCSim SHA: {f.readline()}')
    
def MakeReference(job_num):
    os.chdir(f'{build_dir}')
    #Run WCSim
    mac = macs[job_num]
    print(f'Running job: {job_num}, file: {mac}')
    logfile = f'{job_num}.out'
    f = open(logfile, 'w')
    subprocess.run(['WCSim', mac, f'{validation_dir}/Generate/macReference/tune/tuning_parameters.mac'], stderr=subprocess.STDOUT, stdout=f, text=True)
    f.close()
    #Get the relevant histograms from WCSim
    rootfile = mac.rsplit('/',1)[-1].replace('_seed20230628.mac', '.root')
    subprocess.run([f'{validation_dir}/Generate/daq_readfilemain', rootfile, '0'])
    #Move the histogram file to the reference location
    for branch in ['wcsimrootevent', 'wcsimrootevent2', 'wcsimrootevent_OD']:
        histfile = rootfile.replace('.root', f'_analysed_{branch}.root')
        if os.path.isfile(histfile):
            shutil.move(histfile, f'{validation_dir}/Compare/Reference/{histfile}')
    #Write the bad printouts information to the reference location
    badfile = rootfile.replace('.root', '_bad.txt')
    #Get the stats of bad printouts
    bads = {}
    with open(f'{validation_dir}/Compare/Reference/{badfile}', 'w') as f:
        for bad in ['GeomNav1002', '"Optical photon is killed because of missing refractive index"']:
            bads[bad] = int(subprocess.run(['grep', '-c', bad, logfile], stdout=subprocess.PIPE, text=True).stdout)
            f.write('{bad} {bads[bad]}\n')
    pprint(bads)

def PushToGit(branch_name='new_ref'):
    os.chdir(validation_dir)
    os.system('git config user.name "Travis CI"')
    os.system('git config user.email "wcsim@wcsim.wcsim"')
    os.system('git fetch origin')
    os.system(f'git checkout -b {branch_name} origin/{branch_name} --track || git checkout -b {branch_name}')
    os.system('git add --all')
    os.system('git commit -m "CI reference update"')
    os.system(f'git pull origin {branch_name}')
    os.system('git push https://tdealtry:${GitHubToken}@github.com/tdealtry/Validation.git ' + branch_name)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-number', '-j', type=int, nargs='+', required=True, choices=range(len(macs)), help='Job numbers to run.' + '\n'.join([f'{a:02d}: {b}' for a,b in zip(range(len(macs)), macs_short)]))
    args = parser.parse_args()

    jobs_to_run = set(args.job_number)
    for job in jobs_to_run:
        print(job)
        if job == 0:
            GetSHA()
        MakeReference(job)
    #now all jobs have run, commit to the repo
    PushToGit()
