import logging
import azure.functions as func
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import SubscriptionClient, ResourceManagementClient
from datetime import datetime, timezone
from azure.keyvault.secrets import SecretClient


# Timer function for Function apps
def main(myTimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.now(timezone.utc).isoformat()
    
    if myTimer.past_due:
        logging.info('The timer is past due!')


    # Authentication, will use the session that is initialized when signing in to Azure
    default_credentials = DefaultAzureCredential()

    # Connect to a keyvault and Authenticate.
    secret_client = SecretClient(
        vault_url="URL-for-the-keyvault-that-contains-SP-credentials",
        credential=default_credentials
    )
    
    # Grab the secret strings for the service principal (Tenant ID, Client ID and Secret)
    client_secret = secret_client.get_secret(name= "Name-of-secret-that-contains-the-secret").value
    client_id = secret_client.get_secret(name= "Name-of-the-secret-that-contains-the-client-id").value
    tenant_id = secret_client.get_secret(name= "Name-of-the-secret-that-contains-the-tenant-id").value

    service_principal_credentials = ClientSecretCredential (
        tenant_id = tenant_id,
        client_id = client_id,
        client_secret = client_secret
    )

    # List subscriptions using Azure SDK
    subscription_client = SubscriptionClient(service_principal_credentials)
    subscriptions = subscription_client.subscriptions.list()
    subscription_ids = [subscription.subscription_id for subscription in subscriptions]


    # Create list of resource providers to register per subscription
    ResourceProviders = ['Microsoft.PolicyInsights','Microsoft.OperationalInsights','microsoft.insights']

    # Creates a dictionary where each key is a subscription ID and the value is an instance of ResourceManagementClient
    # Initialized with the credentials and subscription ID, iterating over each subscription ID in subscription_ids
    resource_management_clients = {subscription_id: ResourceManagementClient(service_principal_credentials, subscription_id) for subscription_id in subscription_ids}

    # Iterate over list of subscription ID and register resource providers for all of them. 
    for subscription_id in subscription_ids:
        logging.info("Now we are going to start registering resources for " + subscription_id)
        for provider in ResourceProviders:
            logging.info("Currently registering " + provider + " for " + subscription_id)
            registration_result = resource_management_clients[subscription_id].providers.register(provider)
            logging.info(f"ProviderNamespace: {registration_result.namespace}, RegistrationState: {registration_result.registration_state}")
        logging.info("")

    # Just to verify that the registration worked as intended for all the subscriptions
    for subscription_id, resource_management_client in resource_management_clients.items():
        providers = resource_management_client.providers.list()  
        registered_providers = [provider for provider in providers if provider.registration_state == "Registered"]  
        # Sort by ProviderNamespace  
        sorted_registered_providers = sorted(registered_providers, key=lambda x: x.namespace)

    # List available resource providers and select ProviderNamespace and RegistrationState
    for subscription_id, resource_management_client in resource_management_clients.items():
        logging.info(f"Subscription: {subscription_id}")
        for provider in ResourceProviders:
            registered_provider = next((p for p in sorted_registered_providers if p.namespace == provider), None)
            if registered_provider:
                logging.info(f"Resource provider: {provider} ({registered_provider.registration_state})")
        logging.info("")

    logging.info('Python timer trigger function executed at %s', utc_timestamp)