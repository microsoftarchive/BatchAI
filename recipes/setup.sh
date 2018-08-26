#!/usr/bin/bash
set -e

cp configuration.json.template configuration.json

if ! type "jq" > /dev/null; then
    echo 'jq package is not installed' 
    exit 1
fi

list=`az account list -o table`
if [ "$list" == '[]' ] || [ "$list" == '' ]; then 
  az login -o table
else
  az account list -o table 
fi

set +e
while true; do
    read -p "Input your subscription ID or Name: " account_name
    az account set -s $account_name
    if [ $? == 0 ];then
        sub_id=`az account show | jq -r '.id'`
        echo `jq --arg pass $sub_id '.subscription_id = $pass' configuration.json` > configuration.json
        break
    fi
done

location=`jq -r '.location' configuration.json`

while true; do
    read -p "Please provide the Azure resource group name for Batch AI. If the resource not exist, it will be created automatically: " resource_group
    az group create -l $location -n $resource_group -o table
    if [ $? == 0 ];then
        break
    fi
done
set -e
echo `jq --arg pass $resource_group '.resource_group = $pass' configuration.json` > configuration.json

read -p "Please specify the default Azure Batch AI workspace name, which will be created: " workspace_name
echo `jq --arg pass $workspace_name '.workspace = $pass' configuration.json` > configuration.json

aad_info=`az ad sp create-for-rbac`
aad_id=`echo $aad_info | jq -r '.appId'`
aad_secret=`echo $aad_info | jq -r '.password'`
aad_tenant=`echo $aad_info | jq -r '.tenant'`
echo `jq --arg pass $aad_id '.aad_client_id = $pass' configuration.json` > configuration.json
echo `jq --arg pass $aad_secret '.aad_secret = $pass' configuration.json` > configuration.json
echo `jq --arg pass $aad_tenant '.aad_tenant = $pass' configuration.json` > configuration.json

echo "Batch AI creates administrator user account on every compute node and enables ssh. You need to specify user name and at least a password or ssh public key for this account."
read -p "Username: " username
read -p "Password: " password
echo `jq --arg pass $username '.admin_user["name"] = $pass' configuration.json` > configuration.json
echo `jq --arg pass $password '.admin_user["password"] = $pass' configuration.json` > configuration.json

set +e
while true; do
    read -p "Do you want to create a new Azure storage account [y/n]: " yn
    case $yn in
        [Yy]* ) 
      read -p "Please provide the storage account name you want to create: " storage_account_name  
      az storage account create -l $location -g $resource_group -n $storage_account_name
			if [ $? == 0 ];then
        keysjson=`az storage account keys list -g $resource_group -n $storage_account_name`
        storage_account_key=`echo $keysjson | jq -r '.[0].value'`
        echo `jq --arg pass $storage_account_name '.storage_account["name"] = $pass' configuration.json` > configuration.json
        echo `jq --arg pass $storage_account_key '.storage_account["key"] = $pass' configuration.json` > configuration.json
        break
			fi
			;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
done

az provider register -n Microsoft.Batch
az provider register -n Microsoft.BatchAI
az role assignment create --role "Network Contributor" --assignee 9fcb3732-5f52-4135-8c08-9d4bbaf203ea
echo 'Waiting for Microsoft.BatchAI and Microsoft.Batch providers registered. This may take a few minutes...'
while true; do
    state1=`az provider show -n Microsoft.Batch | jq -r '.registrationState'`
    state2=`az provider show -n Microsoft.BatchAI | jq -r '.registrationState'`
    if [ "Registered" ==  $state1 ] && [ "Registered" == $state2 ]; then
      break
    fi
    sleep 10s
done
