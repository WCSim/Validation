import os
import yaml
import json
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
        #this will fail if there are (somehow) multiple jobs in a single commit
        i = int(message.split('CI reference update. Job(s): ')[1])
        print(message)
        jobs_done.append(i)
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

command = 'python3.8 MakeReference.py --job {} --only-print-filename'.format(' '.join(map(str, jobs_missing)))
os.system(command)
