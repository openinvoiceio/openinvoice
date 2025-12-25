from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class PortalAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.portal.authentication.PortalAuthentication"
    name = "portalAuth"

    def get_security_definition(self, _):
        return build_bearer_security_scheme_object(
            header_name="Authorization",
            token_prefix=self.target.keyword,
        )
