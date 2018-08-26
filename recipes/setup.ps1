$config = Get-Content -Raw -Path ".\configuration.json.template" | ConvertFrom-JSON

$list = & az account list -o table
$list
if ($list -eq ''){
    az login -o table
}

while (1) {
    $account_name = Read-Host -Prompt 'Input your subscription ID or Name'
    az account set -s $account_name
    if ($?) {
        $account = & az account show
        $account_json = ConvertFrom-JSON "$account"
        $config.subscription_id = $account_json.id
        break
    }
}

while (1) {
    $resource_group = Read-Host -Prompt 'Please provide the Azure resource group name for Batch AI. If the resource not exist, it will be created automatically'
    az group create -l $config.location -n $resource_group -o table
    if ($?) {
        $config.resource_group = $resource_group
        break
    }
}

$addinfojson = & az ad sp create-for-rbac
$aadinfo = ConvertFrom-JSON "$addinfojson"

$config.aad_client_id = $aadinfo.appId
$config.aad_secret = $aadinfo.password
$config.aad_tenant = $aadinfo.tenant

$config.workspace = Read-Host -Prompt 'Please specify the default Azure Batch AI workspace name, which will be created'
Write-Host 'Batch AI creates administrator user account on every compute node and enables ssh. You need to specify user name and at least a password or ssh public key for this account.'
$config.admin_user.name = Read-Host -Prompt 'user name'
$config.admin_user.password = Read-Host -Prompt 'password'

$createstorageaccount = '' 
while($createstorageaccount -ne "n")
{
    if ($createstorageaccount -eq 'y') {
        $storage_account_name = Read-Host -Prompt 'Please provide the storage account name you want to create'
        az storage account create -l $config.location -g $resource_group -n $storage_account_name
        if ($?) {
            $keysjson = & az storage account keys list -g $resource_group -n $storage_account_name
            $keys = ConvertFrom-JSON "$keysjson"
            $config.storage_account.name = $storage_account_name
            $config.storage_account.key = $keys[0].value
            break
        }
    }
    $createstorageaccount = Read-Host 'Do you want to create a new Azure storage account [y/n]'
}

$config | ConvertTo-Json | Out-File ".\configuration.json" -Encoding Ascii


az provider register -n Microsoft.Batch
az provider register -n Microsoft.BatchAI
az role assignment create --role "Network Contributor" --assignee 9fcb3732-5f52-4135-8c08-9d4bbaf203ea

Write-Host  'Waiting for Microsoft.BatchAI and Microsoft.Batch providers registered. This may take a few minutes...'

while(1)
{
    $register_status = & az provider show -n Microsoft.Batch
    $state1 = (ConvertFrom-JSON "$register_status").registrationState

    $register_status = & az provider show -n Microsoft.BatchAI
    $state2 = (ConvertFrom-JSON "$register_status").registrationState
    
    if ($state1 -eq 'Registered' -And $state2 -eq 'Registered') {
        break
    }
    Start-Sleep -s 10
}
