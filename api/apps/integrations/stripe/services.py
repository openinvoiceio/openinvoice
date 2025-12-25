import structlog

from apps.integrations.models import StripeConnection

logger = structlog.get_logger(__name__)


def update_stripe_connection(
    connection: StripeConnection,
    *,
    redirect_url: str | None,
) -> StripeConnection:
    connection.redirect_url = redirect_url
    connection.save()

    logger.info(
        "Stripe connection updated",
        connection_id=connection.id,
        account_id=connection.account_id,
    )

    return connection


def delete_stripe_connection(connection: StripeConnection) -> None:
    connection_id = connection.id
    account_id = connection.account_id
    connection.delete()

    logger.info(
        "Stripe connection deleted",
        connection_id=connection_id,
        account_id=account_id,
    )
