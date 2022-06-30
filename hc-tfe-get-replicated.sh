#!/bin/bash
#
## hc-tfe-get-replicated-versions.sh
## Replicated version list
#
#############################################################################################################################

set -eo pipefail

readonly SCRIPT_NAME="$(basename "${0}")"

function usage {
  echo -e "Usage:\n\n"
  echo -e "\t${SCRIPT_NAME} <version>\n"
  echo -e "where version is a Replicated semver e.g. 2.52.3"
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
  version=$1
  [[ -z "$version" ]] && usage

  url="https://s3.amazonaws.com/replicated-airgap-work/stable/replicated-${version}%2B${version}%2B${version}.tar.gz"
  filename="replicated-${version}.tar.gz"

  log "INFO" "${FUNCNAME[0]}" "Accessing Replicated:"
  log "INFO" "${FUNCNAME[0]}" "  Version: ${version}"
  log "INFO" "${FUNCNAME[0]}" "  URL: ${url}"
  log "INFO" "${FUNCNAME[0]}" "  Filename: ${filename}"

  curl -L#o ${filename} ${url}
  rCode=${?}
  if [[ ${rCode} > 0 ]]
  then
    log "ERROR" "${FUNCNAME[0]}" "Problem with the cURL command. Stopping"
    exit ${rCode}
  else
    log "INFO" "${FUNCNAME[0]}" "Download of ${filename} succeeded."
  fi
}

main "$@"
