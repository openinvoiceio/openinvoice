from allauth.headless.spec.internal.schema import get_schema

ALLAUTH_OPERATION_ID_MAP = {
    ("/api/{client}/v1/config/", "get"): "get_auth_config",
    # Account auth
    ("/api/{client}/v1/auth/login/", "post"): "login",
    ("/api/{client}/v1/auth/signup/", "post"): "signup",
    ("/api/{client}/v1/auth/email/verify/", "get"): "get_verify_email",
    ("/api/{client}/v1/auth/phone/verify/", "post"): "verify_phone",
    ("/api/{client}/v1/auth/email/verify/", "post"): "verify_email",
    ("/api/{client}/v1/auth/reauthenticate/", "post"): "reauthenticate",
    # Password reset auth
    ("/api/{client}/v1/auth/password/request/", "post"): "request_password_reset",
    ("/api/{client}/v1/auth/password/reset/", "get"): "get_reset_password",
    ("/api/{client}/v1/auth/password/reset/", "post"): "reset_password",
    # Providers auth
    ("/api/browser/v1/auth/provider/redirect/", "post"): "redirect_provider",
    ("/api/{client}/v1/auth/provider/token/", "post"): "provider_token",
    ("/api/{client}/v1/auth/provider/signup/", "post"): "signup_provider",
    # 2FA auth
    ("/api/{client}/v1/auth/2fa/authenticate/", "post"): "authenticate_2fa",
    ("/api/{client}/v1/auth/2fa/reauthenticate/", "post"): "reauthenticate_2fa",
    # Webauthn login auth
    ("/api/{client}/v1/auth/webauthn/authenticate/", "get"): "get_authenticate_webauthn",
    ("/api/{client}/v1/auth/webauthn/authenticate/", "post"): "authenticate_webauthn",
    ("/api/{client}/v1/auth/webauthn/reauthenticate/", "get"): "get_reauthenticate_webauthn",
    ("/api/{client}/v1/auth/webauthn/reauthenticate/", "post"): "reauthenticate_webauthn",
    ("/api/{client}/v1/auth/webauthn/login/", "get"): "get_login_webauthn",
    ("/api/{client}/v1/auth/webauthn/login/", "post"): "login_webauthn",
    # Webauthn signup auth
    ("/api/{client}/v1/auth/webauthn/signup/", "get"): "get_signup_webauthn",
    ("/api/{client}/v1/auth/webauthn/signup/", "post"): "signup_webauthn",
    ("/api/{client}/v1/auth/webauthn/signup/", "put"): "update_webauthn_signup",
    # Code auth
    ("/api/{client}/v1/auth/code/request/", "post"): "request_code",
    ("/api/{client}/v1/auth/code/confirm/", "post"): "confirm_code",
    # Account providers
    ("/api/{client}/v1/account/providers/", "get"): "get_providers",
    ("/api/{client}/v1/account/providers/", "delete"): "delete_providers",
    # Account email
    ("/api/{client}/v1/account/email/", "get"): "list_email_addresses",
    ("/api/{client}/v1/account/email/", "post"): "add_email_address",
    ("/api/{client}/v1/account/email/", "put"): "request_email_verification",
    ("/api/{client}/v1/account/email/", "patch"): "change_email_address",
    ("/api/{client}/v1/account/email/", "delete"): "remove_email_address",
    # Account phone
    ("/api/{client}/v1/account/phone/", "get"): "list_phone_numbers",
    ("/api/{client}/v1/account/phone/", "post"): "change_phone_number",
    # Account 2fa
    ("/api/{client}/v1/account/authenticators/", "get"): "list_authenticators",
    ("/api/{client}/v1/account/authenticators/totp/", "get"): "get_totp_authenticator_status",
    ("/api/{client}/v1/account/authenticators/totp/", "post"): "activate_totp_authenticator",
    ("/api/{client}/v1/account/authenticators/totp/", "delete"): "deactivate_totp_authenticator",
    ("/api/{client}/v1/account/authenticators/recovery_codes/", "get"): "list_recovery_codes",
    ("/api/{client}/v1/account/authenticators/recovery_codes/", "post"): "regenerate_recovery_codes",
    # Account webauthn
    ("/api/{client}/v1/account/authenticators/webauthn/", "get"): "get_webauthn_authenticator",
    ("/api/{client}/v1/account/authenticators/webauthn/", "post"): "add_webauthn_authenticator",
    ("/api/{client}/v1/account/authenticators/webauthn/", "put"): "rename_webauthn_authenticator",
    ("/api/{client}/v1/account/authenticators/webauthn/", "delete"): "remove_webauthn_authenticator",
    # Current session
    ("/api/{client}/v1/auth/session/", "get"): "get_session",
    ("/api/{client}/v1/auth/session/", "delete"): "logout",
    # Account password
    ("/api/{client}/v1/account/password/change/", "post"): "change_password",
    # Sessions
    ("/api/{client}/v1/auth/sessions/", "get"): "list_sessions",
    ("/api/{client}/v1/auth/sessions/", "delete"): "delete_sessions",
}


def merge_allauth_paths(spec, result) -> None:
    if "paths" in spec:
        result.setdefault("paths", {})
        for path, path_item in spec["paths"].items():
            # If the path doesn't exist in DRF spec, add it in full
            if path not in result["paths"]:
                new_path = path.replace("/_allauth", "/api")
                for method, operation in path_item.items():
                    method_lower = method.lower()
                    normalized_path = new_path if path.endswith("/") else new_path + "/"
                    operation["operationId"] = ALLAUTH_OPERATION_ID_MAP[(normalized_path, method_lower)]
                result["paths"][new_path] = path_item

    return result


def merge_allauth_components(spec, result) -> None:
    if "components" in spec:
        result.setdefault("components", {})
        for subcomponent_key, subcomponent_val in spec["components"].items():
            # If DRF spec doesn't have this subcomponent, assign directly
            if subcomponent_key not in result["components"]:
                result["components"][subcomponent_key] = subcomponent_val
            else:
                if isinstance(subcomponent_val, dict):
                    # Merge dictionaries for components like schemas, parameters, etc.
                    for item_key, item_val in subcomponent_val.items():
                        if item_key not in result["components"][subcomponent_key]:
                            result["components"][subcomponent_key][item_key] = item_val


def allauth_postprocessing_hook(result, **_):
    spec = get_schema()

    # Merge external paths
    merge_allauth_paths(spec, result)

    # Merge external components (all subcomponents: schemas, parameters, etc.)
    merge_allauth_components(spec, result)

    return result
