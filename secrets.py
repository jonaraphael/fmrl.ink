import os

from google.cloud import secretmanager


def get_secret(secret_id, project_id=None):
    """
    Retrieve the latest version of a secret from Google Cloud Secret Manager.
    If project_id is not provided, it is taken from the environment variable GCP_PROJECT.
    """
    if project_id is None:
        project_id = os.environ.get("GCP_PROJECT")
        if not project_id:
            raise Exception(
                "GCP_PROJECT environment variable must be set to use Secret Manager."
            )

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
