#!/bin/sh

# Define various functions that are very useful
#
# A hostlist is a list of hosts in the format
#
#	host		Single host
#	host[nnn]	All names from "host001" to "hostnnn"
#	host[nnn-mmm]	All names from "hostnnn" to "hostmmm"

# hoststatus <hostlist>			Current memcache status of a host list
# online <hostlist>			Mark a list of hosts "online" in memcache
# offline <hostlist> "Reason"		Mark a list of hosts "offline" in memcache with the reason "Reason"
# condor_online <hostlist>		Mark a list of hosts "online" within Condor
# condor_offline <hostlist>		Mark a list of hosts "offline" within Condor


# Other functions are

# dump_site <site>			Dumps a memcache site (uct2, iut2, taub) to stdout
# load_state <dump line>		Load a line from dump_site format back into memcache



# Scripts to get/put data from memcache
MEMCLIENT=~ddl/bin/memclient.py

# Scripts to mark a node on or offline
CONDOR_OFFLINE=~ddl/bin/condor_offline.py

# Check on the status of a node
CONDOR_NODE_CHECK=~ddl/bin/condor_node_check.sh


# Builds a node list in the array "myHostList" (must be declare -a myHostList)
#
# The argument should be of the form
#
#	node		uct2-c100	Returns uct2-c100
#	node[nnn]	uct2-c[100]	Returns uct2-c001, uct2-c002, uct2-c003, ..., uct2-c100
#`	node[nnn-mmm]	uct2-c[90-100]	Returns uct2-c090, uct2-c091, uct2-c092, ..., uct2-c100
#
# 
function BuildmyHostList() {

   for arg in $*; do

      if fgrep -q \[ <<< $arg; then

         ## (Overly?) fancy expansion of [] in hostnames
         # Pull out bracketed expression
   
         brkt=$(sed 's/.*\[\(.*\)\].*/\1/' <<< $arg)

         # If there is a hyphen, it is a range of numbers

         if grep -q -- - <<< $brkt; then
             num1=$(sed 's/-.*//' <<< $brkt)
             num2=$(sed 's/.*-//' <<< $brkt)
         else # otherwise it is 1-N
             num1=1
             num2=$brkt
         fi

         # Format everything to the width of "num2"

         fmt=$(sed 's/\[.*\]/%0'${#num2}'g/' <<< $arg)

         for x in $(seq -f $fmt $num1 $num2); do
             myHostList=(${myHostList[*]} $x)
         done

      else

         myHostList=(${myHostList[*]} $arg)

      fi

   done

}


# Check on the current status of a host list

function hoststatus() {

   declare -a myHostList

   myHostName="$1"

   if [ -z "${myHostName}" ]; then
      echo "Missing host name such as uct2-c100, uct2-c[100] or uct2-c[90-100]"
      return 1
   fi


   # Build the host list from the given name

   BuildmyHostList "$myHostName"


   # Number of hosts we found

   myHostNum=${#myHostList[*]}


   # Loop over all the names in the array

   for ((i=0; i<$myHostNum; i++)) ; do

       # Extract the host we want to lookup

       myHost=${myHostList[$i]}


       # Pull out the status from memcache on this name

       myHostStatus=$($MEMCLIENT get ${myHost}.manualstatus)


       # Status is online, offline or unknown

       case ${myHostStatus} in

       (online)

          echo "$myHost - Online"

          ;;

       (offline)

          myHostReason=$($MEMCLIENT get ${myHost}.manualreason)

          echo "$myHost - Offline : \"${myHostReason}\""

          ;;

       (*)

          echo "$myHost - Unknown : ${myHostStatus}"

          ;;

       esac

   done

}


# Mark a host online in memcache

function online() {

   declare -a myHostList

   myHostName="$1"

   if [ -z "$myHostName" ]; then
      echo "Missing host name such as uct2-c100, uct2-c[100] or uct2-c[90-100]"
      return 1
   fi


   # Build the nodes list

   BuildmyHostList "$myHostName"


   # Number of hosts we found

   myHostNum=${#myHostList[*]}

   for ((i=0; i<$myHostNum; i++)) ; do
      myHost=${myHostList[$i]}

#      echo "$myHost - Online" 
      $CONDOR_OFFLINE c $myHost

   done



}


# Mark a node offline in memcache with an optional reason

function offline() {

   declare -a myHostList

   myHostName="$1"
   myHostReason="$2"

   if [ -z "$myHostName" ]; then
      echo "Missing host name such as uct2-c100, uct2-c[100] or uct2-c[90-100]"
      return 1
   fi

   if [ -z "$myHostReason" ]; then
     myHostReason="For Reasons Unknown"
   fi


   # Build the nodes list

   BuildmyHostList "$myHostName"


   # Number of hosts we found

   myHostNum=${#myHostList[*]}

   for ((i=0; i<$myHostNum; i++)) ; do
      myHost=${myHostList[$i]}

#      echo "$myHost - Offline : \"$myHostReason\""
      $CONDOR_OFFLINE o $myHost "$myHostReason" 

   done

}



# Turn a node online with respect to Condor daemons

function condor_online() {

   declare -a myHostList

   myHostName="$1"

   if [ -z "$myHostName" ]; then
      echo "Missing host name such as uct2-c100, uct2-c[100] or uct2-c[90-100]"
      return 1
   fi


   # Build the nodes list

   BuildmyHostList "$myHostName"


   # Number of hosts we found

   myHostNum=${#myHostList[*]}

   for ((i=0; i<$myHostNum; i++)) ; do
      myHost=${myHostList[$i]}

#      echo "$myHost - Condor ON"
      condor_on -startd $myHost

   done

}


# Turn a node offline (peacefully) with respect to Condor daemons 

function condor_offline() {

   declare -a myHostList

   myHostName="$1"

   if [ -z "$myHostName" ]; then
      echo "Missing host name such as uct2-c100, uct2-c[100] or uct2-c[90-100]"
      return 1
   fi

   # Build the nodes list

   BuildmyHostList "$myHostName"


   # Number of hosts we found

   myHostNum=${#myHostList[*]}

   for ((i=0; i<$myHostNum; i++)) ; do
      myHost=${myHostList[$i]}

#      echo "$myHost - Condor OFF"
      condor_off -peaceful -startd $myHost

   done

}



# Dump the current state of nodes in memcache for a respective site
#
# Usage:	dump_site Site
#
#	Site	iut2
#		uct2
#		taub
#
#
# The dump is to stdout and of the format
#
# Node:State:Reason
#
# Node		Short name of the node (such as uct2-c267, iut2-c199, taub105)
# State		State of the node, online or offline
# Reason	Reason a node is "offline"

function dump_site() {


# The site name

mySite=$1

case ${mySite} in

(uct2)

   myHostBase="uct2-c"
   myHostLow=1
   myHostHigh=350

   ;;

(iut2)

   myHostBase="iut2-c"
   myHostLow=1
   myHostHigh=200

   ;;

(taub)

   myHostBase="taub"
   myHostLow=105
   myHostHigh=140

   ;;

(*)

   echo "$0 Unnown site ${mySite}"

   exit 0

esac



for ((myHostNum=$myHostLow; myHostNum<=myHostHigh; ++myHostNum)); do
  
  # Node names alway have leading "0"
  # Such as iut2-c005 and uct2-c018

  if   [[ myHostNum -lt  10 ]]; then 
     myHostName="${myHostBase}00${myHostNum}"
  elif [[ myHostNum -lt 100 ]]; then
     myHostName="${myHostBase}0${myHostNum}"
  else
     myHostName="${myHostBase}${myHostNum}"
  fi


  # Fetch the status of the node

  myHostStatus=$($MEMCLIENT get ${myHostName}.manualstatus)


  # It should only return:
  #
  # online:	The node is online and ready for jobs
  # offline:	The node is offline with a given reason
  # None:	The node is not defined in memcache

  case ${myHostStatus} in

  (online)

     echo "${myHostName}:${myHostStatus}"

     ;;

  (offline)

     myHostReason=$($MEMCLIENT get ${myHostName}.manualreason)

     echo "${myHostName}:${myHostStatus}:${myHostReason}"

     ;;

  (None)

     ;;

  (*)

     ;;

  esac

done


}

function load_state() {

while read myState; do

   myHostName=$(echo ${myState} | cut -d':' -f1)
   myHostStatus=$(echo ${myState} | cut -d':' -f2)
   myHostReason=$(echo ${myState} | cut -d':' -f3)

   case $myHostStatus in

   (online)

#      echo "Online  ${myHostName}"
      online "${myHostName}"

      ;;

   (offline)

#      echo "Offline ${myHostName} with reason \"${myHostReason}\""
      offline "${myHostName}" "${myHostReason}"

      ;;

   (*)

      echo "$0 Unknown state ${myHostStatus} for node ${myHostName}"

      ;;

   esac

done


}
