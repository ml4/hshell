#!/bin/bash

function usage {
  echo "Usage: $(basename ${0}) <log group> <region>"
  echo
  echo 'ENSURE TO EXPORT AWS CREDS FIRST'
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
  bldred="\033[1;31m" # Red
  bldgrn="\033[1;32m" # Green
  bldylw="\033[1;33m" # Yellow
  bldblu="\033[1;34m" # Blue
  bldpur="\033[1;35m" # Purple
  bldcyn="\033[1;36m" # Cyan
  nmlcyn="\033[0;36m" # Cyan
  bldwht="\033[1;37m" # White
  nmlwht="\033[0;37m" # White
  txtrst="\033[0m"    # Text Reset

  group=${1}
  region=${2}
  if [[ -z "${region}" ]]
  then
    usage
  fi

  aws logs tail ${group} --follow --region ${region} | while read line
  do
    timestamp=$(echo ${line} | awk '{print $1}')
    tag=$(echo ${line} | /usr/bin/sed 's/.*CONTAINER_TAG":"\([^"]*\)".*/\1/g')
    tag_first_ch=$(echo ${tag} | cut -c1)
    if [[ ${tag_first_ch} =~ ^[0-9]+$ ]]
    then
      ## it means sed did not find CONTAINER_TAG so it must be a SYSTEM-type log output
      #
      tag='SYSTEM'
    fi
    message=$(echo ${line} | /usr/bin/sed 's/.*"message":"\(.*\)"_SOURCE_REALTIME_TIMESTAMP.*/\1/')

    level=${bldpur}
    if [[ ${message} =~ '[ERROR]' ]]
    then
      level=${bldred}
    elif [[ ${message} =~ '[WARN]' ]]
    then
      level=${bldylw}
    elif [[ ${message} =~ '[DEBUG]' ]]
    then
      level=${nmlwht}
    elif [[ ${message} =~ '[Audit Log]' ]]
    then
      level=${bldblu}
    elif [[ "${tag}" == 'SYSTEM' ]]
    then
      level=${nmlcyn}
    fi
    echo -e "${nmlcyn}${timestamp} ${txtrst}| ${bldgrn}${tag} ${txtrst}| ${level}${message}"
  done
}

main "$@"