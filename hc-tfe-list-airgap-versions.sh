#!/bin/bash
#
## hc-tfe-list-airgap-versions.sh
## TFE air gap version list
#
## @straubt1, @ml4
#
#############################################################################################################################

set -eo pipefail

readonly SCRIPT_NAME="$(basename "${0}")"

function usage {
  echo -e "Usage:\n\n"
  echo -e "\t${SCRIPT_NAME}\n"
  echo -e "TFE_LICENSE_ID must be exported in your environment.  You will have been sent a link to the download from HashiCorp\n"
  echo -e "with a form like this: https://get.replicated.com/airgap/#/terraformenterprise/97a1c97db01041efefefefefefefefef?_k=5i5sdq\n so set this like so:"
  echo -e "export TFE_LICENSE_ID='97a1c97db01041efefefefefefefefef'\n"
  echo -e "TFE_AIRGAP_DOWNLOAD_PASSWD must also be exported in your environment.  You will have been sent this by HashiCorp e.g.:\n"
  echo -e "export TFE_AIRGAP_DOWNLOAD_PASSWD='LGHF4X'\n"

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
  elif [ "${level}" == "DIVIDE" ]
  then
    COL=${bldpur}
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
  if [[ -z "${TFE_LICENSE_ID}" ]]
  then
    log "ERROR" ${FUNCNAME[0]} "Please Set TFE_LICENSE_ID Environment Variable"
    usage
  fi

  if [[ -z "${TFE_AIRGAP_DOWNLOAD_PASSWD}" ]]
  then
    log "ERROR" ${FUNCNAME[0]} "Please Set TFE_AIRGAP_DOWNLOAD_PASSWD Environment Variable"
    usage
  fi

  b64_password=$(echo -n ${TFE_AIRGAP_DOWNLOAD_PASSWD} | base64)

  # Get all releases visit to this licence ID so we can pull the label
  all_releases=$(curl -s \
  -H "Authorization: Basic ${b64_password}" \
  -H "Accept: application/json" \
  "https://api.replicated.com/market/v1/airgap/releases?license_id=${TFE_LICENSE_ID}&show=all")
  rCode=${?}
  # echo $all_releases > all_releases.json

  ## List replicated sequence ID and TFE version label
  #
  if [[ ${rCode} == 0 ]]
  then
    if [[ ! ${all_releases} ]]
    then
      log "WARN" ${FUNCNAME[0]} "Curl of TFE release versions returned nothing.  Check licence ID or contact your customer success manager"
      exit 1
    fi
    log "INFO" ${FUNCNAME[0]} "Got all TFE versions visible to this licence ID"
    echo "Seq  TFE Version"
    echo ${all_releases} | jq -r '.releases[:50] | .[] | "\(.release_sequence)  \(.label)"'
  else
    log "ERROR" ${FUNCNAME[0]} "Curl of TFE release versions errored"
    exit ${rCode}
  fi
}

main "$@"
