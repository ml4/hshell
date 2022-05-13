#!/bin/bash
#
## script to output the runID of a workspace including plan runID
## usage:
#
##  while true; do sleep 1; ./hc-tfe-get-plan-runID.sh ml4-hc hc-net-main-dev|jq '.included[].id'; done
#
#########################################################################################################

function usage {
  echo "Usage: $(basename ${0}) <org> <workspace> <host>"
  echo "Host defaults to app.terraform.io"
  echo
  exit 1
}

function log {
  bldred="\033[0;31m" # Red
  bldgrn="\033[0;32m" # Green
  bldylw="\033[0;33m" # Yellow
  bldblu="\033[0;34m" # Blue
  bldpur="\033[0;35m" # Purple
  bldcyn="\033[0;36m" # Cyan
  bldwht="\033[0;37m" # White
  txtrst="\033[0m"    # Text Reset

  local -r level="$1"
  if [ "${level}" == "INFO" ]
  then
    COL=${bldgrn}
  elif [ "${level}" == "ERROR" ]
  then
    COL=${bldred}
  elif [ "${level}" == "WARN" ]
  then
    COL=${bldylw}
  fi

  local -r func="$2"
  local -r message="$3"
  local -r timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  >&2 echo -e "${bldcyn}${timestamp}${txtrst} [${COL}${level}${txtrst}] [${SCRIPT_NAME}:${func}] ${message}"
}

function main {
  org=${1}
  wksp=${2}
  host=${3}
  if [[ -z "${wksp}" ]]
  then
    usage
  fi
  if [[ -z "${host}" ]]
  then
    host='app.terraform.io'
  fi

  if [[ -z "${TFE_TOKEN}" ]]
  then
    TFE_TOKEN=$(cat ~/.terraform.d/credentials.tfrc.json|jq -r ".credentials.\"${host}\".token")
    if [[ -z "${TFE_TOKEN}" ]]
    then
      echo "TFE_TOKEN env var needs to be set, have been unable to automatically instantiate it"
    fi
  fi

  curl -sS \
    --header "Authorization: Bearer ${TFE_TOKEN}" \
    --header "Content-Type: application/vnd.api+json" \
    https://${host}/api/v2/organizations/${org}/workspaces/${wksp}?include=current_run.plan | jq
}

main "$@"