"""Models for ShopifyPlugin."""
import json

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import VerificationMethod, WebhookEndpoint, WebhookMessage
from InvenTree.status_codes import StockHistoryCode

from .ShopifyPlugin import ShopifyPlugin


class Product(models.Model):
    """A shopify product reference."""

    id = models.BigIntegerField(primary_key=True, verbose_name=_("Id"))  # noqa: A003
    title = models.CharField(max_length=250, verbose_name=_("Title"))
    body_html = models.CharField(max_length=250, verbose_name=_("Body HTML"))
    vendor = models.CharField(max_length=250, verbose_name=_("Vendor"))
    product_type = models.CharField(max_length=250, verbose_name=_("Product Type"))
    handle = models.CharField(max_length=250, verbose_name=_("Handle"))
    created_at = models.DateField(
        blank=True, null=True, verbose_name=_("Creation Date")
    )
    updated_at = models.DateField(
        blank=True, null=True, verbose_name=_("Creation Date")
    )
    published_at = models.DateField(
        blank=True, null=True, verbose_name=_("Creation Date")
    )

    def __str__(self):
        """Get string representation of product."""
        return str(self.title)


class Variant(models.Model):
    """A shopify product variant reference."""

    inventory_item_id = models.BigIntegerField(
        verbose_name=_("Inventory item ID"), unique=True
    )
    title = models.CharField(max_length=250, verbose_name=_("Title"))
    sku = models.CharField(max_length=250, verbose_name=_("SKU"))
    barcode = models.CharField(max_length=250, verbose_name=_("Barcode"))
    price = models.CharField(max_length=250, verbose_name=_("Price"))
    created_at = models.DateField(
        blank=True, null=True, verbose_name=_("Creation Date")
    )
    updated_at = models.DateField(
        blank=True, null=True, verbose_name=_("Creation Date")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name=_("Product"),
    )
    part = models.ForeignKey(
        "part.Part",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ShopifyVariant",
        verbose_name=_("Part"),
    )

    def __str__(self) -> str:
        """Get string representation of variant."""
        return str(self.title)


class InventoryLevel(models.Model):
    """A shopify inventory level reference."""

    available = models.IntegerField(verbose_name=_("Available"))
    location_id = models.BigIntegerField(verbose_name=_("Location ID"))
    updated_at = models.DateField(
        blank=True, null=True, verbose_name=_("Creation Date")
    )
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="levels",
        verbose_name=_("Variant"),
    )
    stock_item = models.ForeignKey(
        "stock.StockItem",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ShopifyInventoryLevel",
        verbose_name=_("StockItem"),
    )

    class Meta:
        """Meta options for model."""

        unique_together = (
            "location_id",
            "variant",
        )

    def __str__(self) -> str:
        """Get string representation of inventory level."""
        return str(self.variant)


class ShopifyWebhook(WebhookEndpoint):
    """Reference for Shopify specific webhook."""

    TOKEN_NAME = "X-Shopify-Hmac-Sha256"  # noqa: S105
    VERIFICATION_METHOD = VerificationMethod.HMAC

    shopify_webhook_id = models.IntegerField(blank=True, null=True)

    def init(self, request, *args, **kwargs):
        """Setup for webhook handler."""
        super().init(request, *args, **kwargs)
        self.secret = ShopifyPlugin().get_setting("API_SHARED_SECRET")

    def process_payload(self, message, payload=None, headers=None):
        """Process a webhook message."""
        topic = headers["X-Shopify-Topic"]
        if self.check_if_handled(headers):
            return False

        if topic == "inventory_levels/update":
            # handle invetorylevel update
            update_inventory_levels(payload)
        # elif topic == 'orders/edited':
        #     # handle order edited
        #     pass

        # elif topic == 'orders/updated':
        #     # handle order update
        #     pass

        return True

    def check_if_handled(self, headers: dict) -> bool:
        """Checks if the webhook messages was already handled.

        Args:
            headers (dict): Headers of message

        Returns:
            bool: True if message handled
        """
        message_id = headers["X-Shopify-Webhook-Id"]
        msgs = WebhookMessage.objects.filter(
            endpoint=self, header__contains=message_id, worked_on=True
        )
        if msgs.exists():
            # this was already worked on - we think
            msg = msgs.first()
            payload = json.loads(msg.header)
            if payload.get("X-Shopify-Webhook-Id", "") == message_id:
                # now we can be sure
                return True
        return False

    def get_return(self, payload, headers=None, request=None):
        """Shopify expects no returns."""
        return None


def update_inventory_levels(payload: dict):
    """Handle updates to inventory levels.

    :param payload: payload of webhook
    :type payload: dict
    """
    # fetch item
    item = InventoryLevel.objects.filter(
        variant__inventory_item_id=payload["inventory_item_id"],
        location_id=payload["location_id"],
    )
    if item.exists() and item.count() == 1:
        item = item.first()
        avail = payload["available"]

        # set item qty
        item.available = avail
        if item.stock_item:
            # check if the quantity changed and skip if not
            if item.stock_item.quantity == avail:
                return

            # set stock item qty
            item.stock_item.quantity = avail
            item.stock_item.save()
            # add tracking entry
            item.stock_item.add_tracking_entry(
                StockHistoryCode.STOCK_COUNT,
                None,
                notes="changed in shopify inventory",
                deltas={
                    "quantity": float(avail),
                },
            )
        item.save()
