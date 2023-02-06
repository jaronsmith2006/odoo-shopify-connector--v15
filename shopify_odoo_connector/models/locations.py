from odoo import fields, api, models
from datetime import datetime, date
import pytz

india = pytz.timezone('Asia/Kolkata')


class LocationModel(models.Model):
    _name = "ds.locations_tbl"
    _description = "ds.locations_tbl"
    _rec_name = "location_name"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    location_id = fields.Char(string="Location Id")
    location_name = fields.Char(string="Location Name")
    instance = fields.Many2one("shopify_odoo_connector.instance_tbl", string="Instance", ondelete='cascade')
    variants_inventory_data = fields.One2many("ds.variant_inventory_tbl", "variant_location_id", string="Variant Inventory")
    created_date = fields.Datetime(string="Created Date", default=set_date)
