import os
import yaml
import json
import sys
from pprint import pprint

#### GET THE COMMITS FROM THE LATEST PR

with open('commits') as json_data:
    data = json.load(json_data)

#pprint(data)
commits = data['commits']
jobs_done = []
for commit in commits:
    #pprint(commit)
    message = commit['messageHeadline']
    if message.startswith('Merge branch'):
        continue
    elif message.startswith('CI reference update. Job(s): '):
        #skip the geofile commits
        if message.endswith('geofile'):
            continue
        #this will fail if there are multiple jobs in a single commit
        # (Shouldn't happen on CI, can happen if running locally)
        try:
            i = int(message.split('CI reference update. Job(s): ')[1])
            jobs_done.append(i)
        #so catch multiple jobs. Thankfully they are just comma separated (no spaces)
        except ValueError:
            js = message.split('CI reference update. Job(s): ')[1].split(',')
            for j in js:
                jobs_done.append(int(j))
        print(message)
    else:
        print('UNKNOWN COMMIT MESSAGE:\n', message)
print()

jobs_done = sorted(jobs_done)
assert(len(jobs_done) == len(set(jobs_done)))


#### GET THE EXPECTED JOB NUMS
wcsimdir = os.environ['WCSIMDIR']
assert(os.path.isdir(wcsimdir))
wcsimfile = wcsimdir + '/.github/workflows/on_tag.yml'
assert(os.path.isfile(wcsimfile))
print('Taking expected jobs from:', wcsimfile)
with open(wcsimfile) as job:
    data = yaml.safe_load(job)
jobs_expected = sorted(data['jobs']['physics']['strategy']['matrix']['physics_job'])

#### PRINT STUFF
print()
print(len(jobs_done), 'jobs done:', jobs_done)
print(len(jobs_expected), 'jobs expe:', jobs_expected)

#### GET THE MISSING JOBS
jobs_missing = sorted(list(set(jobs_expected).difference(jobs_done)))
print(len(jobs_missing), 'jobs missing:', jobs_missing)
print()

if(not jobs_missing):
    sys.exit(0)

#### DECIDE TO RUN OR NOT
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--run', action='store_true', help='Run the missing jobs?')
args = parser.parse_args()

command = 'python3.8 MakeReference.py --job {} --only-print-filename'.format(' '.join(map(str, jobs_missing)))
if args.run:
    os.system(command)
else:
    print('Run this python script again with --run to automatically run MakeReference.py to run the missing jobs')
    print('Or just copy/paste the command:')
    print(command)
