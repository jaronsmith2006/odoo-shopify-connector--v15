from odoo import fields, models, api


class LocationCreateModel(models.TransientModel):
    _name = "create.create_location_tbl"
    _description = "Location Popup"

    instance = fields.Many2one("demo_shopify.instance_tbl", string="Instance", required=True, domain="[('state', '=', '1')]")
    location_name = fields.Char(string="Location Name")

