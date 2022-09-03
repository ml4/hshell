#!/usr/bin/env python3
#
## hc-tfe-attestation.py
## 2022-05-24 ml4
## Automate the TFE API specifically for assessment of attestation of Sentinel soft mandatory overrides.
## This is to avoid using Audit Logging as it is a lagging indicator.
## NOTE: this software is provided AS-IS. No warrantee exists with this software.  Read and understand the code
## prior to running, and run in non-production prior to then running in production.
#
#######################################################################################################################

import argparse
import shutil
import os
import subprocess
import requests
import json
import zlib
import tarfile
import difflib

############################################################################
#
#   Globals
#
############################################################################

QUIET         = False
TFE_ADDR      = os.getenv('TFE_ADDR')
TFE_TOKEN     = os.getenv('TFE_TOKEN')
TFE_CACERT    = os.getenv('TFE_CACERT')
rows, columns = os.popen('stty size', 'r').read().split()

## /var/tmp used as CIS benchmarking compliance means /tmp noexec
#
tfeProbeTmpDir0  =  '/var/tmp/tfeProbeTmpDir0'
tfeProbeTmpDir1  =  '/var/tmp/tfeProbeTmpDir1'
cv0tgzPath       =  '/var/tmp/cv0blob.tgz'
cv1tgzPath       =  '/var/tmp/cv1blob.tgz'
sv0Path          = f'{tfeProbeTmpDir0}/sv0blob.json'
sv1Path          = f'{tfeProbeTmpDir1}/sv1blob.json'

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
# def drawLine
#
############################################################################

## output a line the width of the terminal
#
def drawLine():
  print(f'{bcolors.Default}')
  line = '#' * int(columns)
  print(line)
  print()
#
## End Func drawLine

############################################################################
#
# def handleDirectories
#
############################################################################

def handleDirectories(DEBUG, handle):
  if handle == 'create':
    for dir in [ tfeProbeTmpDir0, tfeProbeTmpDir1 ]:
      try:
        if DEBUG:
          drawLine()
          print(f'{bcolors.Magenta}Creating temporary directory: {dir}{bcolors.Endc}')
        os.mkdir(dir)
      except OSError as error:
        print()
        print(f'{bcolors.BRed}handleDirectories ERROR failed to {handle} {dir}:{bcolors.Endc}')
        print(error)
        exit(1)
  elif handle == 'delete':
    for dir in [ tfeProbeTmpDir0, tfeProbeTmpDir1 ]:
      try:
        if DEBUG:
          drawLine()
          print(f'{bcolors.Magenta}Deleting temporary directory: {dir}{bcolors.Endc}')
        shutil.rmtree(dir, ignore_errors = False)
      except OSError as error:
        print()
        print(f'{bcolors.BRed}handleDirectories ERROR failed to {handle} {dir}:{bcolors.Endc}')
        print(error)
        exit(1)
  else:
    print()
    print(f'{bcolors.BRed}handleDirectories ERROR internally: handle is {handle}{bcolors.Endc}')
    exit(1)
#
## End Func handleDirectories

############################################################################
#
# def callTFE
#
############################################################################

## call TFE and return json object
#
def callTFE(QUIET, DEBUG, path, downloadPath=''):
  if not path:
    print(f'{bcolors.BRed}No TFE API in calling path{bcolors.Endc}')
    handleDirectories(DEBUG, 'delete')
    exit(1)

  if not QUIET and DEBUG:
    print(f'{bcolors.Magenta}Calling TFE with {path}{bcolors.Endc}')
    print(f'{bcolors.Magenta}Download path:   {downloadPath}{bcolors.Endc}')
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
    handleDirectories(DEBUG, 'delete')
    exit(1)

  ## handle response code
  #
  if DEBUG:
    if response.status_code >= 400:
      print(f'{bcolors.BRed}API Request Response code: {response.status_code}')
    else:
      print(f'{bcolors.BMagenta}API Request Response code: {response.status_code}')

  ## detect output gzip file (which is the only type this script handles) or marshall
  #
  if response.status_code == 200:
    if not downloadPath or downloadPath == '':
      j = response.json()
      if DEBUG:
        print()
        print(f'{bcolors.BYellow}{json.dumps(j)}{bcolors.Endc}')  # in order to put it out to https://codeamaze.com/web-viewer/json-explorer to make sense
        print()
      return(j)
    elif downloadPath.endswith('tgz'):
      try:
        data = zlib.decompress(response.content, zlib.MAX_WBITS|32)
        with open(downloadPath,'wb') as outFile:
          outFile.write(data)
      except Exception as e:
        print()
        print(f'{bcolors.BRed}ERROR writing to {downloadPath}:')
        print(e)
        print(f'{bcolors.Endc}')
        handleDirectories(DEBUG, 'delete')
        exit(1)
      return('OK')
    elif downloadPath.endswith('json'):
      try:
        j = response.json()
        with open(downloadPath,'w') as outFile:
          outFile.write(json.dumps(j))
        if DEBUG:
          print(f'{bcolors.BGreen}DOWNLOADED STATE VERSION OK{bcolors.Endc}')
          print()
          print(f'{bcolors.BYellow}{json.dumps(j)}{bcolors.Endc}')  # in order to put it out to https://codeamaze.com/web-viewer/json-explorer to make sense
          print()
      except Exception as e:
        print()
        print(f'{bcolors.BRed}ERROR writing to {downloadPath}:')
        print(e)
        print(f'{bcolors.Endc}')
        handleDirectories(DEBUG, 'delete')
        exit(1)
  elif response.status_code >= 400:
    j = response.json()
    print()
    print(f'{bcolors.BYellow}{json.dumps(j)}{bcolors.Endc}')  # in order to put it out to https://codeamaze.com/web-viewer/json-explorer to make sense
    print()
    handleDirectories(DEBUG, 'delete')
    exit(response.status_code)
#
## End Func callTFE

############################################################################
#
# def runDiff
#
############################################################################

## Diff config or state; had probs with difflib output so dropped to CLI for brevity
#
def runDiff(QUIET, DEBUG, tfeProbeTmpDir0, tfeProbeTmpDir1, fileType=False):
  if fileType == "state":
    try:
      os.system(f'terraform state list -state={sv0Path} > {tfeProbeTmpDir0}/sv0blob.tfstate')
      with open(f'{tfeProbeTmpDir0}/sv0blob.tfstate', 'r') as file:
        sv0 = file.read()
      os.system(f'terraform state list -state={sv1Path} > {tfeProbeTmpDir1}/sv1blob.tfstate')
      with open(f'{tfeProbeTmpDir1}/sv1blob.tfstate', 'r') as file:
        sv1 = file.read()

      child = subprocess.run([f'diff -dabEBur {tfeProbeTmpDir0}/sv0blob.tfstate {tfeProbeTmpDir1}/sv1blob.tfstate'], capture_output=True, shell=True)
      output = str(child.stdout, 'utf-8')
      error  = str(child.stderr, 'utf-8')

      if output == '' and error == '':
        print(f'{bcolors.Green}config.{bcolors.BCyan}Configuration Changes:       {bcolors.BYellow}No difference{bcolors.Endc}')
      elif output != '' and error == '':
        print(f'{bcolors.Green}config.{bcolors.BCyan}Configuration Changes:{bcolors.BWhite}\n')
        print(f'{output}{bcolors.Endc}')
      elif error != '':
        print(f'{bcolors.BRed}ERROR: {error}')
        raise Exception
    except Exception as error:
      print(f'{bcolors.BRed}ERROR: Failed to diff state files {tfeProbeTmpDir0}/sv0blob.tfstate and {tfeProbeTmpDir1}/sv1blob.tfstate.{bcolors.Endc}. Exiting here')
      print(error)
      print(f'{bcolors.Endc}')
      handleDirectories(DEBUG, 'delete')
      exit(1)
  else:
    try:
      child = subprocess.run([f'diff -dabEBur {tfeProbeTmpDir0} {tfeProbeTmpDir1}'], capture_output=True, shell=True)
      output = str(child.stdout, 'utf-8')
      error  = str(child.stderr, 'utf-8')

      if output == '' and error == '':
        print(f'{bcolors.Green}config.{bcolors.BCyan}Configuration Changes:      {bcolors.BYellow}No difference{bcolors.Endc}')
      elif output != '' and error == '':
        print(f'{bcolors.Green}config.{bcolors.BCyan}Configuration Changes:{bcolors.BWhite}\n')
        print(f'{output}{bcolors.Endc}')
      elif error != '':
        print(f'{bcolors.BRed}ERROR: {error}')
        raise Exception
    except Exception as error:
      print(f'{bcolors.BRed}ERROR: Failed to diff configurations {tfeProbeTmpDir0} and {tfeProbeTmpDir1}.{bcolors.Endc}. Exiting here')
      print(error)
      print(f'{bcolors.Endc}')
      handleDirectories(DEBUG, 'delete')
      exit(1)
#
## End Func runDiff

############################################################################
#
# def runReport
#
############################################################################

## perform initial tasks such as assess health
#
def runReport(QUIET, DEBUG, org):
  if not QUIET:
    drawLine()
    print(f'{bcolors.Green}TFE.{bcolors.Default}Address:          {bcolors.BWhite}{TFE_ADDR}{bcolors.Endc}')
    print(f'{bcolors.Green}TFE.{bcolors.Default}CA Cert file:     {bcolors.BWhite}{TFE_CACERT}{bcolors.Endc}')
    if DEBUG:
      print(f'{bcolors.Green}TFE.{bcolors.Default}TFE Token:        {bcolors.BWhite}{TFE_TOKEN}{bcolors.Endc}')

  ## Get TFE version and ensure it is recent enough to download config versions
  #
  releaseBlob = callTFE(QUIET, DEBUG, f'{TFE_ADDR}/api/v2/admin/release')
  print(f'{bcolors.Green}TFE.{bcolors.Default}Release:          {bcolors.BMagenta}{releaseBlob["release"]}{bcolors.Endc}')
  print
  yearMonth = int(releaseBlob["release"][1:7])
  if yearMonth < 202203:
    print()
    print(f'{bcolors.BRed}ERROR: Your TFE release version ({releaseBlob["release"]}) needs to be >= 202203-1 in order to be able to download the configuration versions required to putative understand changes. Exiting here')
    handleDirectories(DEBUG, 'delete')
    exit(1)

  ## Initial workspace items
  #
  workspaces = {}
  workspaceBlob = callTFE(QUIET, DEBUG, f'{TFE_ADDR}/api/v2/organizations/{org}/workspaces')
  for array_obj in workspaceBlob["data"]:
    workspaces[array_obj["attributes"]["name"]] = {
      'id':                      f'{array_obj["id"]}',
      'auto-apply':              f'{array_obj["attributes"]["auto-apply"]}',
      'created-at':              f'{array_obj["attributes"]["created-at"]}',
      'locked':                  f'{array_obj["attributes"]["locked"]}',
      'speculative-enabled':     f'{array_obj["attributes"]["speculative-enabled"]}',
      'terraform-version':       f'{array_obj["attributes"]["terraform-version"]}',
      'global-remote-state':     f'{array_obj["attributes"]["global-remote-state"]}',
      'resource-count':          f'{array_obj["attributes"]["resource-count"]}',
      'can-read-state-versions': f'{array_obj["attributes"]["permissions"]["can-read-state-versions"]}'
    }
  for key in sorted(workspaces):
    if not QUIET:
      drawLine()
    print(f'{bcolors.Green}workspace.{bcolors.Default}Name:                    {bcolors.BMagenta}{key}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.Default}ID:                      {bcolors.BCyan}{workspaces[key]["id"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.Default}TF Version:              {workspaces[key]["terraform-version"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.Default}Created:                 {workspaces[key]["created-at"]}{bcolors.Endc}')
    if workspaces[key]["locked"] == "True":
      colour = f'{bcolors.BRed}'
    else:
      colour = f'{bcolors.Default}'
    print(f'{bcolors.Green}workspace.{bcolors.Default}Locked:                  {colour}{workspaces[key]["locked"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.Default}Speculative Enabled:     {workspaces[key]["speculative-enabled"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.Default}Global Remote State:     {workspaces[key]["global-remote-state"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.Default}Resources in State:      {workspaces[key]["resource-count"]}{bcolors.Endc}')
    #
    ## Run data
    #
    runBlob = callTFE(QUIET, DEBUG, f'{TFE_ADDR}/api/v2/workspaces/{workspaces[key]["id"]}/runs?page%5Bsize%5D=1')
    if len(runBlob["data"]) == 0:
      print(f'{bcolors.Green}run.{bcolors.BCyan}Last Run:                      {bcolors.BYellow}No runs yet{bcolors.Endc}')
    else:
      print(f'{bcolors.Green}run.{bcolors.BCyan}Last Run:                      {bcolors.BCyan}{runBlob["data"][0]["id"]}{bcolors.Endc}')
      if runBlob["data"][0]["relationships"]["created-by"]["data"]["id"]:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Created by:                    {bcolors.BBlue}{runBlob["data"][0]["relationships"]["created-by"]["data"]["id"]}{bcolors.Endc}')
      else:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Created by:                    {bcolors.BRed}No user found!{bcolors.Endc}')

      # if runBlob["data"][0]["relationships"]["configuration-version"]["data"]["id"]:
      #   print(f'{bcolors.Green}run.{bcolors.BCyan}Configuration Version:        {bcolors.BBlue}{runBlob["data"][0]["relationships"]["configuration-version"]["data"]["id"]}{bcolors.Endc}')
      # else:
      #   print(f'{bcolors.Green}run.{bcolors.BCyan}Configuration Version:        {bcolors.BRed}No configuration version found!{bcolors.Endc}')
      #
      ## if we have a configuration that begins with 'cv', hit the API again and get the configuration version data:
      ##   - as we have a configuration version, get a list of configuration versions and ensure there are at least two
      ##   - get the previous configuration version
      ##   - show both configuration versions = get links to the blobs containing the configuration data
      ##   - get each blob
      ##   - diff the blobs and output






      ## outstanding: if there is only one version, then there is no need to do a diff







      #
      try:
        if runBlob["data"][0]["relationships"]["configuration-version"]["data"]["id"].startswith("cv-"):
          cvListBlob = callTFE(QUIET, DEBUG, f'{TFE_ADDR}/api/v2/workspaces/{workspaces[key]["id"]}/configuration-versions')

          if len(cvListBlob) == 0:
            print(f'{bcolors.BRed}ERROR: Configuration version list blob is empty, but configuration version {runBlob["data"][0]["relationships"]["configuration-version"]["data"]["id"]} detected.{bcolors.Endc}. Exiting here')
            handleDirectories(DEBUG, 'delete')
            exit(1)
          elif len(cvListBlob) == 1:
            firstCV = True  # see below when we diff the blobs
          else:
            multipleCV = True
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Configuration Versions:        {bcolors.BRed}List Not Found{bcolors.Endc}')

      if multipleCV == True:
        # OK we have >1 configuration versions: get the second one in the array (1) - we already have element 0, but check
        if runBlob["data"][0]["relationships"]["configuration-version"]["data"]["id"] != cvListBlob["data"][0]["id"]:
          print(f'{bcolors.BRed}ERROR: Configuration version ({runBlob["data"][0]["relationships"]["configuration-version"]["data"]["id"]}) is different from element 0 in the configuration versions blob ({cvListBlob["data"][0]["id"]}).{bcolors.Endc}. Exiting here')
          handleDirectories(DEBUG, 'delete')
          exit(1)
        cv0 = cvListBlob["data"][0]["id"]
        cv0download = cvListBlob["data"][0]["links"]["download"]
        cv1 = cvListBlob["data"][1]["id"]
        cv1download = cvListBlob["data"][1]["links"]["download"]

        if cv0 and cv0download and cv1 and cv1download:
          print(f'{bcolors.Green}run.{bcolors.BCyan}Latest Config Version ID:      {bcolors.BBlue}{cv0}{bcolors.Endc}')
          print(f'{bcolors.Green}run.{bcolors.BCyan}Latest Config Version Path:    {bcolors.BCyan}{cv0download}{bcolors.Endc}')
          print(f'{bcolors.Green}run.{bcolors.BCyan}Previous Config Version ID:    {bcolors.BBlue}{cv1}{bcolors.Endc}')
          print(f'{bcolors.Green}run.{bcolors.BCyan}Previous Config Version Path:  {bcolors.BCyan}{cv1download}{bcolors.Endc}')

        cv0blobDownloadCheck = callTFE(QUIET, DEBUG, f'{TFE_ADDR}/api/v2/configuration-versions/{cv0}/download', cv0tgzPath)
        if cv0blobDownloadCheck != 'OK':
          print(f'{bcolors.BRed}ERROR: Download configuration version 0 {cv0} failed.{bcolors.Endc}. Exiting here')
          handleDirectories(DEBUG, 'delete')
          exit(1)
        cv1blobDownloadCheck = callTFE(QUIET, DEBUG, f'{TFE_ADDR}/api/v2/configuration-versions/{cv1}/download', cv1tgzPath)
        if cv0blobDownloadCheck != 'OK':
          print(f'{bcolors.BRed}ERROR: Download configuration version 0 {cv0} failed.{bcolors.Endc}. Exiting here')
          handleDirectories(DEBUG, 'delete')
          exit(1)

        ## untar both tgz files and diff
        #
        try:
          cv0tgzFH = tarfile.open(cv0tgzPath)
        except Exception as error:
          print(f'{bcolors.BRed}ERROR: Failed to open tar file {cv0tgzPath}.{bcolors.Endc}. Exiting here')
          print(error)
          print(f'{bcolors.Endc}')
          handleDirectories(DEBUG, 'delete')
          exit(1)
        try:
          cv1tgzFH = tarfile.open(cv1tgzPath)
        except Exception as error:
          print(f'{bcolors.BRed}ERROR: Failed to open tar file {cv1tgzPath}.{bcolors.Endc}. Exiting here')
          print(error)
          print(f'{bcolors.Endc}')
          handleDirectories(DEBUG, 'delete')
          exit(1)

        ## extract dumps
        #
        try:
          cv0tgzFH.extractall(tfeProbeTmpDir0)
          cv0tgzFH.close()
        except FileExistsError as error:
          print(f'{bcolors.BRed}ERROR: Failed to extract configuration tar file {cv0tgzPath}.{bcolors.Endc}. Exiting here')
          print(error)
          print(f'{bcolors.Endc}')
          handleDirectories(DEBUG, 'delete')
          exit(1)

        try:
          cv1tgzFH.extractall(tfeProbeTmpDir1)
          cv1tgzFH.close()
        except FileExistsError as error:
          print(f'{bcolors.BRed}ERROR: Failed to extract configuration tar file {cv1tgzPath}.{bcolors.Endc}. Exiting here')
          print(error)
          print(f'{bcolors.Endc}')
          handleDirectories(DEBUG, 'delete')
          exit(1)

        try:
          os.remove(cv0tgzPath)
          os.remove(cv1tgzPath)
        except Exception as error:
          print(f'{bcolors.BRed}ERROR: Failed to remove configuration tar files {cv0tgzPath} and {cv1tgzPath}.{bcolors.Endc}. Exiting here')
          print(error)
          print(f'{bcolors.Endc}')
          handleDirectories(DEBUG, 'delete')
          exit(1)

        ## diff dirs
        #
        runDiff(QUIET, DEBUG, tfeProbeTmpDir0, tfeProbeTmpDir1)

        ## empty dirs in case we diff state versions below
        #
        for dir in [ tfeProbeTmpDir0, tfeProbeTmpDir1 ]:
          try:
            if DEBUG:
              drawLine()
              print(f'{bcolors.Magenta}Emptying temporary directory: {dir}{bcolors.Endc}')
            for root, dirs, files in os.walk(dir):
              for file in files:
                  os.remove(os.path.join(root, file))
          except OSError as error:
            print()
            print(f'{bcolors.BRed}ERROR: failed to empty temporary dir {emptyPath}:{bcolors.Endc}')
            print(error)
            handleDirectories(DEBUG, 'delete')
            exit(1)

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Canceled:                      {bcolors.BYellow}{runBlob["data"][0]["attributes"]["canceled-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Canceled:                      {bcolors.BCyan}Not canceled{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Created:                       {bcolors.BCyan}{runBlob["data"][0]["attributes"]["created-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Created:                       {bcolors.BYellow}Not Created{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Plan Queueable:                {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["plan-queueable-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Plan Queueable:                {bcolors.BYellow}Not Queueable{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Plan Queued:                   {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["plan-queued-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Plan Queued:                   {bcolors.BYellow}Not Queued{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Planning:                      {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["planning-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Planning:                      {bcolors.BYellow}Not Planned{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Planned:                       {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["planned-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Planned:                       {bcolors.BYellow}Not Planned{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Apply Queued:                  {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["apply-queued-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Apply Queued:                  {bcolors.BYellow}No Apply Queued{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Applying:                      {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["applying-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Applying:                      {bcolors.BYellow}Not Applied{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Confirmed:                     {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["confirmed-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Confirmed:                     {bcolors.BYellow}Not Confirmed{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Applied:                       {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["applied-at"]}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Applied:                       {bcolors.BYellow}Not Applied{bcolors.Endc}')

      try:
        if runBlob["data"][0]["attributes"]["status"] == "applied":
          print(f'{bcolors.Green}run.{bcolors.BCyan}Status (Outcome):              {bcolors.Default}applied{bcolors.Endc}')
        else:
          print(f'{bcolors.Green}run.{bcolors.BCyan}Status (Outcome):              {bcolors.BYellow}{runBlob["data"][0]["attributes"]["status"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Status (Outcome):              {bcolors.BRed}UNKNOWN{bcolors.Endc}')
      #
      ## If state changed then diff from the previous run - essentially repeat the equivalent from the configuration version diffs from above
      #
      try:
        if workspaces[key]["can-read-state-versions"] == "True":
          #
          ## Use the State Versions API rather than the workspaces API because it has everything we need for this section in it
          #
          stateVersionsBlob = callTFE(QUIET, DEBUG, f'{TFE_ADDR}/api/v2/state-versions?filter%5Bworkspace%5D%5Bname%5D={key}&filter%5Borganization%5D%5Bname%5D={org}')
      except KeyError:
        print(f'{bcolors.BRed}ERROR: Cannot find permission can-read-state-versions yet there is data in /organizations/{org}/workspaces API call. Probably a mishandling in the script. Exiting here')
        print(error)
        print(f'{bcolors.Endc}')
        handleDirectories(DEBUG, 'delete')
        exit(1)

      ## state data
      ## if we have a state version that begins with 'sv', hit the API again and get the state version data:
      ##   - as we have a state version, get a list of state versions and ensure there are at least two
      ##   - get the previous configuration version
      ##   - show both configuration versions = get links to the blobs containing the configuration data
      ##   - get each blob
      ##   - diff the blobs and output
      ##   - if there is only one state version in the history, no need to do a diff
      #
      try:
        if stateVersionsBlob["data"][0]["id"] and stateVersionsBlob["data"][0]["id"].startswith("sv-"):
          print(f'{bcolors.Green}state.{bcolors.BCyan}Latest State Version ID:     {bcolors.BBlue}{stateVersionsBlob["data"][0]["id"]}{bcolors.Endc}')
          # print(f'{bcolors.Green}state.{bcolors.BCyan}Latest State Version Path:   {bcolors.BCyan}{stateVersionsBlob["data"][0]["attributes"]["hosted-state-download-url"]}{bcolors.Endc}')
          print(f'{bcolors.Green}state.{bcolors.BCyan}Latest State Version S/N:    {bcolors.BCyan}{stateVersionsBlob["data"][0]["attributes"]["serial"]}{bcolors.Endc}')
      except KeyError:
          print(f'{bcolors.Green}state.{bcolors.BCyan}Latest Version:              {bcolors.BYellow}No Latest State Version{bcolors.Endc}')

      try:
        if stateVersionsBlob["data"][1]["id"]:
          print(f'{bcolors.Green}state.{bcolors.BCyan}Previous State Version ID:   {bcolors.BBlue}{stateVersionsBlob["data"][1]["id"]}{bcolors.Endc}')
          # print(f'{bcolors.Green}state.{bcolors.BCyan}Previous State Version Path: {bcolors.BCyan}{stateVersionsBlob["data"][1]["attributes"]["hosted-state-download-url"]}{bcolors.Endc}')
          print(f'{bcolors.Green}state.{bcolors.BCyan}Previous State Version S/N:  {bcolors.BCyan}{stateVersionsBlob["data"][1]["attributes"]["serial"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}state.{bcolors.BCyan}Previous Version:            {bcolors.BYellow}No Previous State Version{bcolors.Endc}')

  if not QUIET:
    print()
#
## End Func runReport

############################################################################
#
# def MAIN
#
############################################################################

#    #   ##   # #    #
##  ##  #  #  # ##   #
# ## # #    # # # #  #
#    # ###### # #  # #
#    # #    # # #   ##
#    # #    # # #    #

## Main
#
def main():
    global QUIET
    global TFE_ADDR
    global TFE_TOKEN
    global TFE_CACERT

    ## check env vars
    #
    if TFE_ADDR is None:
      print(f'{bcolors.BRed}ERROR: Please export TFE_ADDR as an environment variable in the form https://dev-tfe.mydomain.com{bcolors.Endc}')
      exit(1)

    if not TFE_ADDR.startswith('https://') and not TFE_ADDR.startswith('http://'):
      TFE_ADDR = 'https://'+TFE_ADDR

    if TFE_TOKEN is None:
      print(f'{bcolors.BRed}ERROR: Please export TFE_TOKEN as an environment variable{bcolors.Endc}')
      exit(1)

    if TFE_CACERT is None:
      print(f'{bcolors.BRed}ERROR: Please export local path to TFE_CACERT as an environment variable{bcolors.Endc}')
      exit(1)

    ## create parser
    #
    parser = argparse.ArgumentParser(
        description=f'HashiCorp Terraform Enterprise probe, for convenient iteration of enterprise namespaces for rudimentary reporting',
        formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=80, width=130)
    )
    optional = parser._action_groups.pop()

    org   = parser.add_argument_group('Handle TFE organisations')
    quiet = parser.add_argument_group('Hide dressing for better pipeline work')
    debug = parser.add_argument_group('Add outputs of debug information')

    ## add arguments to the parser
    #
    org.add_argument('-o', '--org', type=str, help='Specify the organisation in TFE to use')
    quiet.add_argument('-q', '--quiet',         action='store_true', help='Hide extraneous output')
    debug.add_argument('-d', '--debug',         action='store_true', help='Output debug output')

    parser._action_groups.append(optional)

    ## parse
    #
    arg = parser.parse_args()

    if arg.quiet:
      QUIET = True
    else:
      QUIET = False

    if arg.debug:
      DEBUG = True
    else:
      DEBUG = False

    if arg.org:
      org = arg.org
    else:
      print(f'{bcolors.BRed}ERROR: Please supply an org name with -o{bcolors.Endc}')
      exit(1)

    ## handle temporary directories and call
    #
    handleDirectories(DEBUG, 'create')
    runReport(QUIET, DEBUG, org)
    handleDirectories(DEBUG, 'delete')
#
## End Func main

if __name__ == '__main__':
    main()
