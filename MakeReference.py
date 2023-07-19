#! /bin/env python

import sys
import glob
import os
import subprocess
import shutil
from pprint import pprint
import time

validation_dir = os.path.expandvars('$ValidationPath')
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
    #Check it worked
    rootfile = mac.rsplit('/',1)[-1].replace('_seed20230628.mac', '.root')
    if not os.path.isfile(rootfile):
        print(f'Cannot find expected WCSim output root file: {rootfile}')
        return False
    #Get the relevant histograms from WCSim
    subprocess.run([f'{validation_dir}/Generate/daq_readfilemain', rootfile, '0'])
    #Move the histogram file to the reference location
    found_a_histfile = False
    for branch in ['wcsimrootevent', 'wcsimrootevent2', 'wcsimrootevent_OD']:
        histfile = rootfile.replace('.root', f'_analysed_{branch}.root')
        if os.path.isfile(histfile):
            shutil.move(histfile, f'{validation_dir}/Compare/Reference/{histfile}')
            found_a_histfile = True
    #Get the stats of bad printouts
    # including writing the bad printouts information to the reference location
    badfile = rootfile.replace('.root', '_bad.txt')
    bads = {}
    with open(f'{validation_dir}/Compare/Reference/{badfile}', 'w') as f:
        for bad in ['GeomNav1002', 'Optical photon is killed because of missing refractive index']:
            bads[bad] = int(subprocess.run(['grep', '-c', f'"{bad}"', logfile], stdout=subprocess.PIPE, text=True).stdout)
            f.write(f'"{bad}" {bads[bad]}\n')
    pprint(bads)
    #Get the geometry text file
    geofiles = glob.glob('geofile_*.txt')
    if len(geofiles) == 1:
        geofile_to_move = geofiles[0]
    elif len(geofiles) == 2:
        geofile_to_move = [x for x in geofiles if 'SuperK' not in x][0]
    #leave it not in the correct place, to account for git pull clashes
    shutil.move(geofile_to_move, f'{validation_dir}/{geofile_to_move}')
    #return
    return not found_a_histfile

def PushToGit(job_str, branch_name='new_ref'):
    os.chdir(validation_dir)
    #setup default names, or git complains
    os.system('git config user.name "WCSim CI"')
    os.system('git config user.email "wcsim@wcsim.wcsim"')
    #fetch any changes from the remote
    os.system('git fetch origin')
    #make sure we're on correct branch
    # - gets the remote one, if it exists remotely
    # - otherwise makes a new branch locally, based on the default branch
    os.system(f'git checkout -b {branch_name} origin/{branch_name} --track || git checkout -b {branch_name}')
    #add all our changes
    os.system('git add Compare/')
    #commit
    os.system(f'git commit -m "CI reference update. Job(s): {job_str}"')
    #pull any remote changes
    # Need to account for conflicts in the geofile.txt
    #  This is done by not moving it to the correct place until after the pull
    # However all other files are unique to each job
    subprocess.run(['git', 'pull', '--no-rebase', 'origin', branch_name])
    for geofilenew in glob.glob(f'{validation_dir}/geofile_*.txt'):
        shutil.move(geofilenew, f'{validation_dir}/Compare/Reference/{geofilenew.rsplit("/",1)[-1]}')
    #now try push
    try:
        subprocess.run(['git', 'push', 'https://tdealtry:${GitHubToken}@github.com/tdealtry/Validation.git', branch_name], check=True)
    except subprocess.CalledProcessError:
        #if it didn't work, undo the last commit
        os.system('git reset HEAD~1')
        #clear the geofile changes
        os.system('git checkout Compare/Reference/geofile_*.txt')
        #have a rest before trying again
        time.sleep(15)
        PushToGit(branch_name)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-number', '-j', type=int, nargs='+', required=True, choices=range(len(macs)), help='Job numbers to run.' + '\n'.join([f'{a:02d}: {b}' for a,b in zip(range(len(macs)), macs_short)]))
    args = parser.parse_args()

    jobs_to_run = set(args.job_number)
    failure = False
    for job in jobs_to_run:
        print(job)
        if job == 0:
            GetSHA()
        failure = failure or MakeReference(job)
    #now all jobs have run, commit to the repo
    PushToGit(','.join([str(x) for x in jobs_to_run]))

    if failure:
        sys.exit(-1)
