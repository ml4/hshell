#!/usr/bin/env bash
#
## hc-tfe-api.sh
#
## Example script to summarises the cURL commands required to enact various tasks on TFE.
## NOTE: insufficient checking of integrity of variables after commands are run to instantiate them is
##       done - this script is expected to just illustrate API workflow concepts pursuant to being translated
##       into the same or different language ready for production work.
#
#############################################################################################################

readonly SCRIPT_NAME="$(basename "${0}")"
UPLOAD_FILE_NAME="/tmp/content-$(date +%s).tar.gz"
CREATE_CONFIG_VERSION="/tmp/create_config_version.json"
echo '{"data":{"type":"configuration-versions"}}' > ${CREATE_CONFIG_VERSION}

# export TFE_ADDR=https://my-tfe.company.com
# export TFE_TOKEN=9LexxxxxxxxNs7Q.atlasv1.66pyyeLxCxxx66pyyeLxCxxx66pyyeLxCxxx66pyyeLxCxxxAo
# export TFE_CACERT=/path/to/CACERT.pem
# export TFE_ORG=aeoa
# export TFE_WORKSPACE=workspace1
# export TFE_CONTENT_DIR=.

# The sections below divide cURL commands into logical sets pertaining to specific tasks
# Read these links before proceeding:
# - https://www.terraform.io/cloud-docs/run/api
# - https://www.terraform.io/cloud-docs/api-docs

function usage {
  echo "Usage: $(basename ${0}) <op>"
  echo "Need to ensure the env vars are exported in your shell for the script to work (except the token)"
  echo
  exit 1
}

function handle_resp {
  resp_body="$(printf '%s' "$1" | awk '!/^http_code/; /^http_code/{next}')"
  resp_code="$(printf '%s' "$1" | awk '!/^http_code/{next} /^http_code/{print $2}')"
  case "${resp_code}" in
    2*)
      log "INFO" "${FUNCNAME[0]}" "${resp_code}: SUCCESS"
      ;;
    4*|5*)
      log "ERROR" "${FUNCNAME[0]}" "${resp_code}"
      echo "${resp_body}"
      exit 1
      ;;
    *)
      echo "unknown response"
      log "ERROR" "${FUNCNAME[0]}" "${resp_code}"
      echo "${resp_body}"
      exit 1
      ;;
  esac
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

function terraform_plan {
  log "INFO" "${FUNCNAME[0]}" "Running ${op}"

  log "INFO" "${FUNCNAME[0]}" "tar -zcf "${UPLOAD_FILE_NAME}" ."
  tar -zcf "${UPLOAD_FILE_NAME}" .

  ## Get the workspace ID from the name
  #
  log "INFO" "${FUNCNAME[0]}" "Getting workspace ID for workspace ${TFE_WORKSPACE}"
  WORKSPACE_ID=($(curl -sS\
    --header "Authorization: Bearer ${TFE_TOKEN}" \
    --header "Content-Type: application/vnd.api+json" \
    https://${TFE_ADDR}/api/v2/organizations/${TFE_ORG}/workspaces/${TFE_WORKSPACE} \
    | jq -r '.data.id'))
  rCode=${?}
  if [[ -z "${WORKSPACE_ID}" ]]
  then
    log "ERROR"  "No response from curl command. Running again without silent"
    curl \
      --header "Authorization: Bearer ${TFE_TOKEN}" \
      --header "Content-Type: application/vnd.api+json" \
      https://${TFE_ADDR}/api/v2/organizations/${TFE_ORG}/workspaces/${TFE_WORKSPACE} \
      | jq -r '.data.id'
    exit 1
  fi
  log "INFO" "${FUNCNAME[0]}" "Workspace ID: ${WORKSPACE_ID}"

  log "INFO" "${FUNCNAME[0]}" "Running |curl -sS --header \"Authorization: Bearer ${TFE_TOKEN}\" --header \"Content-Type: application/vnd.api+json\" --request POST --data @${CREATE_CONFIG_VERSION} https://${TFE_ADDR}/api/v2/workspaces/${WORKSPACE_ID}/configuration-versions | jq -r '.data.attributes.\"upload-url\"')|"
  UPLOAD_URL="$(curl -sS\
    --header "Authorization: Bearer ${TFE_TOKEN}" \
    --header "Content-Type: application/vnd.api+json" \
    --request POST \
    --data @${CREATE_CONFIG_VERSION} \
    https://${TFE_ADDR}/api/v2/workspaces/${WORKSPACE_ID}/configuration-versions \
    | jq -r '.data.attributes."upload-url"')"
  rCode=${?}
  if [[ -z "${UPLOAD_URL}" ]]
  then
    log "ERROR"  "No response from curl command. Running again without silent"
    curl \
      --header "Authorization: Bearer ${TFE_TOKEN}" \
      --header "Content-Type: application/vnd.api+json" \
      --request POST \
      --data @${CREATE_CONFIG_VERSION} \
      https://${TFE_ADDR}/api/v2/workspaces/${WORKSPACE_ID}/configuration-versions \
      | jq -r '.data.attributes."upload-url"'
    exit 1
  fi
  log "INFO" "${FUNCNAME[0]}" "Upload URL: ${UPLOAD_URL}"

  ## upload config version to the server to trigger a plan. if workspace is set to auto-apply, TFE will also attempt that
  ## or one can be manually triggered - see below in the terraform_apply function
  #
  response=$(curl -sSw '\nhttp_code: %{http_code}\n' --header "Content-Type: application/octet-stream" --request PUT --data-binary @"${UPLOAD_FILE_NAME}" ${UPLOAD_URL})
  handle_resp "${response}"
}

function main {
  op=${1}
  pushd ${TFE_CONTENT_DIR}
  rCode=${?}
  if [[ ${rCode} > 0 ]]
  then
    log "ERROR" "${FUNCNAME[0]}" "cd ${TFE_CONTENT_DIR} failed with return code: |${rCode}|"
    exit 1
  fi

  if [[ -z "${TFE_ADDR}" || "${TFE_ADDR}" =~ ^http ]]
  then
    log "ERROR" "${FUNCNAME[0]}" "TFE_ADDR is not set or set with protocol in front (just put the fqdn of the server in)"
    exit 1
  fi

  if [[ -z "${TFE_CACERT}" ]]
  then
    log "ERROR" "${FUNCNAME[0]}" "TFE_CACERT is not set"
    exit 1
  fi

  if [[ -z "${TFE_ORG}" ]]
  then
    log "ERROR" "${FUNCNAME[0]}" "TFE_ORG is not set"
    exit 1
  fi

  if [[ -z "${TFE_WORKSPACE}" ]]
  then
    log "ERROR" "${FUNCNAME[0]}" "TFE_WORKSPACE is not set"
    exit 1
  fi

  if [[ -z "${TFE_CONTENT_DIR}" ]]
  then
    log "ERROR" "${FUNCNAME[0]}" "TFE_CONTENT_DIR is not set"
    exit 1
  fi

  if [[ -z "${op}" ]]
  then
    usage
  fi

  if [[ -z "${TFE_TOKEN}" ]]
  then
    TFE_TOKEN=$(cat ~/.terraform.d/credentials.tfrc.json|jq -r ".credentials.\"${TFE_ADDR}\".token")
    if [[ -z "${TFE_TOKEN}" ]]
    then
      log "ERROR" "${FUNCNAME[0]}" "TFE_TOKEN env var needs to be set, have been unable to automatically instantiate it from ~/.terraform.d/credentials.tfrc.json"
      exit 1
    fi
  fi

  log "INFO" "${FUNCNAME[0]}" "OPERATION ${op}"

  if [[ "${op}" == "plan" ]]
  then
    terraform_plan
  else
    log "ERROR" "${FUNCNAME[0]}" "Do not recognise operation ${op}"
    exit 1
  fi



  ## remove the create_config_version.json file
  #
  rm -f ${UPLOAD_FILE_NAME}
  rm -f ${CREATE_CONFIG_VERSION}
  popd
}

main "$@"
