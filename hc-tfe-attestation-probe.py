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
import os
import requests
import json

#import subprocess
#import re
#import random
#import signal
#import datetime
#import sys
#import glob

############################################################################
#
#   Globals
#
############################################################################

QUIET = False
TFE_ADDR = os.getenv('TFE_ADDR')
if not TFE_ADDR.startswith('https://') and not TFE_ADDR.startswith('http://'):
    TFE_ADDR = 'https://'+TFE_ADDR

TFE_TOKEN = os.getenv('TFE_TOKEN')
TFE_CACERT = os.getenv('TFE_CACERT')
rows, columns = os.popen('stty size', 'r').read().split()

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
# def line
#
############################################################################

## output a line the width of the terminal
#
def line():
  line = '#' * int(columns)
  print(line)
#
## End Func line

############################################################################
#
# def callTFE
#
############################################################################

## call TFE and return json object
#
def callTFE(QUIET, DEBUG, path):
  if not path:
    print(f'{bcolors.BRed}No TFE API in calling path{bcolors.Endc}')
    exit(1)

  if not QUIET and DEBUG:
    print(f'{bcolors.Magenta}Calling TFE with {TFE_ADDR}/api/v2{path}{bcolors.Endc}')
    print()

  headers = {
    'Authorization': f'Bearer {TFE_TOKEN}',
    'Content-Type':  'application/vnd.api+json'
  }
  r = requests.get(f'{TFE_ADDR}/api/v2{path}', headers=headers)
  j = r.json()
  if DEBUG:
    print(f'{json.dumps(j)}')  # in order to put it out to https://codeamaze.com/web-viewer/json-explorer to make sense
  return(j)
#
## End Func callVault

############################################################################
#
# def runReport
#
############################################################################

## perform initial tasks such as assess health
#
def runReport(QUIET, DEBUG, org):
  if not QUIET:
    line()
    print(f'{bcolors.Default}TFE Address:      {bcolors.BWhite}{TFE_ADDR}{bcolors.Endc}')
    print(f'{bcolors.Default}TFE CA Cert file: {bcolors.BWhite}{TFE_CACERT}{bcolors.Endc}')
    if DEBUG:
      print(f'{bcolors.Default}TFE Token:        {bcolors.BWhite}{TFE_TOKEN}{bcolors.Endc}')
    print()

  ## Initial workspace items
  #
  workspaces = {}
  workspaceblob = callTFE(QUIET, DEBUG, f'/organizations/{org}/workspaces')
  for array_obj in workspaceblob["data"]:
    workspaces[array_obj["attributes"]["name"]] = {
      'id':                  f'{array_obj["id"]}',
      'auto-apply':          f'{array_obj["attributes"]["auto-apply"]}',
      'created-at':          f'{array_obj["attributes"]["created-at"]}',
      'locked':              f'{array_obj["attributes"]["locked"]}',
      'speculative-enabled': f'{array_obj["attributes"]["speculative-enabled"]}',
      'terraform-version':   f'{array_obj["attributes"]["terraform-version"]}',
      'global-remote-state': f'{array_obj["attributes"]["global-remote-state"]}',
      'resource-count':      f'{array_obj["attributes"]["resource-count"]}',
    }
  for key in sorted(workspaces):
    print(f'{bcolors.Green}workspace.{bcolors.BGreen}Name:                {bcolors.BMagenta}{key}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.BGreen}ID:                  {bcolors.BCyan}{workspaces[key]["id"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.BGreen}TF Version:          {workspaces[key]["terraform-version"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.BGreen}Created:             {workspaces[key]["created-at"]}{bcolors.Endc}')
    if workspaces[key]["locked"] == "True":
      colour = f'{bcolors.BRed}'
    else:
      colour = f'{bcolors.BGreen}'
    print(f'{bcolors.Green}workspace.{bcolors.BGreen}Locked:              {colour}{workspaces[key]["locked"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.BGreen}Speculative Enabled: {workspaces[key]["speculative-enabled"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.BGreen}Global Remote State: {workspaces[key]["global-remote-state"]}{bcolors.Endc}')
    print(f'{bcolors.Green}workspace.{bcolors.BGreen}Resources in State:  {workspaces[key]["resource-count"]}{bcolors.Endc}')
    #
    ## Run data
    #
    runBlob = callTFE(QUIET, DEBUG, f'/workspaces/{workspaces[key]["id"]}/runs?page%5Bsize%5D=1')
    if len(runBlob["data"]) == 0:
      print(f'{bcolors.Green}run.{bcolors.BCyan}Previous:                  {bcolors.BYellow}No runs yet{bcolors.Endc}')
    else:
      print(f'{bcolors.Green}run.{bcolors.BCyan}Previous:                  {bcolors.BCyan}{runBlob["data"][0]["id"]}{bcolors.Endc}')
      if runBlob["data"][0]["attributes"]["canceled-at"]:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Canceled:                  {bcolors.BYellow}{runBlob["data"][0]["attributes"]["canceled-at"]}{bcolors.Endc}')
      else:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Canceled:                  {bcolors.BCyan}Not canceled{bcolors.Endc}')

      if runBlob["data"][0]["attributes"]["created-at"] is None:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Created:                   {bcolors.BYellow}Not Created{bcolors.Endc}')
      else:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Created:                   {bcolors.BCyan}{runBlob["data"][0]["attributes"]["created-at"]}{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Plan Queueable:            {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["plan-queueable-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Plan Queueable:            {bcolors.BYellow}Not Queueable{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Plan Queued:               {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["plan-queued-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Plan Queued:               {bcolors.BYellow}Not Queued{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Planning:                  {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["planning-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Planning:                  {bcolors.BYellow}Not Planned{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Planned:                   {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["planned-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Planned:                   {bcolors.BYellow}Not Planned{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Apply Queued:              {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["apply-queued-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Apply Queued:              {bcolors.BYellow}No Apply Queued{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Applying:                  {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["applying-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Applying:                  {bcolors.BYellow}Not Applied{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Confirmed:                 {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["confirmed-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Confirmed:                 {bcolors.BYellow}Not Confirmed{bcolors.Endc}')

      try:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Applied:                   {bcolors.BCyan}{runBlob["data"][0]["attributes"]["status-timestamps"]["applied-at"]}{bcolors.Endc}')
      except KeyError:
        print(f'{bcolors.Green}run.{bcolors.BCyan}Applied:                   {bcolors.BYellow}Not Applied{bcolors.Endc}')
    print()
  if not QUIET:
    print()

  # ## Get most recent workspace run
  # #
  # for key in sorted(workspaces):
  #   blob = callTFE(QUIET, f'/workspaces/{workspaces[key]["id"]}/runs?page%5Bsize%5D=1')
  #   #
  #   ## use array even though we only want the most recent run in case we start to iterate more than one run back
  #   #
  #   for array_obj in blob["data"]:
  #     workspaces[array_obj["id"]] = {
  #       'created-at':        f'{array_obj["attributes"]["created-at"]}',
  #       'plan-queueable-at': f'{array_obj["attributes"]["plan-queueable-at"]}',
  #       'plan-queued-at':    f'{array_obj["attributes"]["plan-queued-at"]}',
  #       'planning-at':       f'{array_obj["attributes"]["planning-at"]}',
  #       'planned-at':        f'{array_obj["attributes"]["planned-at"]}',
  #       'apply-queued-at':   f'{array_obj["attributes"]["apply-queued-at"]}',
  #       'applying-at':       f'{array_obj["attributes"]["applying-at"]}',
  #       'confirmed-at':      f'{array_obj["attributes"]["confirmed-at"]}',
  #       'applied-at':        f'{array_obj["attributes"]["applied-at"]}',
  #     }

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
    ## check env vars
    #
    if TFE_ADDR is None:
      print(f'{bcolors.BRed}ERROR: Please export TFE_ADDR as an environment variable in the form https://dev-tfe.hsbc.com{bcolors.Endc}')
      exit(1)

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


    ## need more time with argparse to work out how to improve this
    #
    # if not system and not namespace:
    #   print(f'{bcolors.BCyan}Start with:\n{bcolors.Endc}')
    #   print(f'{bcolors.BCyan}hc-vault-probe.py -h{bcolors.Endc}')
    #   exit(1)

    runReport(QUIET, DEBUG, org)
#
## End Func main

if __name__ == '__main__':
    main()
