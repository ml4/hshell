#!/bin/bash
#
## hc-tfe-list-replicated-versions.sh
## Replicated version list
#
#############################################################################################################################

set -eo pipefail

readonly SCRIPT_NAME="$(basename "${0}")"

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
  URL="https://release-notes.replicated.com"

  log "INFO" "${FUNCNAME[0]}" "Listing versions of Replicated available for download"
  curl -Ss ${URL} | grep blog-post-title | awk -F '>' '{print $2}' | awk -F '<' '{print $1}'
}

main "$@"
