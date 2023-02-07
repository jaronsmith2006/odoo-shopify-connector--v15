from odoo import models, api, fields, _
import shopify
import json
from odoo.exceptions import Warning, ValidationError
from odoo.fields import One2many
from datetime import datetime, date
import re
import pytz

india = pytz.timezone('Asia/Kolkata')


class InstanceClass(models.Model):
    _name = "shopify_odoo_connector_sp.instance_tbl"
    _description = "shopify_odoo_connector_sp.instance_tbl"
    _rec_name = 'store_name'

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    store_name = fields.Char(string="Store Name", track_visibility='always', required=True)
    store_url = fields.Char(string="Store URL", required=True, track_visibility='always')
    store_image = fields.Image(string="Store Logo")
    api_key = fields.Char(string="Store API Key", required=True)
    api_password = fields.Char(string="Store API Password", required=True)
    shopify_version = fields.Char(string="Version", required=True)
    address = fields.Text(string="Address", readonly=True)
    email = fields.Char(string="Email", readonly=True)
    currency = fields.Char(string="Currency", readonly=True)
    domain = fields.Char(string="Domain", readonly=True)
    timezone = fields.Char(string="Timezone", readonly=True)
    locations = fields.One2many("ds.locations_tbl", "instance", readonly=True)
    active_status = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ('0', 'Pending'),
            ('1', 'Connected'),
            ('2', 'Failed'),
        ], default='0'
    )    # 0 means pending, 1 means connected, 2 means failed
    connection_msg = fields.Char(string="Connection Message")
    shopify_product_count = fields.Integer(string="Total Shopify Product", compute="count_shopify_products", default=0)
    odoo_product_count = fields.Char(string="Total Odoo Product", compute="count_odoo_products", default=0)
    shopify_order_count = fields.Char(string="Total Shopify Orders", compute="count_shopify_orders", default=0)
    shopify_customer_count = fields.Char(string="Total Shopify Customers", compute="count_shopify_customers", default=0)
    shopify_location_count = fields.Char(string="Total Store Locations", compute="count_store_location", default=0)
    created_date = fields.Datetime(string="Created Date", default=set_date)

    @api.constrains('store_url')
    def _validate_url(self):
        for rec in self:
            if ".myshopify.com" not in rec.store_url:
                raise ValidationError(_("Enter valid .myshopify.com shop url."))

    @api.model
    def create(self, instance_vals):
        instance_vals['store_name'] = (instance_vals["store_name"]).capitalize()
        is_insert = super(InstanceClass, self).create(instance_vals)  # InstanceClass is class name

        is_save = self.action_check_connection_for_store(record_data=is_insert)
        is_update = is_insert.write(is_save)
        if is_update:
            return is_insert
        return False

    def write(self, vals):
        if "store_name" in vals:
            vals['store_name'] = (vals["store_name"]).capitalize()
        super(InstanceClass, self).write(vals)  # InstanceClass is class name
        is_save = self.action_check_connection_for_store(record_data=self)
        is_update = super(InstanceClass, self).write(is_save)
        return is_update

    # CHECKING SHOPIFY CONNECTION
    def action_check_connection_for_store(self, record_data=None):
        update_record = {}
        shop_connection = self.env['shopify_odoo_connector_sp.common'].action_check_connection(instance_data=record_data)
        state = '2'
        connection_msg = "Failed"

        if shop_connection:
            connection_msg = "Connected"
            state = '1'

            shop_data = location_data = None
            try:
                shop_data = shopify.Shop.current().to_dict()
                location_data = shopify.Location.find()
            except Exception as e:
                file = open("custom/shopify_odoo_connector_sp/models/module_errors.txt", "a")
                now = datetime.now()
                error_data = {
                    "function": "action_check_connection_for_store instance model",
                    "error": str(e),
                    "date": now.strftime("%d-%m-%Y %H:%M:%S")
                }
                file.write(json.dumps(error_data))
                file.close()

            if shop_data:
                address1 = shop_data.get("address1")
                address2 = shop_data.get("address2")
                city = shop_data.get("city")
                country_name = shop_data.get("country_name")

                address = ''
                if address1 and address2:
                    address = "{}, {}".format(address1, address2)
                elif address1 and not address2:
                    address = address1
                elif not address1 and address2:
                    address = address2

                store_address = "{}, {}, {}".format(address, city, country_name)

                currency_symbol = (shop_data.get("money_format")).replace('{{amount}}', '')
                currency_symbol = currency_symbol.replace('{{amount_no_decimals}}', '')
                currency_symbol = currency_symbol.replace('{{amount_with_comma_separator}}', '')
                currency_symbol = currency_symbol.replace('{{amount_no_decimals_with_comma_separator}}', '')

                update_record.update({
                    "email": shop_data.get("email"),
                    "domain": shop_data.get("domain"),
                    "timezone": shop_data.get("iana_timezone"),
                    "address": store_address,
                    "currency": currency_symbol
                })

            # locations_arr = []
            if location_data:
                for locations in location_data:
                    get_all_locations = self.env['ds.locations_tbl'].search([
                        ('location_id', '=', locations.id)
                    ])

                    if not get_all_locations:
                        insert_location = {
                            'location_id': locations.id,
                            'location_name': locations.name,
                            'instance': record_data.id
                        }

                        self.env['ds.locations_tbl'].create(insert_location)
                    else:
                        get_all_locations.write({'location_name': locations.name})

            update_record.update({"connection_msg": connection_msg,"state": state})
        else:
            update_record.update({"connection_msg": connection_msg, "state": state})

        return update_record

    # COUNT TOTAL NUMBER OF SHOPIFY PRODUCTS
    def count_shopify_products(self):
        for rec in self:
            get_all_shopify_products = self.env['ds.products_tbl'].search([
                ('instance', '=', rec.id), ('odoo_product_id', '=', '0')
            ])
            rec.shopify_product_count = len(get_all_shopify_products)

    # COUNT TOTAL NUMBER OF ODOO PRODUCTS
    def count_odoo_products(self):
        for rec in self:
            get_all_odoo_products = self.env['ds.products_tbl'].search([
                ('instance', '=', rec.id), ('odoo_product_id', '!=', '0')
            ])
            rec.odoo_product_count = len(get_all_odoo_products)

    # COUNT TOTAL NUMBER OF SHOPIFY ORDERS
    def count_shopify_orders(self):
        for rec in self:
            get_all_shopify_orders = self.env['ds.order_tbl'].search([
                ('instance_id', '=', rec.id), ('order_id', '!=', '0')
            ])
            rec.shopify_order_count = len(get_all_shopify_orders)

    # COUNT TOTAL NUMBER OF SHOPIFY CUSTOMERS
    def count_shopify_customers(self):
        for rec in self:
            get_all_shopify_products = self.env['ds.customers_tbl'].search([
                ('instance', '=', rec.id)
            ])
            rec.shopify_customer_count = len(get_all_shopify_products)

    # COUNT TOTAL NUMBER OF SHOPIFY STORE LOCATIONS
    def count_store_location(self):
        for rec in self:
            get_all_shopify_products = self.env['ds.locations_tbl'].search([
                ('instance', '=', rec.id)
            ])
            rec.shopify_location_count = len(get_all_shopify_products)

    # FOR SMART BUTTON
    # DISPLAY PRODUCTS
    def display_products(self):
        return {
            'name': _('Products'),
            'domain': [('instance', '=', self.id)],  # VALUE WHICH WANT TO PASS
            'type': 'ir.actions.act_window',
            'res_model': 'ds.products_tbl',  # MODEL NAME
            'view_type': 'form',
            'view_mode': 'tree,form',  # DISPLAY MODE
            'target': 'current'
        }

    # FOR SMART BUTTON
    # DISPLAY ORDERS
    def display_orders(self):
        return {
            'name': _('Orders'),
            'domain': [('instance_id', '=', self.id)],  # VALUE WHICH WANT TO PASS
            'type': 'ir.actions.act_window',
            'res_model': 'ds.order_tbl',  # MODEL NAME
            'view_type': 'form',
            'view_mode': 'tree,form',  # DISPLAY MODE
            'target': 'current'
        }

    # FOR SMART BUTTON
    # DISPLAY CUSTOMERS
    def display_customers(self):
        return {
            'name': _('Customers'),
            'domain': [('instance', '=', self.id)],  # VALUE WHICH WANT TO PASS
            'type': 'ir.actions.act_window',
            'res_model': 'ds.customers_tbl',  # MODEL NAME
            'view_type': 'form',
            'view_mode': 'tree,form',  # DISPLAY MODE
            'target': 'current'
        }

    # FOR SMART BUTTON
    # DISPLAY LOCATIONS
    def display_locations(self):
        return {
            'name': _('Locations'),
            'domain': [('instance', '=', self.id)],  # VALUE WHICH WANT TO PASS
            'type': 'ir.actions.act_window',
            'res_model': 'ds.locations_tbl',  # MODEL NAME
            'view_type': 'form',
            'view_mode': 'kanban,form',  # DISPLAY MODE
            'target': 'current'
        }

    @api.onchange('active_status')
    def change_active_status(self):
        instance_id = self._origin.id

        get_cron_data = self.env['shopify_odoo_connector_sp.common'].search([
            ('to_instance', '=', instance_id), ('status', 'in', ['0', '1'])
        ])

        if get_cron_data:
            update_cron = get_cron_data.write({'is_active': self.active_status})
