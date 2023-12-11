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
    if rootfile == 'wcsim_test_sk.root':
        rootfile = 'wcsim_test.root'
    if not os.path.isfile(rootfile):
        print(f'Cannot find expected WCSim output root file: {rootfile}')
        with open(logfile) as flog:
            print(flog.read())
        return True
    else:
        print(f'Created output root file: {rootfile}')
    #Get the relevant histograms from WCSim
    for ipmttype in range(3):
        subprocess.run([f'{validation_dir}/Generate/daq_readfilemain', rootfile, '0', ipmttype])
    #Move the histogram file to the reference location
    found_a_histfile = False
    for branch in ['wcsimrootevent', 'wcsimrootevent2', 'wcsimrootevent_OD']:
        histfile = rootfile.replace('.root', f'_analysed_{branch}.root')
        if os.path.isfile(histfile):
            shutil.move(histfile, f'{validation_dir}/{histfile}')
            found_a_histfile = True
    #Get the stats of bad printouts
    # including writing the bad printouts information to the reference location
    badfile = rootfile.replace('.root', '_bad.txt')
    bads = {}
    with open(f'{validation_dir}/{badfile}', 'w') as f:
        for bad in ['GeomNav1002', 'Optical photon is killed because of missing refractive index']:
            bads[bad] = int(subprocess.run(['grep', '-c', bad, logfile], stdout=subprocess.PIPE, text=True).stdout)
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

def PushToGit(job_str, branch_name='new_ref', callnum=0):
    os.chdir(validation_dir)
    if not callnum:
        #setup default names, or git complains
        os.system('git config user.name "WCSim CI"')
        os.system('git config user.email "wcsim@wcsim.wcsim"')
    #fetch any changes from the remote
    os.system('git fetch origin')
    #merge in these changes from the remote
    print('Attempting to merge')
    os.system(f'git merge origin/{branch_name}')
    #save this hash, in case we need to reset back to it
    remote_hash = str(subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True).stdout)
    #make sure we're on correct branch
    # - gets the remote one, if it exists remotely
    # - otherwise makes a new branch locally, based on the default branch
    os.system(f'git checkout -b {branch_name} origin/{branch_name} --track || git checkout -b {branch_name}')
    #copy all our changes (except geofile - this comes later) to the right location
    for filenew in glob.glob(f'{validation_dir}/*_analysed_wcsimrootevent*.root'):
        shutil.copyfile(filenew, f'{validation_dir}/Compare/Reference/{filenew.rsplit("/",1)[-1]}')
    for filenew in glob.glob(f'{validation_dir}/*_bad.txt'):
        shutil.copyfile(filenew, f'{validation_dir}/Compare/Reference/{filenew.rsplit("/",1)[-1]}')
    #add all our changes
    os.system('git add Compare/')
    #commit
    print('Attempting commit of reference files (except geofiles)')
    os.system(f'git commit -m "CI reference update. Job(s): {job_str}"')
    #pull any remote changes
    # Need to account for conflicts in the geofile.txt
    #  This is done by not moving it to the correct place until after the pull
    # However all other files are unique to each job
    print('Attempting to git pull')
    subprocess.run(['git', 'pull', '--no-rebase', 'origin', branch_name])
    #Finally copy the geofile info to the new place
    for filenew in glob.glob(f'{validation_dir}/geofile_*.txt'):
        shutil.copyfile(filenew, f'{validation_dir}/Compare/Reference/{filenew.rsplit("/",1)[-1]}')
    #commit
    print('Attempting commit of geofile reference files')
    os.system(f'git commit {validation_dir}/Compare/Reference/geofile*.txt -m "CI reference update. Job(s): {job_str} geofile"')
    #now try push
    print('Attempting to git push')
    try:
        subprocess.run(['git', 'push', f'https://tdealtry:{os.environ["GitHubToken"]}@github.com/WCSim/Validation.git', branch_name], check=True)
    except KeyError:
        print("The $GitHubToken environment variable doesn't exist, so we can't git push. Giving up")
        return True
    except subprocess.CalledProcessError:
        print('push failed. Waiting 15 seconds before trying again')
        # Don't try forever
        #  100 calls x 15 seconds = 25 minutes
        if callnum > 100:
            print('Tried to push 100 times without success. Giving up')
            return True
        #if it didn't work, undo the last commit
        os.system(f'git reset --hard {remote_hash}')
        #clear the geofile changes
        os.system('git checkout Compare/Reference/geofile_*.txt')
        #have a rest before trying again
        time.sleep(15)
        PushToGit(job_str, branch_name, callnum=callnum+1)
    return False
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-number', '-j', type=int, nargs='+', required=True, choices=range(len(macs)), help='Job numbers to run.' + '\n'.join([f'{a:02d}: {b}' for a,b in zip(range(len(macs)), macs_short)]))
    parser.add_argument('--only-print-filename', action='store_true', help='Only prints the file number')
    args = parser.parse_args()

    jobs_to_run = sorted(set(args.job_number))
    failure = False
    for job in jobs_to_run:
        print(job, macs[job])
        if args.only_print_filename:
            continue
        if job == 0:
            GetSHA()
        failure = failure or MakeReference(job)

    if args.only_print_filename:
        sys.exit(0)
    #now all jobs have run, commit to the repo
    failure = failure or PushToGit(','.join([str(x) for x in jobs_to_run]))

    if failure:
        sys.exit(-1)
