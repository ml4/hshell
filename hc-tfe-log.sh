#!/usr/bin/env bash
#
## hc-tfe-log.sh
#
## 2022-05-18 ml4
## TESTED WITH 619 v202205-1
#
################################################################################################################

function usage {
  echo "Usage: $(basename ${0}) <log group> <region>"
  echo
  echo 'ENSURE TO EXPORT AWS CREDS FIRST'
  exit 1
}

function main {
  nmlred="\033[0;31m" # Red
  bldred="\033[1;31m" # Red
  nmlgrn="\033[0;32m" # Green
  bldgrn="\033[1;32m" # Green
  nmlylw="\033[0;33m" # Yellow
  bldylw="\033[1;33m" # Yellow
  bldblu="\033[1;34m" # Blue
  nmlpur="\033[0;35m" # Purple
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

  aws logs tail ${group} --follow --region ${region} | while read -r line
  do
    log=$(echo "${line}" | cut -d' ' -f3-)
    container_name=$(echo "${log}" | /usr/bin/sed 's/.*container_tag":"\([^"]*\)".*/\1/g')
    message=$(echo "${log}" | jq -r .message)

    ## normalise timestamp
    ## there are several different formats due to conglomeration of services within TFE:
    #
    ## "message":"10.128.21.133 - - [18/May/2022:12:11:15 +0000] ...
    ## "message":"[2022/05/18 12:21:13] [error] ...
    ## "message":"2022-05-18 12:21:05 [INFO] ...
    ## "message":"  [DEPRECATION] :after_commit AASM callback is not safe in terms of race conditions and redundant calls.","source_realtime_timestamp":"1652888678750007"
    #
    if [[ $(echo ${message} | awk '{print $1}') == '[DEPRECATION]' ]]
    then
      ## Deprecation warning - take timestamp from line, not message
      #
      timestamp=$(echo ${message} | awk '{print $1}' | sed 's/T/ /' | sed 's/\..*//')
      logEntry="${message}"
      level="DPRC8"
    elif [[ $(echo ${message} | awk '{print $1}') =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]
    then
      ## nginx-type log message
      #
      ts=$(echo ${message} | cut -d' ' -f4)
      day=$(echo ${ts} | cut -d'/' -f1 | tr -d '[')
      month=$(echo ${ts} | cut -d'/' -f2)
      year=$(echo ${ts} | cut -d'/' -f3 | cut -d: -f1)
      time=$(echo ${ts} | cut -d: -f2-4)
      case ${month} in
        Jan) mo='01' ;;
        Feb) mo='02' ;;
        Mar) mo='03' ;;
        Apr) mo='04' ;;
        May) mo='05' ;;
        Jun) mo='06' ;;
        Jul) mo='07' ;;
        Aug) mo='08' ;;
        Sep) mo='09' ;;
        Oct) mo='10' ;;
        Nov) mo='11' ;;
        Dec) mo='12' ;;
        *)
          echo "ERROR IN SCRIPT on message:"
          echo ${message}
          echo
          exit 1
          ;;
      esac
      timestamp="${year}-${mo}-${day} ${time}"
      logEntry=$(echo "${message}" | cut -d' ' -f6-)
      level=$(echo "${message}" | cut -d' ' -f9 | tr -d '[]')
    elif [[ $(echo ${message} | awk '{print $1}') =~ [0-9]{4}-[0-9]{2}-[0-9]{2}T ]]
    then
      ## sidekiq-type log message
      #
      timestamp=$(echo ${message} | cut -d' ' -f1 | sed 's/T/ /' | sed 's/\.[0-9][0-9][0-9]Z//')
      level=$(echo "${message}" | awk '{print $6}' | tr -d ':')
      logEntry=$(echo "${message}" | cut -d' ' -f2-)
    elif [[ "${message:0:1}" == '[' ]]
    then
      ## fluent-bit-type entries
      #
      timestamp=$(echo ${message} | cut -d' ' -f1-2 | tr -d '[]')
      level=$(echo "${message}" | cut -d'[' -f3 | tr -d '[]' | awk '{print $1}')
      logEntry=$(echo "${message}" | cut -d']' -f3- | sed 's/^ //')
    else
      ## "normal" entries
      #
      timestamp=$(echo ${message} | cut -d' ' -f1-2 | tr -d '[]')
      level=$(echo "${message}" | awk '{print $3}' | tr -d '[]')
      logEntry=$(echo "${message}" | cut -d' ' -f4-)
    fi

    colour=${bldwht}
    level=$(echo ${level} | tr '[:lower:]' '[:upper:]')
    if [[ ${level} =~ 'ERROR' ]]
    then
      colour=${bldred}
    elif [[ ${level} =~ 'WARN' ]]
    then
      colour=${bldylw}
    elif [[ ${level} =~ 'DEBUG' ]]
    then
      colour=${nmlwht}
    elif [[ "${level}" =~ 'INFO' ]]
    then
      colour=${bldwht}
    elif [[ "${level}" =~ 'DPRC8' ]]
    then
      colour=${nmlylw}
    elif [[ ${line} =~ 'Audit Log' ]]
    then
      colour=${bldblu}
    elif [[ ${level:0:1} =~ [12] ]]
    then
      colour=${bldgrn}
    elif [[ ${level:0:1} =~ [3] ]]
    then
      colour=${nmlgrn}
    elif [[ ${level:0:1} =~ [4] ]]
    then
      colour=${nmlred}
    elif [[ ${level:0:1} =~ [5] ]]
    then
      colour=${bldred}
    else
      ## We probably encountered a message which we've not accounted for - output special case
      #
      colour=${nmlpur}
      logEntry=${message}
      level="?????"
    fi

    # echo '--------------------------'
    # echo "$line"
    # echo '--------------------------'
    printf "${nmlcyn}%s${txtrst} ${bldgrn}%14s${txtrst} [${colour}%5s${txtrst}] ${colour}%s${txtrst}\n" "${timestamp}" "${container_name}" "${level}" "${logEntry}"
  done
}

main "$@"
