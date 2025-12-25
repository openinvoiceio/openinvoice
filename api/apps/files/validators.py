from .enums import FilePurpose


class FileValidator:
    allowed_content_types: list[str] = []
    max_size = 0


class AccountLogoValidator(FileValidator):
    allowed_content_types = ["image/png", "image/jpeg", "image/svg+xml"]
    max_size = 512 * 1024


class ProductImageValidator(FileValidator):
    allowed_content_types = ["image/png", "image/jpeg", "image/webp"]
    max_size = 2 * 1024 * 1024


class ProfileAvatarValidator(FileValidator):
    allowed_content_types = ["image/png", "image/jpeg", "image/svg+xml"]
    max_size = 512 * 1024


class CustomerLogoValidator(FileValidator):
    allowed_content_types = ["image/png", "image/jpeg", "image/svg+xml"]
    max_size = 512 * 1024


SUPPORTED_FILE_VALIDATORS = {
    FilePurpose.ACCOUNT_LOGO: AccountLogoValidator(),
    FilePurpose.PRODUCT_IMAGE: ProductImageValidator(),
    FilePurpose.PROFILE_AVATAR: ProfileAvatarValidator(),
    FilePurpose.CUSTOMER_LOGO: CustomerLogoValidator(),
}
