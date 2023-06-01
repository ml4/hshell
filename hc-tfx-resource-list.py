#!/usr/bin/env python3
#
## hc-tfx-resource-list
#
## Originally by @richard-russell, modified by @ml4
#
## Retrieve workspace resource counts and output sorted list (most resources first)
## NB: skeleton code ... only checks for basic errors in responses
## Reads inputs from env vars or interactively
#
## ONLY TESTED ON TFC

from getpass import getpass
import os
import requests
import json

DEBUG     = False
QUIET     = False
PAGESIZE  = 100
TS_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

############################################################################
#
# Class: bcolors
#
############################################################################

## bcolors - used to provide more engaging output
#
class bcolors:
  Red      = '\033[0;31m'
  Green    = '\033[0;32m'
  Blue     = '\033[0;34m'
  Cyan     = '\033[0;36m'
  White    = '\033[0;37m'
  Yellow   = '\033[0;33m'
  Magenta  = '\033[0;35m'
  BRed     = '\033[1;31m'
  BGreen   = '\033[1;32m'
  BBlue    = '\033[1;34m'
  BCyan    = '\033[1;36m'
  BWhite   = '\033[1;37m'
  BYellow  = '\033[1;33m'
  BMagenta = '\033[1;35m'
  Grey     = '\033[90m'
  Default  = '\033[1;32m'
  Endc     = '\033[0m'
#
## End Class bcolors

############################################################################
#
# def env_or_ask
#
############################################################################

## check env vars or ask for input
#
def env_or_ask(var, sensitive=False):
    """Retrieve environment variable called 'var', and if it
       doesn't exist, prompt for it via interactive input,
       optionally using getpass if secure=True
    """
    value = os.getenv(var)
    if value is not None:
        return value
    if sensitive:
        return getpass(f'{var}: ')
    return input(f'{var}: ')

############################################################################
#
# def call_TFE
#
############################################################################

## call TFE and return json object
#
def call_TFE(QUIET, path):
  if not path:
    print(f'{bcolors.BRed}No TFE API in calling path{bcolors.Endc}')
    exit(1)

  if not QUIET:
    print(f'{bcolors.Magenta}Calling TFE with {path}{bcolors.Endc}')
    print()

  headers = {
    'Authorization': f'Bearer {TFE_TOKEN}',
    'Content-Type':  'application/vnd.api+json'
  }
  try:
    response = requests.get(f'{path}', headers=headers)
  except Exception as e:
    print()
    print(f'{bcolors.BRed}ERROR with requests to {path}:')
    print(e)
    print(f'{bcolors.Endc}')
    exit(1)

  ## handle response code
  #
  if response.status_code >= 400:
    print(f'{bcolors.BRed}API Request Response code: {response.status_code}')
  else:
    print(f'{bcolors.BMagenta}API Request Response code: {response.status_code}')

  ## detect output gzip file (which is the only type this script handles) or marshall
  #
  if response.status_code == 200:
    j = response.json()
  elif response.status_code >= 400:
    j = response.json()
    print()
    print(f'{bcolors.BYellow}{json.dumps(j)}{bcolors.Endc}')  # in order to put it out to https://codeamaze.com/web-viewer/json-explorer to make sense
    print()
    exit(response.status_code)

  data = j.get('data')
  links = j.get('links')
  if links is None:
      return data
  nextpage = links.get('next')
  # print(f'  nextpage -> {nextpage}')
  if nextpage is None:
      return data
  data.extend(call_TFE(QUIET, nextpage))
  return data
#
## End Func call_TFE

def main():
  global QUIET
  global TFE_ADDR
  global TFE_TOKEN
  global TFE_CACERT

  ## These variables are populated from environment variables if they exist, else prompt for input
  #
  TFE_ADDR  = env_or_ask('TFE_ADDR')
  TFE_ORG   = env_or_ask('TFE_ORG')
  TFE_TOKEN = env_or_ask('TFE_TOKEN', sensitive=True)

  workspaces_blob = call_TFE(QUIET, f'{TFE_ADDR}/api/v2/organizations/{TFE_ORG}/workspaces?page%5Bsize%5d={PAGESIZE}')
  wsresources = [ (ws['attributes']['name'], ws['attributes']['resource-count']) for ws in workspaces_blob ]
  wsr_sorted = sorted(wsresources, key=lambda x:x[0], reverse=False)

  print()
  total_resources = 0
  for ws, num_resources in wsr_sorted:
    print(f'{bcolors.Green}{ws}: {num_resources}')
    total_resources += num_resources
  print(f'\nTotal workspaces: {len(wsresources)}')
  print(f'{bcolors.BYellow}Total resources:  {total_resources}')
  print()

  # print()
  # print('name, resource-count')
  # for ws in wsr_sorted:
  #     print(f'{ws[0]}, {ws[1]}')

if __name__ == '__main__':
    main()
