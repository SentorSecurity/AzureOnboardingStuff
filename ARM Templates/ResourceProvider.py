import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

# Authentication
credentials = DefaultAzureCredential()
subscription_ids = os.environ["LIST_OF_SUBSCRIPTION_IDS"].split(',')

# Create list of resource providers to register per subscription
ResourceProviders = ['Microsoft.PolicyInsights','Microsoft.OperationalInsights','microsoft.insights']

resource_management_clients = {subscription_id: ResourceManagementClient(credentials, subscription_id) for subscription_id in subscription_ids}

# Iterate over list of subscription ID and register resource providers for all of them. 
for subscription_id in subscription_ids:
    print("Now we are going to start registering resources for " + subscription_id)
    for provider in ResourceProviders:
        print("Currently registering " + provider + " for " + subscription_id)
        registration_result = resource_management_clients[subscription_id].providers.register(provider)
        print(f"ProviderNamespace: {registration_result.namespace}, RegistrationState: {registration_result.registration_state}")
    print()

# Just to verify that the registration worked as intended for all the subscriptions
for subscription_id, resource_management_client in resource_management_clients.items():
    providers = resource_management_client.providers.list()  
    registered_providers = [provider for provider in providers if provider.registration_state == "Registered"]  
    # Sort by ProviderNamespace  
    sorted_registered_providers = sorted(registered_providers, key=lambda x: x.namespace)

# List available resource providers and select ProviderNamespace and RegistrationState
for subscription_id, resource_management_client in resource_management_clients.items():
    print(f"Subscription: {subscription_id}")
    for provider in ResourceProviders:
        registered_provider = next((p for p in sorted_registered_providers if p.namespace == provider), None)
        if registered_provider:
            print(f"Resource provider: {provider} ({registered_provider.registration_state})")
    print()