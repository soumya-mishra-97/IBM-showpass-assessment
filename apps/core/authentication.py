from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """DRF's database token auth with the industry-familiar 'Bearer' prefix.

    This is a learning implementation: tokens do not expire or rotate.
    Use OAuth2/OIDC or expiring tokens in a real deployment.
    """
    keyword = "Bearer"
