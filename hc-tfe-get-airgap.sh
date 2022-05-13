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
  echo -e "Usage:\n"
  echo -e "\t${SCRIPT_NAME} <release>\n"
  echo -e "where <release> is the release sequence of the application to download for example 534."
  echo -e "\n* TFE_LICENSE_ID must be exported in your environment.  You will have been sent a link to the download from HashiCorp"
  echo -e "with a form like this:\thttps://get.replicated.com/airgap/#/terraformenterprise/97a1c97db01041efefefefefefefefef?_k=5i5sdq\nso set this with:\texport TFE_LICENSE_ID='97a1c97db01041efefefefefefefefef'"
  echo -e "\n* TFE_AIRGAP_DOWNLOAD_PASSWD must also be exported in your environment.\nYou will have been sent this by HashiCorp e.g.:\texport TFE_AIRGAP_DOWNLOAD_PASSWD='LGHF4X'"

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
  release_sequence=${1}

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

  if [[ -z "${release_sequence}" ]]
  then
    log "ERROR" ${FUNCNAME[0]} "Please provide a release sequence number"
    usage
  fi

  b64_password=$(echo -n ${TFE_AIRGAP_DOWNLOAD_PASSWD} | base64)

  ## Get all releases so we can pull the label
  #
  response=$(curl -s \
  -H "Authorization: Basic ${b64_password}" \
  -H "Accept: application/json" \
  --write-out " %{http_code}" \
  "https://api.replicated.com/market/v1/airgap/releases?license_id=${TFE_LICENSE_ID}&show=all")
  rCode=$(echo ${response} | awk '{print $NF}')
  if [[ "${rCode}" != "200" ]]
  then
    log "ERROR" ${FUNCNAME[0]} "Curl to access sequence number list errored with code ${rCode}"
    exit ${rCode}
  else
    ## Cut the return code
    #
    all_releases=$(echo ${response} | awk '{$NF=""; print $0}')
  fi

  ## Get the specific release airgap so we can get the generated URL
  #
  response=$(curl -s \
  -H "Authorization: Basic ${b64_password}" \
  -H "Accept: application/json" \
  --write-out " %{http_code}" \
  "https://api.replicated.com/market/v1/airgap/images/url?license_id=${TFE_LICENSE_ID}&sequence=${release_sequence}")
  rCode=$(echo ${response} | awk '{print $NF}')
  if [[ "${rCode}" != "200" ]]
  then
    log "ERROR" ${FUNCNAME[0]} "Curl to access specific sequence number errored with code ${rCode}"
    exit ${rCode}
  else
    replicated_release=$(echo ${response} | awk '{$NF=""; print $0}')
    log "INFO" ${FUNCNAME[0]} "Got Replicated release"
  fi

  ## Get label from releases
  #
  label=$(echo ${all_releases} | jq -r ".releases[] | select(.release_sequence == ${release_sequence}) | .label")
  if [[ -z "${label}" ]]
  then
    log "ERROR" ${FUNCNAME[0]} "TFE release sequence not found"
    exit 1
  fi

  url=$(echo ${replicated_release} | jq -r '.url')
  if [[ -z "${url}" ]]
  then
    log "ERROR" ${FUNCNAME[0]} "TFE download URL is empty"
    exit 1
  fi

  filename="tfe_${label}_${release_sequence}.airgap"

  log "INFO" ${FUNCNAME[0]} "Found TFE release:"
  log "INFO" ${FUNCNAME[0]} "Sequence: ${release_sequence}"
  log "INFO" ${FUNCNAME[0]} "Label: ${label}"
  log "INFO" ${FUNCNAME[0]} "URL: ${url}"
  log "INFO" ${FUNCNAME[0]} "Filename: ${filename}"

  curl -#o ${filename} ${url}
  rCode=${?}
  if [[ ${rCode} > 0 ]]
  then
    log "ERROR" ${FUNCNAME[0]} "Curl to download TFE airgap errored"
    exit ${rCode}
  fi
}

main "$@"
