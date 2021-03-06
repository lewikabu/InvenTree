# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from datetime import datetime

from InvenTree.models import InvenTreeTree


class StockLocation(InvenTreeTree):
    """ Organization tree for StockItem objects
    A "StockLocation" can be considered a warehouse, or storage location
    Stock locations can be heirarchical as required
    """

    def get_absolute_url(self):
        return '/stock/location/{id}/'.format(id=self.id)

    @property
    def items(self):
        return self.stockitem_set.all()

    @property
    def has_items(self):
        return self.items.count() > 0


@receiver(pre_delete, sender=StockLocation, dispatch_uid='stocklocation_delete_log')
def before_delete_stock_location(sender, instance, using, **kwargs):

    # Update each part in the stock location
    for item in instance.items.all():
        item.location = instance.parent
        item.save()

    # Update each child category
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()


class StockItem(models.Model):
    """
    A 'StockItem' instance represents a quantity of physical instances of a part.
    It may exist in a StockLocation, or as part of a sub-assembly installed into another StockItem
    StockItems may be tracked using batch or serial numbers.
    If a serial number is assigned, then StockItem cannot have a quantity other than 1
    """

    def get_absolute_url(self):
        return '/stock/item/{id}/'.format(id=self.id)

    class Meta:
        unique_together = [
            ('part', 'serial'),
        ]

    # The 'master' copy of the part of which this stock item is an instance
    part = models.ForeignKey('part.Part', on_delete=models.CASCADE, related_name='locations')

    # The 'supplier part' used in this instance. May be null if no supplier parts are defined the master part
    supplier_part = models.ForeignKey('part.SupplierPart', blank=True, null=True, on_delete=models.SET_NULL)

    # Where the part is stored. If the part has been used to build another stock item, the location may not make sense
    location = models.ForeignKey(StockLocation, on_delete=models.DO_NOTHING,
                                 related_name='items', blank=True, null=True,
                                 help_text='Where is this stock item located?')

    # If this StockItem belongs to another StockItem (e.g. as part of a sub-assembly)
    belongs_to = models.ForeignKey('self', on_delete=models.DO_NOTHING,
                                   related_name='owned_parts', blank=True, null=True,
                                   help_text='Is this item installed in another item?')

    # The StockItem may be assigned to a particular customer
    customer = models.ForeignKey('company.Company', on_delete=models.SET_NULL,
                                 related_name='stockitems', blank=True, null=True,
                                 help_text='Item assigned to customer?')

    # Optional serial number
    serial = models.PositiveIntegerField(blank=True, null=True,
                                         help_text='Serial number for this item')

    # Optional URL to link to external resource
    URL = models.URLField(max_length=125, blank=True)

    # Optional batch information
    batch = models.CharField(max_length=100, blank=True,
                             help_text='Batch code for this stock item')

    # If this part was produced by a build, point to that build here
    # build = models.ForeignKey('build.Build', on_delete=models.SET_NULL, blank=True, null=True)

    # Quantity of this stock item. Value may be overridden by other settings
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    # Last time this item was updated (set automagically)
    updated = models.DateField(auto_now=True)

    # last time the stock was checked / counted
    stocktake_date = models.DateField(blank=True, null=True)

    stocktake_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    review_needed = models.BooleanField(default=False)

    ITEM_OK = 10
    ITEM_ATTENTION = 50
    ITEM_DAMAGED = 55
    ITEM_DESTROYED = 60

    ITEM_STATUS_CODES = {
        ITEM_OK: _("OK"),
        ITEM_ATTENTION: _("Attention needed"),
        ITEM_DAMAGED: _("Damaged"),
        ITEM_DESTROYED: _("Destroyed")
    }

    status = models.PositiveIntegerField(
        default=ITEM_OK,
        choices=ITEM_STATUS_CODES.items(),
        validators=[MinValueValidator(0)])

    notes = models.TextField(blank=True)

    # If stock item is incoming, an (optional) ETA field
    # expected_arrival = models.DateField(null=True, blank=True)

    infinite = models.BooleanField(default=False)

    @property
    def has_tracking_info(self):
        return self.tracking_info.count() > 0

    @transaction.atomic
    def stocktake(self, count, user):
        """ Perform item stocktake.
        When the quantity of an item is counted,
        record the date of stocktake
        """

        count = int(count)

        if count < 0 or self.infinite:
            return

        self.quantity = count
        self.stocktake_date = datetime.now().date()
        self.stocktake_user = user
        self.save()

    @transaction.atomic
    def add_stock(self, amount):
        """ Add items to stock
        This function can be called by initiating a ProjectRun,
        or by manually adding the items to the stock location
        """

        amount = int(amount)

        if self.infinite or amount == 0:
            return

        amount = int(amount)

        q = self.quantity + amount
        if q < 0:
            q = 0

        self.quantity = q
        self.save()

    @transaction.atomic
    def take_stock(self, amount):
        self.add_stock(-amount)

    def __str__(self):
        s = '{n} x {part}'.format(
	    n=self.quantity,
            part=self.part.name)

        if self.location:
            s += ' @ {loc}'.format(loc=self.location.name)

        return s

    @property
    def is_trackable(self):
        return self.part.trackable


class StockItemTracking(models.Model):
    """ Stock tracking entry
    """

    # Stock item
    item = models.ForeignKey(StockItem, on_delete=models.CASCADE,
                             related_name='tracking_info')

    # Date this entry was created (cannot be edited)
    date = models.DateField(auto_now_add=True, editable=False)

    # Short-form title for this tracking entry
    title = models.CharField(max_length=250)

    # Optional longer description
    notes = models.TextField(blank=True)

    # Which user created this tracking entry?
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    # Was this tracking note auto-generated by the system?
    system = models.BooleanField(default=False)

    # TODO
    # image = models.ImageField(upload_to=func, max_length=255, null=True, blank=True)

    # TODO
    # file = models.FileField()
