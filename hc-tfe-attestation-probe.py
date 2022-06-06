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
def callTFE(QUIET, path):
  if not path:
    print(f'{bcolors.BRed}No TFE API in calling path{bcolors.Endc}')
    exit(1)

  if not QUIET:
   print(f'{bcolors.BCyan}Calling TFE with {TFE_ADDR}/api/v2{path}{bcolors.Endc}')

  headers = {
    'Authorization': f'Bearer {TFE_TOKEN}',
    'Content-Type':  'application/vnd.api+json'
  }
  r = requests.get(f'{TFE_ADDR}/api/v2{path}', headers=headers)
  json = r.json()
  return(json)
#
## End Func callVault

############################################################################
#
# def initTasks
#
############################################################################

## perform initial tasks such as assess health
#
def initTasks(QUIET, org):
  if not QUIET:
    line()
    print(f'{bcolors.Default}TFE Address: {bcolors.BWhite}{TFE_ADDR}{bcolors.Endc}')
    print(f'{bcolors.Default}TFE Token: {bcolors.BWhite}{TFE_TOKEN}{bcolors.Endc}')
    print(f'{bcolors.Default}TFE CA Cert file: {bcolors.BWhite}{TFE_CACERT}{bcolors.Endc}')
    print()

  ## runs
  #
  workspaces = callTFE(QUIET, f'/organizations/{org}/workspaces')
  # print(f'{workspaces}')
  for all in workspaces:
    for workspace in all:
      print(f'{bcolors.Green}workspaces.{bcolors.BGreen}Workspace: {workspace}{bcolors.Endc}')
  # print(f'{bcolors.Green}health.{bcolors.Default}Initialised:     {bcolors.BWhite}{health["initialized"]}{bcolors.Endc}')
  if not QUIET:
    print()

#
## End Func initTasks

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
      print(f'{bcolors.BRed}ERROR: Please export TFE_ADDR as an environment variable{bcolors.Endc}')
      exit(1)

    if TFE_TOKEN is None:
      print(f'{bcolors.BRed}ERROR: Please export TFE_TOKEN as an environment variable{bcolors.Endc}')
      exit(1)

    if TFE_CACERT is None:
      print(f'{bcolors.BRed}ERROR: Please export TFE_CACERT as an environment variable{bcolors.Endc}')
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

    ## add arguments to the parser
    #
    org.add_argument('-o', '--org', type=str, help='Specify the organisation in TFE to use')

    # org.add_argument('-s', '--system',       action='store_true', help='Output information about the system as a whole, not namespaces-level information')

    quiet.add_argument('-q', '--quiet',         action='store_true', help='Hide extraneous output')

    parser._action_groups.append(optional)

    ## parse
    #
    arg = parser.parse_args()

    if arg.quiet:
      QUIET = True
    else:
      QUIET = False

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

    initTasks(QUIET, org)
#
## End Func main

if __name__ == '__main__':
    main()
