from odoo import models, api, fields


class ColorSizeClass(models.Model):
    _name = "ds.color_size_code_tbl"

    color_name = fields.Text(string="Color Name")
    color_code = fields.Text(string="Color Code")
    size_name = fields.Text(string="Size Name")
    size_code = fields.Text(string="Size Code")