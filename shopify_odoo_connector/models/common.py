from odoo import models, fields, api
from odoo.exceptions import Warning
import shopify
from datetime import datetime
import base64
import requests
import json
import pytz

india = pytz.timezone('Asia/Kolkata')


class CommonClass(models.Model):
    _name = "shopify_odoo_connector.common"
    EXEC_LIMIT = 5     # GLOBAL VARIABLE

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    is_active = fields.Boolean(string="Active", default=True)
    action_type = fields.Selection([
        ('1', 'Import'),
        ('2', 'Export'),
    ], default='0')
    from_instance = fields.Many2one("shopify_odoo_connector.instance_tbl", String="From Instance", ondelete="cascade")
    to_instance = fields.Many2one("shopify_odoo_connector.instance_tbl", String="To Instance", ondelete="cascade")
    product_ids = fields.Many2many("ds.products_tbl", String="Product Ids for action")
    last_cursor = fields.Text(String="Last Executed Data Cursor")
    status = fields.Selection([
        ('0', 'Pending'),
        ('1', 'Processing'),
        ('2', 'Completed'),
        ('3', 'Failed')
    ], default='0')
    type = fields.Selection([
        ('0', 'Products'),
        ('1', 'Orders'),
        ('2', 'Customers')
    ], default='0')
    fail_message = fields.Text(String="Fail Message")
    created_date = fields.Datetime(default=set_date)
    sync_end_date = fields.Datetime(String="Sync end date")

    # GET LAST SYNC DATA FROM CRON TABLE
    def get_last_sync_date(self, cron_type=0, action_type=None, to_instance_id=None, from_instance_id=None):
        last_sync_date = ''

        get_last_sync_data = None
        if action_type == '1':      # FOR IMPORT ACTION
            get_last_sync_data = self.env['shopify_odoo_connector.common'].search([
                ('to_instance', '=', to_instance_id), ('type', '=', cron_type), ('status', '=', '2'), ('is_active', '=', True),
                ('action_type', '=', '1')
            ], order='sync_end_date desc', limit=1)
        elif action_type == '2':    # FOR EXPORT ACTION
            get_last_sync_data = self.env['shopify_odoo_connector.common'].search([
                ('from_instance', '=', from_instance_id), ('to_instance', '=', to_instance_id), ('status', '=', '2'),
                ('is_active', '=', True), ('action_type', '=', '2')
            ], order='sync_end_date desc', limit=1)

        if get_last_sync_data:
            last_sync_date = get_last_sync_data.sync_end_date
        return last_sync_date

    # RUN CRON FILE FOR PRODUCT ACTIONS
    @api.model
    def perform_action_by_product_cron(self):
        # GLOBAL VARIABLE
        # WHEN CRON FILE WILL CALL. EXECUTE NUMBERS OF RECORDS
        EXECUTE_RECORDS = CommonClass.EXEC_LIMIT

        get_cron_data = self.env['shopify_odoo_connector.common'].search([
            ('status', '=', '1'), ('type', '=', '0'), ('is_active', '=', True)
        ])

        if not get_cron_data:
            get_cron_data = self.env['shopify_odoo_connector.common'].search([
                ('status', '=', '0'), ('type', '=', '0'), ('is_active', '=', True)
            ])

        if get_cron_data:
            get_cron_data = get_cron_data[0]
            action = get_cron_data[0].action_type
            last_cursor = get_cron_data[0].last_cursor

            if action == '1':   # FOR IMPORT ACTION
                instance = get_cron_data[0].to_instance
                import_data = self.import_product_from_shopify(instance=instance, next_page_url=last_cursor,
                                                               inserted_cron_data=get_cron_data, limit=EXECUTE_RECORDS,
                                                               last_sync_date=self.get_last_sync_date(cron_type=0, action_type=action,
                                                               to_instance_id=instance.id))
            elif action == '2':     # FOR EXPORT ACTION
                product_ids = get_cron_data[0].product_ids
                to_instance_id = get_cron_data[0].to_instance
                from_instance_id = get_cron_data[0].from_instance

                if not product_ids:
                    export_data = self.export_all_products_from_shopify(to_instance=to_instance_id,
                                                                        from_instance=from_instance_id,
                                                                        next_page_url=last_cursor,
                                                                        inserted_cron_data=get_cron_data,
                                                                        limit=EXECUTE_RECORDS,
                                                                       last_sync_date=self.get_last_sync_date(action_type=action,
                                                                                                            to_instance_id=to_instance_id.id,
                                                                                                            from_instance_id=from_instance_id.id))
                else:
                    export_data = self.export_shopify_product_by_action(instance=to_instance_id,
                                                                        product_ids=product_ids,
                                                                        next_page_url=last_cursor,
                                                                        inserted_cron_data=get_cron_data,
                                                                        limit=EXECUTE_RECORDS)

    # RUN CRON FILE FOR ORDER ACTIONS
    @api.model
    def perform_action_by_order_cron(self):
        # GLOBAL VARIABLE
        # WHEN CRON FILE WILL CALL. EXECUTE NUMBERS OF RECORDS
        EXECUTE_RECORDS = CommonClass.EXEC_LIMIT

        get_cron_data = self.env['shopify_odoo_connector.common'].search([
            ('status', '=', '1'), ('type', '=', '1'), ('is_active', '=', True)
        ])

        if not get_cron_data:
            get_cron_data = self.env['shopify_odoo_connector.common'].search([
                ('status', '=', '0'), ('type', '=', '1'), ('is_active', '=', True)
            ])

        if get_cron_data:
            get_cron_data = get_cron_data[0]
            action = get_cron_data[0].action_type
            last_cursor = get_cron_data[0].last_cursor

            if action == '1':
                instance = get_cron_data[0].to_instance

                import_data = self.import_orders_from_shopify(instance=instance, next_page_url=last_cursor,
                                                            inserted_cron_data=get_cron_data, limit=EXECUTE_RECORDS,
                                                            last_sync_date=self.get_last_sync_date(cron_type=1, action_type=action,
                                                                                                   to_instance_id=instance.id))

    # RUN CRON FILE FOR CUSTOMERS ACTIONS
    @api.model
    def perform_action_by_customer_cron(self):
        # GLOBAL VARIABLE
        # WHEN CRON FILE WILL CALL. EXECUTE NUMBERS OF RECORDS
        EXECUTE_RECORDS = CommonClass.EXEC_LIMIT

        get_cron_data = self.env['shopify_odoo_connector.common'].search([
            ('status', '=', '1'), ('type', '=', '2'), ('is_active', '=', True)
        ])

        if not get_cron_data:
            get_cron_data = self.env['shopify_odoo_connector.common'].search([
                ('status', '=', '0'), ('type', '=', '2'), ('is_active', '=', True)
            ])

        if get_cron_data:
            get_cron_data = get_cron_data[0]
            action = get_cron_data[0].action_type
            last_cursor = get_cron_data[0].last_cursor

            if action == '1':
                instance = get_cron_data[0].to_instance

                import_data = self.import_customers_from_shopify(instance=instance, next_page_url=last_cursor,
                                                                inserted_cron_data=get_cron_data, limit=EXECUTE_RECORDS,
                                                                last_sync_date=self.get_last_sync_date(cron_type=2, action_type=action,
                                                                                                       to_instance_id=instance.id))

    # CHECKING CONNECTION WITH SHOPIFY STORE
    def action_check_connection(self, instance_data=None):
        is_connected = False
        shop_url = "https://{}:{}@{}/admin/api/{}".format(instance_data["api_key"], instance_data["api_password"], instance_data["store_url"],
                                                            instance_data["shopify_version"])
        try:
            shopify.ShopifyResource.set_site(shop_url)
            shopify.Shop.current().to_dict()
            is_connected = True
        except Exception as e:
            is_connected = False
        return is_connected

    # MESSAGE WIZARD OPEN FUNCTION
    def message_wizard_open(self, view, name, message):
        # view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = message
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ds.message_wizard',
            'view_id': view.id,
            'target': 'new',
            'context': context
        }

    # CREATE RECORD IN DATABASE
    def create_record(self, table_name=None, data=None):
        if table_name and data:
            create_response = self.env[table_name].create(data)
            return create_response

    # UPDATE RECORD IN DATABASE
    def update_record(self, exist_data=None, data=None):
        update_response = False
        if exist_data and data:
            update_response = exist_data.write(data)

        return update_response

    # PRODUCT CREATE JSON WHILE INSERT IN DATATABLE
    def create_product_json(self, product_json=None, instance=None, odoo_product_id=None):
        create_product_data = ''
        if product_json:
            product_id = product_json.get("id")
            product_title = product_json.get("title")
            product_status = product_json.get("status")
            product_vendor = product_json.get("vendor")
            product_tags = product_json.get("tags")
            product_description = product_json.get("body_html")

            product_image = ''
            if product_json.get("image") and product_json.get("image").get("src"):
                product_image = base64.b64encode(
                    requests.get((product_json.get("image").get("src")).strip()).content).replace(b'\n', b'')

            if odoo_product_id:
                create_product_data = {
                    'product_id': product_id,
                    'product_title': product_title,
                    'product_image': product_image,
                    'vendor': product_vendor or "",
                    'tags': product_tags or "",
                    'product_status': product_status,
                    'instance': instance,
                    'description': product_description or "",
                    'odoo_product_id': odoo_product_id
                }
            else:
                create_product_data = {
                    'product_id': product_id,
                    'product_title': product_title,
                    'product_image': product_image,
                    'vendor': product_vendor or "",
                    'tags': product_tags or "",
                    'product_status': product_status,
                    'instance': instance,
                    'description': product_description or ""
                }
        return create_product_data

    # CUSTOMER CREATE JSON
    def create_customer_json(self, customer_json=None, instance=None):
        create_customer_data = ''
        if customer_json:
            name = ""
            phone = email = address = "--"
            orders_count = 0
            total_spent = 0

            if customer_json.get("first_name") and customer_json.get("last_name"):
                name = "{} {}".format(customer_json.get("first_name"), customer_json.get("last_name"))
            elif not customer_json.get("first_name") and customer_json.get("last_name"):
                name = "{}".format(customer_json.get("last_name"))
            elif customer_json.get("first_name") and not customer_json.get("last_name"):
                name = "{}".format(customer_json.get("first_name"))

            if customer_json.get("phone"):
                phone = customer_json.get("phone")

            if customer_json.get("email"):
                email = customer_json.get("email")

            if customer_json.get("total_spent"):
                total_spent = customer_json.get("total_spent")

            if customer_json.get("orders_count"):
                orders_count = customer_json.get("orders_count")

            cust_address_data = customer_json.get("default_address")
            if cust_address_data:
                if cust_address_data.get("address1"):
                    address = "{}".format(cust_address_data.get("address1"))
                if cust_address_data.get("address2"):
                    address += ", {}".format(cust_address_data.get("address2"))
                if cust_address_data.get("city"):
                    address += ", {}".format(cust_address_data.get("city"))
                if cust_address_data.get("country"):
                    address += ", {}".format(cust_address_data.get("country"))
                if cust_address_data.get("province"):
                    address += ", {}".format(cust_address_data.get("province"))
                if cust_address_data.get("zip"):
                    address += ", {}".format(cust_address_data.get("zip"))

            create_customer_data = {
                'customer_id': customer_json.get("id"),
                'name': name,
                'email': email,
                'phone': phone,
                'instance': instance.id,
                'orders_count': orders_count,
                'total_spent': "{}{}".format(instance.currency, float(total_spent)),
                'address': address
            }
        return create_customer_data

    # ORDER CREATE JSON
    def create_order_json(self, order_json=None, instance=None, inserted_id=None):
        create_order_data = ''

        if order_json:
            order_id = order_json.get("id")
            order_name = order_json.get("name")
            instance_id = instance.id
            shop_currency = instance.currency
            order_date = order_json.get("created_at")
            total_price = "{}{:.2f}".format(shop_currency, float(order_json.get("current_total_price")))
            subtotal_price = "{}{:.2f}".format(shop_currency, float(order_json.get("current_subtotal_price")))
            total_discounts = "{}{:.2f}".format(shop_currency, float(order_json.get("total_discounts")))
            total_tax = "{}{:.2f}".format(shop_currency, float(order_json.get("current_total_tax")))

            shipping_address = payment_status = fulfillment_status = '--'

            shipping_address_data = order_json.get("shipping_address")
            if shipping_address_data:
                if shipping_address_data.get("address1"):
                    shipping_address = "{}".format(shipping_address_data.get("address1"))
                if shipping_address_data.get("address2"):
                    shipping_address += ", {}".format(shipping_address_data.get("address2"))
                if shipping_address_data.get("city"):
                    shipping_address += ", {}".format(shipping_address_data.get("city"))
                if shipping_address_data.get("country"):
                    shipping_address += ", {}".format(shipping_address_data.get("country"))
                if shipping_address_data.get("province"):
                    shipping_address += ", {}".format(shipping_address_data.get("province"))
                if shipping_address_data.get("zip"):
                    shipping_address += ", {}".format(shipping_address_data.get("zip"))

            if order_json.get("financial_status"):
                payment_status = order_json.get("financial_status")

            if order_json.get("fulfillment_status"):
                fulfillment_status = order_json.get("fulfillment_status")

            create_order_data = {
                'order_id': order_id,
                'order_name': order_name,
                'instance_id': instance_id,
                'customer_id': inserted_id,
                'order_date': order_date,
                'total_price': total_price,
                'total_tax': total_tax,
                'subtotal_price': subtotal_price,
                'total_discounts': total_discounts,
                'shipping_address': shipping_address,
                'payment_status': payment_status,
                'fulfillment_status': fulfillment_status
            }
        return create_order_data

    # ORDER LINE ITEMS CREATE JSON
    def create_line_item_json(self, item=None, order_json=None, instance=None, inserted_order_id=None, inserted_product_id=None):
        create_line_item_data = ''
        if item:
            line_item_price = float(item.get("quantity"))*float(item.get("price"))
            create_line_item_data = {
                'line_item_id': item.get("id"),
                'sku': item.get("sku") or "--",
                'product_id': inserted_product_id,
                'order_id': order_json.get("id"),
                'inserted_order_id': inserted_order_id,
                'fulfill_qty': item.get("fulfillable_quantity"),
                'price': "{} {}".format(instance.currency, line_item_price),
                'quantity': item.get("quantity"),
                'instance_id': instance.id
            }
        return create_line_item_data

    # IMPORT PRODUCTS FROM SHOPIFY
    # CRON PROCESS OF IMPORT PRODUCTS
    def import_product_from_shopify(self, instance=None, next_page_url=None, inserted_cron_data=None, limit=None, last_sync_date=None):
        is_import = False
        message = ''

        if instance:
            shop_connection = self.action_check_connection(instance_data=instance)
            if shop_connection:
                response = None
                try:
                    if inserted_cron_data:
                        if next_page_url:
                            response = shopify.Product.find(from_=next_page_url)
                        else:
                            if not last_sync_date:
                                response = shopify.Product.find(limit=limit, fields="id,title,status,vendor,tags,body_html,variants,options,images,"
                                                                                    "image")
                            else:
                                response = shopify.Product.find(limit=limit,
                                                                fields="id,title,status,vendor,tags,body_html,variants,options,images,"
                                                                       "image", updated_at_min=last_sync_date)
                    else:
                        # INSERT CRON DATA
                        get_cron_data = self.env['shopify_odoo_connector.common'].search([
                            ('to_instance', '=', instance.id), ('action_type', '=', '1'), ('type', '=', '0'),
                            ('status', 'in', ['0', '1'])
                        ])

                        insert_cron = ''
                        if not get_cron_data:
                            insert_cron_data = {
                                'to_instance': instance.id,
                                'action_type': '1',
                                'status': '0'
                            }
                            insert_cron = self.env['shopify_odoo_connector.common'].create(insert_cron_data)

                        if insert_cron or get_cron_data:
                            message = 'Your imported products will be reflected in store within sometime.'
                            is_import = True
                        else:
                            message = 'Something went wrong. Please try again.'
                            is_import = False
                except Exception as e:
                    message = e

                if response:
                    for product in response:
                        product_json = product.to_dict()

                        is_product_already_exists = self.env["ds.products_tbl"].search(
                            [("product_id", "=", product_json.get("id")),
                             ("instance", "=", instance.id)])

                        if product_json:
                            if not is_product_already_exists:
                                # CREATE PRODUCT IF PRODUCT IS NOT EXISTS IN ODOO MODULE
                                create_product_data = self.create_product_json(product_json, instance.id)
                                if create_product_data:
                                    inserted_product_id = self.create_record(table_name="ds.products_tbl",data=create_product_data)

                                    if inserted_product_id:
                                        option_response = self.insert_product_extra_details_while_import(
                                            inserted_product_id.id, product_json, instance.id)

                                        if not option_response:
                                            is_import = False
                                            message = "Insert Product Error."
                                        else:
                                            is_import = True
                            else:
                                # UPDATE PRODUCT IF PRODUCT IS ALREADY EXISTS IN ODOO MODULE
                                update_product_data = self.create_product_json(product_json, instance.id)

                                if update_product_data:
                                    is_update_product = self.update_record(exist_data=is_product_already_exists, data=update_product_data)

                                    if is_update_product:
                                        is_deleted = self.delete_product_extra_details_before_update(
                                            is_product_already_exists.id, instance.id)

                                        if is_deleted:
                                            option_response = self.insert_product_extra_details_while_import(
                                                is_product_already_exists.id, product_json, instance.id)

                                            if not option_response:
                                                is_import = False
                                                message = "Update Product Error."
                                            else:
                                                is_import = True

                        next_page_url = response.next_page_url
                        if not next_page_url:
                            update_cron_data = {
                                'sync_end_date': (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S"),
                                'last_cursor': next_page_url,
                                'status': '2'
                            }
                        else:
                            update_cron_data = {
                                'last_cursor': next_page_url,
                                'status': '1'
                            }

                        if not is_import:
                            update_cron_data = {
                                'status': '3',
                                'fail_message': message
                            }

                        if is_import:
                            update_cron = inserted_cron_data.write(update_cron_data)

                            if not update_cron:
                                self.write_error_log("import_product_from_shopify", "Cron update error.")
            else:
                is_import = False
        else:
            is_import = False
        return {"is_import": is_import, "message": message}

    # DELETE EXISTING PRODUCT'S OPTION & VARIANTS
    def delete_product_extra_details_before_update(self, product_id=None, instance=None):
        is_deleted = False

        if product_id and instance:
            get_products_data = self.env['ds.products_tbl'].search([
                ('id', '=', product_id), ('instance', '=', instance),
            ])

            if get_products_data:
                # DELETE EXISTING OPTIONS
                if get_products_data.product_options:
                    option_ids = []
                    for val_id in get_products_data.product_options:
                        option_ids.append(val_id.id)

                    if option_ids:
                        is_option_delete = self.env['ds.product_options'].search([
                            ('id', 'in', option_ids)
                        ]).unlink()

                        if is_option_delete:
                            is_deleted = True

                # DELETE EXISTING VARIANTS
                if get_products_data.product_variants:
                    variant_ids = []
                    for val_id in get_products_data.product_variants:
                        variant_ids.append(val_id.id)

                    is_option_value_delete = self.env['ds.products_variants_tbl'].search([
                        ('id', 'in', variant_ids)
                    ]).unlink()

                    if is_option_value_delete:
                        is_deleted = True

                # DELETE PRODUCT IMAGES
                if get_products_data.p_images:
                    imgs_ids = []
                    for val_id in get_products_data.p_images:
                        imgs_ids.append(val_id.id)

                    is_images_delete = self.env['ds.product_images_tbl'].search([
                        ('id', 'in', imgs_ids)
                    ]).unlink()

                    if is_images_delete:
                        is_deleted = True

                # DELETE EXISTING VARIANTS INVENTORY
                get_variant_location_data = self.env['ds.variant_inventory_tbl'].search([
                    ('product_id', '=', product_id)
                ])

                variants_location_arr = []
                if get_variant_location_data:
                    for variant_location in get_variant_location_data:
                        variants_location_arr.append(variant_location.id)

                if variants_location_arr:
                    delete_variant_locations = self.env['ds.variant_inventory_tbl'].search([
                        ('id', 'in', variants_location_arr)
                    ]).unlink()

                    if delete_variant_locations:
                        is_deleted = True
        return is_deleted

    # INSERTING OPTIONS OF PRODUCT WHILE IMPORTING A PRODUCTS
    def insert_product_extra_details_while_import(self, product_inserted_id=None, product_json=None, instance_id=None):
        is_option_inserted = False
        product_template = None

        if product_json:
            product_id = product_json.get("id")
            is_product_exists_in_sales_module = self.env['product.template'].search([
                ('product_id', '=', product_id), ('instance', '=', instance_id)
            ])

            #  FOR PRODUCT MAIN IMAGE START
            product_image_data = product_json.get("image")

            product_main_image = None
            if product_image_data:
                product_src = product_image_data.get("src")
                if product_src:
                    product_main_image = base64.b64encode(requests.get(product_src.strip()).content).replace(b'\n', b'')
            #  FOR PRODUCT MAIN IMAGE END

            # CREATE PRODUCT IN SALES MODULE
            create_update_in_sales_module_data = {
                'name': product_json.get("title"),
                'instance': instance_id,
                'image_1920': product_main_image,
                'type': 'product',
                'list_price': 0,
                'is_published': True
            }

            if not is_product_exists_in_sales_module:  # CREATE PRODUCT IN SALES MODULE
                create_update_in_sales_module_data.update({'product_id': product_id})
                product_template = self.env['product.template'].create(create_update_in_sales_module_data)
            else:  # UPDATE PRODUCT IN SALES MODULE
                is_update_product_in_sales = is_product_exists_in_sales_module.write(create_update_in_sales_module_data)
                if is_update_product_in_sales:
                    product_template = is_product_exists_in_sales_module
                    vids_arr = []
                    for var_id in is_product_exists_in_sales_module.attribute_line_ids:
                        vids_arr.append(var_id.id)

                    is_variant_del_in_sales = self.env["product.template.attribute.line"].search([
                        ("id", "in", vids_arr)
                    ]).unlink()

                    if not is_variant_del_in_sales:
                        self.write_error_log("insert_product_extra_details_while_import", "Existing variant not deleted.")
                else:
                    self.write_error_log("insert_product_extra_details_while_import", "Product not updated in sales module.")

            # GET PRODUCT OPTIONS DATA START
            if product_json.get("options"):
                option = product_json.get("options")[0]

                if option.get("name") == "Title" and option.get("values")[0] == "Default Title":
                    for product_variant in product_json.get("variants"):
                        # Write weight unit
                        uom_category_id = self.env["uom.category"].search([("name", "=", "Weight")],limit=1)
                        uom_id = self.env["uom.uom"].search(
                            [("name", "in", ["kg", "KG"]),
                             ("category_id", "=", uom_category_id.id)], limit=1)
                        inst_uom_id = self.env["uom.uom"].search(
                            [("name", "=", product_variant.get("weight_unit")),
                             ("category_id", "=", uom_category_id.id)], limit=1)
                        weight = round(
                            inst_uom_id._compute_quantity(product_variant.get("weight"), uom_id), 2)

                        create_or_update_product_data = {
                                                            "name": product_json.get("title"),
                                                            'instance': instance_id,
                                                            'product_id': product_json.get("id"),
                                                            'image_1920': product_main_image,
                                                            "default_code": product_variant.get("sku"),
                                                            "type": "product",
                                                            "standard_price": product_variant.get("compare_at_price") or 0,
                                                            "list_price": product_variant.get("price"),
                                                            # "barcode": product_variant.get("barcode"),
                                                            "weight": weight,
                                                            'is_published': True
                                                        }

                        if not is_product_exists_in_sales_module:
                            product_tmpl_id = self.env['product.template'].create(create_or_update_product_data)
                            if not product_tmpl_id:
                                return False
                        else:
                            is_update_product = is_product_exists_in_sales_module.write(create_or_update_product_data)
                            if not is_update_product:
                                return False
                    return True

                attribute_line_ids_arr = []

                for option in product_json.get("options"):
                    inserted_option_values_id = []

                    # INSERT OPTION VALUES INTO TABLE
                    option_arr = []
                    sales_options_arr = []

                    # ADD PRODUCT ATTRIBUTE IN SALES MODULE
                    product_option_title = self.env["product.attribute"].search([("name", "=", option.get("name"))])

                    if not product_option_title:
                        product_option_title = self.env['product.attribute'].create({'name': option.get("name")})

                    for option_val in option.get("values"):
                        attribute_value_id = self.env["product.attribute.value"].search([("name", "=", option_val),
                                                                                         ("attribute_id", "=", product_option_title.id)])

                        if not attribute_value_id:
                            attribute_value_id = self.env['product.attribute.value'].create({
                                'name': option_val, 'attribute_id': product_option_title.id
                            })

                        sales_options_arr.append(attribute_value_id.id)

                        option_value_already_exists = self.env["ds.product_options_values"].search([
                            ('option_value', "=", option_val)
                        ])

                        if option_value_already_exists:
                            inserted_option_values_id.append(option_value_already_exists.id)
                        else:
                            option_values_data = {'option_value': option_val}
                            option_arr.append(option_values_data)

                    if sales_options_arr:
                        # SET ATTRIBUTE AND ATTRIBUTE VALUES ON THE TEMPLATE
                        self.env['product.template.attribute.line'].create([{
                            'attribute_id': product_option_title.id,
                            'product_tmpl_id': product_template.id,
                            'value_ids': [(6, 0, sales_options_arr)]
                        }])

                    if option_arr:
                        insert_option_values = self.create_record(table_name="ds.product_options_values", data=option_arr)

                        if insert_option_values:
                            for inserted_option_id in insert_option_values:
                                inserted_option_values_id.append(inserted_option_id.id)

                    # INSERT OPTIONS INTO TABLE
                    is_option_already_exists = self.env["ds.product_options"].search(
                        [('product_id', '=', product_json.get('id')), ('instance_id', '=', instance_id),
                         ('option_id', '=', option.get('id'))]
                    )

                    if not is_option_already_exists:
                        option_data = {
                            'product_id': product_json.get("id"),
                            'op_product_id': product_inserted_id,
                            'instance_id': instance_id,
                            'option_id': option.get("id"),
                            'option_name': option.get("name"),
                            'option_position': option.get("position"),
                            'op_val_id': inserted_option_values_id
                        }

                        insert_option = self.create_record(table_name="ds.product_options", data=option_data)
                        if insert_option:
                            is_option_inserted = True
                    else:
                        update_option_data = {
                            'option_name': option.get("name"),
                            'option_position': option.get("position"),
                            'op_val_id': inserted_option_values_id
                        }

                        update_option = self.update_record(exist_data=is_option_already_exists, data=update_option_data)

                        if update_option:
                            is_option_inserted = True
            # GET PRODUCT OPTIONS DATA END

            # PRODUCT ALL IMAGES DATA START
            product_images_arr = []
            if product_json.get("images"):
                for variant_image_data in product_json.get("images"):
                    v_image = variant_image_data.get("src")

                    is_product_image_exists = self.env["ds.product_images_tbl"].search([
                        ('product_id', '=', product_inserted_id),
                        ('product_image', '=', base64.b64encode(requests.get(v_image.strip()).content).replace(b'\n', b''))
                    ])

                    if not is_product_image_exists:      # FOR ALL IMAGES EXCEPT VARIANTS IMAGES
                        if not variant_image_data.get("variant_ids"):
                            product_image_data = {
                                "product_id": product_inserted_id,
                                "product_image": base64.b64encode(requests.get(v_image.strip()).content).replace(b'\n', b'')
                            }
                            product_images_arr.append(product_image_data)

                if product_images_arr:
                    is_insert_images = self.create_record(table_name="ds.product_images_tbl", data=product_images_arr)
                    if is_insert_images:
                        is_option_inserted = True
            # PRODUCT ALL IMAGES DATA END

            # GET PRODUCT VARIANTS DATA START
            if product_json.get("variants"):
                for variants in product_json.get("variants"):
                    attribute_value_ids = self.env["product.template.attribute.value"]
                    # CHECKING VARIANTS IMAGES AVAILABLE OR NOT
                    product_variant_image = ''

                    if product_json.get("images"):
                        for variant_image_data in product_json.get("images"):
                            v_image = variant_image_data.get("src")

                            # FOR VARIANT IMAGES
                            if variant_image_data.get("variant_ids"):  # PRODUCT VARIANTS IMAGES
                                if variants.get("id") in variant_image_data.get("variant_ids"):
                                    product_variant_image = base64.b64encode(
                                        requests.get(v_image.strip()).content).replace(b'\n', b'')

                    # VARIANT UPDATE IN SALES MODULE END
                    for count in range(len(product_json.get("options"))):
                        attribute_name = product_json.get("options")[count].get("name")
                        attribute_line_id = None
                        if product_template.attribute_line_ids:
                            attribute_line_id = product_template.attribute_line_ids.filtered(
                                lambda l: l.attribute_id.name == attribute_name)

                        option = "option" + str(count + 1)
                        if variants.get(option):
                            condition_list = [("name", "=", variants.get(option)),("attribute_id.name", "=", attribute_name)]
                            if attribute_line_id:
                                condition_list.append(("attribute_line_id", "=", attribute_line_id.id))
                            attribute_value_ids += self.env["product.template.attribute.value"].search(condition_list)

                    product_variant_id = product_template.product_variant_ids.filtered(  # TODO for remove new attribute value
                        lambda l: l.product_template_attribute_value_ids == attribute_value_ids
                    )

                    if product_variant_id:
                        uom_category_id = self.env["uom.category"].search([("name", "=", "Weight")], limit=1)
                        uom_id = self.env["uom.uom"].search(
                            [("name", "in", ["kg", "KG"]), ("category_id", "=", uom_category_id.id)], limit=1)
                        inst_uom_id = self.env["uom.uom"].search(
                            [("name", "=", variants.get("weight_unit")),
                             ("category_id", "=", uom_category_id.id)], limit=1)
                        weight = round(inst_uom_id._compute_quantity(variants.get("weight"), uom_id), 2)

                        # CREATE PRODUCT VARIANTS IN SALES MODULE
                        product_variant_id.write({
                            "default_code": variants.get("sku"),
                            # "price_extra": variants.get("price"),
                            'lst_price': float(variants.get("price")) or 0,
                            "standard_price": variants.get("compare_at_price") or 0,
                            "barcode": variants.get("barcode") or None,
                            "weight": weight,
                            "image_variant_1920": product_variant_image or None
                        })
                    # VARIANT UPDATE IN SALES MODULE END

                    is_variant_already_exists = self.env['ds.products_variants_tbl'].search(
                        [('instance_id', '=', instance_id), ('variant_id', '=', variants.get('id'))]
                    )

                    if not is_variant_already_exists:
                        variant_data = {
                            'instance_id': instance_id,
                            'product_id': product_inserted_id,
                            'variant_id': variants.get("id"),
                            'title': variants.get("title"),
                            'variant_image': product_variant_image,
                            'price': variants.get("price"),
                            'compare_at_price': variants.get("compare_at_price"),
                            'sku': variants.get("sku"),
                            'barcode': variants.get("barcode"),
                            'grams': variants.get("grams"),
                            'weight': variants.get("weight"),
                            'weight_unit': variants.get("weight_unit"),
                            'inventory_item_id': variants.get("inventory_item_id"),
                            'inventory_quantity': variants.get("inventory_quantity"),
                            # 'old_inventory_quantity': variants.get("old_inventory_quantity"),
                        }

                        insert_variant_data = self.create_record(table_name="ds.products_variants_tbl", data=variant_data)

                        if insert_variant_data:
                            is_location_added = self.get_set_inventory_locations_for_variants(variants.get("inventory_item_id"),
                                                insert_variant_data.id, product_inserted_id, instance_id)

                            if is_location_added:
                                is_option_inserted = True
                    else:
                        update_variant_data = {
                            'title': variants.get("title"),
                            'variant_image': product_variant_image,
                            'price': variants.get("price"),
                            'compare_at_price': variants.get("compare_at_price"),
                            'sku': variants.get("sku"),
                            'barcode': variants.get("barcode"),
                            'grams': variants.get("grams"),
                            'weight': variants.get("weight"),
                            'weight_unit': variants.get("weight_unit"),
                            'inventory_item_id': variants.get("inventory_item_id"),
                            'inventory_quantity': variants.get("inventory_quantity"),
                            # 'old_inventory_quantity': variants.get("old_inventory_quantity"),
                        }

                        update_variant = self.update_record(exist_data=is_variant_already_exists, data=update_variant_data)

                        if update_variant:
                            is_location_added = self.get_set_inventory_locations_for_variants(variants.get("inventory_item_id"),
                                                                        is_variant_already_exists.id, product_inserted_id, instance_id)
                            if is_location_added:
                                is_option_inserted = True
            # GET PRODUCT VARIANTS DATA END
        return is_option_inserted

    # GET SET INVENTORY LOCATIONS OF VARIANTS WHILE IMPORTING PRODUCTS DATA
    def get_set_inventory_locations_for_variants(self, inventory_item_id, insert_variant_data, product_inserted_id,
                                                 instance_id):
        is_location_added = False
        if inventory_item_id or insert_variant_data:
            try:
                inventory_data = shopify.InventoryLevel.find(inventory_item_ids=inventory_item_id)

                variant_location_arr = []
                if inventory_data:
                    for inventory in inventory_data:
                        location_data = shopify.Location.find(id_=inventory.location_id)

                        if location_data:
                            if location_data.id == inventory.location_id:
                                location_name = location_data.name

                                is_already_exists_location = self.env['ds.locations_tbl'].search([
                                    ('location_id', '=', inventory.location_id), ('instance', '=', instance_id)
                                ])

                                if not is_already_exists_location:
                                    create_location_data = {
                                        'location_id': inventory.location_id,
                                        'location_name': location_name or "",
                                        'instance': instance_id,
                                    }

                                    is_location_inserted = self.create_record(table_name="ds.locations_tbl", data=create_location_data)
                                    location_id_for_variant = is_location_inserted.id
                                else:
                                    location_id_for_variant = is_already_exists_location.id

                                get_variant_inventory_data = self.env['ds.variant_inventory_tbl'].search([
                                    ('inventory_item_id', '=', inventory.inventory_item_id),
                                    ('location_id', '=', inventory.location_id)
                                ])

                                if get_variant_inventory_data:
                                    update_location_data = {
                                        'location_name': location_name,
                                        'available': inventory.available,
                                    }

                                    update_location_data = self.update_record(exist_data=get_variant_inventory_data,
                                                                              data=update_location_data)

                                    if update_location_data:
                                        is_location_added = True
                                else:
                                    insert_location_data = {
                                        'product_id': product_inserted_id,
                                        'instance': instance_id,
                                        'inventory_item_id': inventory.inventory_item_id,
                                        'variant_id': insert_variant_data,
                                        'location_id': inventory.location_id,
                                        'location_name': location_name,
                                        'variant_location_id': location_id_for_variant,
                                        'available': inventory.available,
                                    }
                                    variant_location_arr.append(insert_location_data)

                    if variant_location_arr:
                        insert_location_data = self.create_record(table_name="ds.variant_inventory_tbl", data=variant_location_arr)

                        if insert_location_data:
                            is_location_added = True
            except Exception as e:
                self.write_error_log("get_set_inventory_locations_for_variants", str(e))
        return is_location_added

    # IMPORT ALL CUSTOMERS FROM SHOPIFY TO ODOO
    # CRON PROCESS OF IMPORT CUSTOMERS
    def import_customers_from_shopify(self, instance=None, next_page_url=None, inserted_cron_data=None, limit=None, last_sync_date=None):
        is_import = False
        message = 'Something went wrong.'

        if instance:
            shop_connection = self.action_check_connection(instance_data=instance)
            if shop_connection:
                response = None
                try:
                    if inserted_cron_data:
                        if next_page_url:
                            response = shopify.Customer.find(from_=next_page_url)
                        else:
                            if not last_sync_date:
                                response = shopify.Customer.find(limit=limit, fields="id,first_name,last_name,phone,email,total_spent,"
                                                                                     "orders_count,default_address")
                            else:
                                response = shopify.Customer.find(limit=limit,
                                                                 fields="id,first_name,last_name,phone,email,total_spent,orders_count,"
                                                                        "default_address", updated_at_min=last_sync_date)
                    else:
                        # INSERT CRON DATA
                        get_cron_data = self.env['shopify_odoo_connector.common'].search([
                            ('to_instance', '=', instance.id), ('action_type', '=', '1'), ('type', '=', '2'),
                            ('status', 'in', ['0', '1'])
                        ])

                        insert_cron = ''
                        if not get_cron_data:
                            insert_cron_data = {
                                'to_instance': instance.id,
                                'action_type': '1',
                                'type': '2',
                                'status': '0'
                            }
                            insert_cron = self.env['shopify_odoo_connector.common'].create(insert_cron_data)

                        if insert_cron or get_cron_data:
                            message = 'Your imported data will be reflected in store within sometime.'
                            is_import = True
                        else:
                            message = 'Something went wrong. Please try again.'
                            is_import = False

                    if response:
                        for customer_data in response:
                            customer_json = customer_data.to_dict()
                            customer_data = self.create_customer_json(customer_json, instance)

                            is_customer_exists = self.env['ds.customers_tbl'].search([
                                ('customer_id', '=', customer_json.get("id")), ('instance', '=', instance.id)
                            ])

                            if not is_customer_exists:
                                customer_response = self.create_record(table_name="ds.customers_tbl", data=customer_data)
                            else:
                                customer_response = self.update_record(exist_data=is_customer_exists, data=customer_data)

                            if customer_response:
                                is_import = True
                                message = "Customer Imported Successfully."
                            else:
                                is_import = False
                                message = "Customer Imported Failed."

                            next_page_url = response.next_page_url
                            if not next_page_url:
                                update_cron_data = {
                                    'sync_end_date': (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S"),
                                    'last_cursor': next_page_url,
                                    'status': '2'
                                }
                            else:
                                update_cron_data = {
                                    'last_cursor': next_page_url,
                                    'status': '1'
                                }

                            if not is_import:
                                update_cron_data = {
                                    'status': '3',
                                    'fail_message': message
                                }

                            if is_import:
                                update_cron = inserted_cron_data.write(update_cron_data)

                                if not update_cron:
                                    self.write_error_log("import_customers_from_shopify", "Update Cron Failed.")
                except Exception as e:
                    self.write_error_log("import_customers_from_shopify", str(e))
            else:
                message = "Connection Failed!!"
        return {"is_import": is_import, "message": message}

    # IMPORT ALL ORDERS FROM SHOPIFY TO ODOO
    # CRON PROCESS OF IMPORT ORDERS
    def import_orders_from_shopify(self, instance=None, next_page_url=None, inserted_cron_data=None, limit=None, last_sync_date=None):
        is_import = False
        message = ''

        if instance:
            shop_connection = self.action_check_connection(instance_data=instance)
            if shop_connection:
                response = None
                try:
                    if inserted_cron_data:
                        if next_page_url:
                            response = shopify.Order.find(from_=next_page_url)
                        else:
                            if not last_sync_date:
                                response = shopify.Order.find(limit=limit, fields="id,name,number,order_number,created_at,current_total_price,"
                                                                                  "current_subtotal_price,total_discounts,current_total_tax,"
                                                                                  "shipping_address,financial_status,fulfillment_status,customer,"
                                                                                  "line_items,customer")
                            else:
                                response = shopify.Order.find(limit=limit,
                                                              fields="id,name,number,order_number,created_at,current_total_price,"
                                                                     "current_subtotal_price,total_discounts,current_total_tax,"
                                                                     "shipping_address,financial_status,fulfillment_status,customer,"
                                                                     "line_items,customer", updated_at_min=last_sync_date)
                    else:
                        # INSERT CRON DATA
                        get_cron_data = self.env['shopify_odoo_connector.common'].search([
                            ('to_instance', '=', instance.id), ('type', '=', '1'), ('action_type', '=', '1'),
                            ('status', 'in', ['0', '1'])
                        ])

                        insert_cron = ''
                        if not get_cron_data:
                            insert_cron_data = {
                                'to_instance': instance.id,
                                'type': '1',
                                'action_type': '1',
                                'status': '0'
                            }

                            insert_cron = self.env['shopify_odoo_connector.common'].create(insert_cron_data)

                        if insert_cron or get_cron_data:
                            message = 'Your imported orders will be reflected in store within sometime.'
                            is_import = True
                        else:
                            message = 'Something went wrong. Please try again.'
                            is_import = False

                    if response:
                        instance_id = instance.id
                        for order_data in response:
                            order_json = order_data.to_dict()

                            order_id = order_json.get("id")

                            if order_json:
                                is_data_added = self.insert_order_related_data(order_json=order_json, instance=instance)

                                if is_data_added:
                                    is_import = is_data_added.get("is_import")
                                    message = is_data_added.get("message")

                            next_page_url = response.next_page_url

                            if not next_page_url:
                                update_cron_data = {
                                    'sync_end_date': (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S"),
                                    'last_cursor': next_page_url,
                                    'status': '2'
                                }
                            else:
                                update_cron_data = {
                                    'last_cursor': next_page_url,
                                    'status': '1'
                                }

                            if not is_import:
                                update_cron_data = {
                                    'status': '3',
                                    'fail_message': message
                                }

                            if is_import:
                                update_cron = inserted_cron_data.write(update_cron_data)

                                if not update_cron:
                                    self.write_error_log("import_orders_from_shopify", "Update Cron Failed.")

                except Exception as e:
                    message = e
            else:
                message = "Connection Failed!!"
        return {"is_import": is_import, "message": message}

    # EXPORT ALL PRODUCTS OF ONE STORE TO ANOTHER STORE FROM EXPORT OPTION IN MENUBAR
    # CRON PROCESS OF EXPORT PRODUCTS
    def export_all_products_from_shopify(self, to_instance=None, from_instance=None, next_page_url=None,
                                         inserted_cron_data=None, limit=None, last_sync_date=None):
        is_export = False
        message = ''

        if not last_sync_date:
            all_products_ids = self.env['ds.products_tbl'].search([('instance', '=', from_instance.id)])
        else:
            all_products_ids = self.env['ds.products_tbl'].search([
                ('instance', '=', from_instance.id), ('updated_date', '>', last_sync_date) or ('created_date', '>', last_sync_date)
            ])

        if all_products_ids:
            shop_connection = self.action_check_connection(instance_data=to_instance)
            if shop_connection:
                start = 0
                end = limit
                total_records = len(all_products_ids)

                if next_page_url:
                    start = int(next_page_url)
                    end = start + end

                    if total_records < end:
                        end = total_records

                if not inserted_cron_data:
                    check_cron_is_exists_or_not = self.env['shopify_odoo_connector.common'].search([
                        ('to_instance', '=', to_instance.id), ('from_instance', '=', from_instance.id),
                        ('status', 'in', ['0', '1']), ('action_type', '=', '2')
                    ])

                    insert_cron = ''
                    if not check_cron_is_exists_or_not:
                        insert_cron_data = {
                            'to_instance': to_instance.id,
                            'from_instance': from_instance.id,
                            'action_type': '2',
                            'status': '0'
                        }
                        insert_cron = self.env['shopify_odoo_connector.common'].create(insert_cron_data)

                    if insert_cron or check_cron_is_exists_or_not:
                        message = 'Your products will be reflected in shopify store within sometime.'
                        is_export = True
                    else:
                        message = 'Something went wrong. Please try again.'
                        is_export = False
                    all_products_ids = []

                if all_products_ids:
                    # for product in all_products_ids(start, end):
                    for product in range(start, end):

                        get_export_product_data = self.env['ds.products_tbl'].search([
                            ('id', '=', all_products_ids[product].id)
                        ])

                        product_options = get_export_product_data.product_options
                        product_variants = get_export_product_data.product_variants

                        # GET ATTRIBUTES & ITS VALUES & VARIANTS FROM DATATABLES
                        resp = self.get_options_and_variants(product_options, product_variants)

                        export_product_res = self.create_update_product_in_shopify_store(get_product_data=get_export_product_data,
                                                                                         instance=to_instance, resp=resp)

                        if export_product_res != "":
                            is_export = export_product_res["is_export"]
                            message = export_product_res["message"]

                    if total_records == end:
                        update_cron_data = {
                            'sync_end_date': (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S"),
                            'last_cursor': end,
                            'status': '2'
                        }
                    else:
                        update_cron_data = {
                            'last_cursor': end,
                            'status': '1'
                        }

                    if not is_export:
                        update_cron_data = {
                            'status': '3',
                            'fail_message': message
                        }

                    update_cron = ''
                    if is_export:
                        update_cron = inserted_cron_data.write(update_cron_data)

                    if not update_cron:
                        self.write_error_log("export_all_products_from_shopify", "Update Cron File Failed.")
            else:
                is_export = False
        else:
            message = 'No data found in Odoo {} store. You can export only imported data!!'.format(from_instance.store_name)
            is_export = False
        return {'is_export': is_export, 'message': message}

    # EXPORT PRODUCTS FROM ODOO TO SHOPIFY BY ACTION
    def export_product_from_odoo_to_shopify_by_action(self, instance=None):
        is_export = False

        if instance:
            product_ids = self.browse(self._context.get("active_ids"))     # FETCH ALL SELECTED PRODUCTS ID

            shop_connection = self.action_check_connection(instance_data=instance)
            if shop_connection:
                for product in product_ids:

                    is_already_exported_in_shopify = self.env['ds.products_tbl'].search([
                        ('odoo_product_id', '=', product.id), ('instance', '=', instance.id)
                    ])

                    get_product_data = self.env['ds.odoo_products_tbl'].search([
                        ('id', '=', product.id)
                    ])

                    if get_product_data:
                        product_options = get_product_data.product_options
                        product_variants = get_product_data.product_variants

                        # GET ATTRIBUTES & ITS VALUES & VARIANTS FROM DATATABLES
                        resp = self.get_options_and_variants(option_ids=product_options, variant_ids=product_variants)

                        is_shopify_product_deleted_pid = ''

                        is_mode = "create"
                        if not is_already_exported_in_shopify:  # CREATE PRODUCT DATA JSON FOR CREATE PRODUCT IN STORE
                            product_data = self.create_update_product_json_data(product_data=get_product_data, resp=resp)
                        else:
                            update_product_id = is_already_exported_in_shopify.product_id

                            is_product_exists = None
                            try:
                                is_product_exists = shopify.Product.find(ids=update_product_id)
                            except Exception as e:
                                self.write_error_log("export_product_from_odoo_to_shopify_by_action checking product exists", str(e))

                            if not is_product_exists:
                                is_shopify_product_deleted_pid = update_product_id
                                product_data = self.create_update_product_json_data(product_data=get_product_data, resp=resp)
                            else:
                                is_mode = 'update'
                                product_data = self.create_update_product_json_data(product_data=get_product_data,
                                                                                    resp=resp,
                                                                                    shopify_product_id=update_product_id)

                        product_create_response = None
                        try:
                            product_create_response = shopify.Product.create(product_data)
                        except Exception as e:
                            self.write_error_log("export_product_from_odoo_to_shopify_by_action", str(e))

                        if product_create_response:
                            exported_product_json = product_create_response.to_dict()

                            if resp and resp.get("variants"):
                                is_variant_created = self.create_variant_with_images(resp_data=resp,
                                                                                     product_id=exported_product_json.get("id"))

                                if is_variant_created:
                                    exported_product_json = is_variant_created.to_dict()

                            create_product_data = self.create_product_json(exported_product_json, instance.id, product.id)

                            if is_mode == "create":
                                if is_shopify_product_deleted_pid != "":
                                    is_delete_old_product = self.env["ds.products_tbl"].search([
                                        ("product_id", '=', is_shopify_product_deleted_pid)
                                    ]).unlink()

                                    delete_old_sales_record = self.env["product.template"].search([
                                        ("product_id", "=", is_shopify_product_deleted_pid)
                                    ]).unlink()

                                    if not is_delete_old_product or not delete_old_sales_record:
                                        self.write_error_log("export_product_from_odoo_to_shopify_by_action old record delete",
                                                             "Old record deletion failed.")

                                inserted_product_id = self.create_record(table_name="ds.products_tbl", data=create_product_data)

                                if inserted_product_id:
                                    option_response = self.insert_product_extra_details_while_import(
                                        inserted_product_id.id, exported_product_json, instance.id)

                                    if option_response:
                                        exported_ids = get_product_data.exported_in

                                        export_arr = []
                                        if exported_ids:
                                            for e_id in exported_ids:
                                                export_arr.append(e_id.id)

                                            export_arr.append(instance.id)
                                        else:
                                            export_arr.append(instance.id)

                                        update_odoo_product = get_product_data.write({
                                            'exported_in': export_arr
                                        })

                                        if update_odoo_product:
                                            is_export = True
                            elif is_mode == "update":
                                is_update_product = self.update_record(exist_data=is_already_exported_in_shopify, data=create_product_data)

                                if is_update_product:
                                    is_deleted = self.delete_product_extra_details_before_update(
                                        is_already_exported_in_shopify.id, instance.id)

                                    if is_deleted:
                                        option_response = self.insert_product_extra_details_while_import(
                                            is_already_exported_in_shopify.id, exported_product_json, instance.id)

                                        if option_response:
                                            is_export = True
        return is_export

    # EXPORT SHOPIFY PRODUCT FROM ONE STORE TO ANOTHER STORE BY ACTION
    # CRON PROCESS OF EXPORT PRODUCTS TO SAME OR ANOTHER STORE
    def export_shopify_product_by_action(self, instance=None, product_ids=None, next_page_url=None, inserted_cron_data=None, limit=None):
        is_export = False
        message = ''
        if instance:
            shop_connection = self.action_check_connection(instance_data=instance)
            if shop_connection:

                total_records = 0
                if not product_ids:
                    product_ids = self.browse(self._context.get("active_ids"))  # FETCH ALL SELECTED PRODUCTS ID
                    total_records = len(product_ids)

                    limit = CommonClass.EXEC_LIMIT if limit is None else limit

                    if total_records > limit:
                        # INSERT CRON DATA
                        get_cron_data = self.env['shopify_odoo_connector.common'].search([
                            ('to_instance', '=', instance.id), ('action_type', '=', '2'), ('status', 'in', ['0', '1']),
                            ('product_ids', '!=', '')
                        ])

                        insert_cron = None
                        if not get_cron_data:
                            selected_product_ids = []
                            for pid in product_ids:
                                selected_product_ids.append(pid.id)

                            insert_cron_data = {
                                'to_instance': instance.id,
                                'action_type': '2',
                                'product_ids': selected_product_ids,
                                'status': '0',
                            }
                            insert_cron = self.env['shopify_odoo_connector.common'].create(insert_cron_data)
                        else:
                            existing_products = new_product_ids = []
                            existing_product_ids = get_cron_data.product_ids

                            if existing_product_ids:
                                for pid in existing_product_ids:
                                    existing_products.append(pid.id)

                            for pid in product_ids:
                                new_product_ids.append(pid.id)

                            if new_product_ids:
                                for pid in new_product_ids:
                                    if pid not in existing_products:
                                        existing_products.append(pid)

                            update_cron_data = {
                                'product_ids': existing_products
                            }
                            insert_cron = get_cron_data.write(update_cron_data)

                        if insert_cron or get_cron_data:
                            message = 'Your products will be reflected in shopify store within sometime.'
                            is_export = True
                        else:
                            message = 'Something went wrong. Please try again.'
                            is_export = False
                        product_ids = []

                if product_ids:
                    total_records = len(product_ids)
                    start = 0
                    end = limit or total_records

                    if total_records < end:
                        end = total_records

                    all_product_ids = []
                    for pid in product_ids:
                        all_product_ids.append(pid.id)

                    for product in range(start, end):
                        get_product_data = self.env['ds.products_tbl'].search([
                            ('id', '=', product_ids[product].id)
                        ])

                        if get_product_data:
                            product_options = get_product_data.product_options
                            product_variants = get_product_data.product_variants

                            # GET ATTRIBUTES & ITS VALUES & VARIANTS FROM DATATABLES
                            resp = self.get_options_and_variants(option_ids=product_options, variant_ids=product_variants,
                                                                 shopify_product_id=get_product_data.product_id)

                            export_product_res = self.create_update_product_in_shopify_store(
                                get_product_data=get_product_data,
                                instance=instance, resp=resp)

                            if export_product_res != "":
                                is_export = export_product_res["is_export"]
                                message = export_product_res["message"]

                            if inserted_cron_data:
                                if all_product_ids:
                                    del all_product_ids[product]

                                if not is_export:
                                    update_cron_data = {
                                        'status': '3',
                                        'fail_message': message
                                    }
                                else:
                                    update_cron_data = {
                                        'product_ids': all_product_ids or [(6, 0, all_product_ids)],
                                    }
                                    if not all_product_ids:
                                        update_cron_data.update({'status': '2'})
                                    else:
                                        update_cron_data.update({'status': '1'})

                                update_cron = ''
                                if is_export:
                                    update_cron = inserted_cron_data.write(update_cron_data)

                                if not update_cron:
                                    self.write_error_log("export_shopify_product_by_action", "Update Cron Failed.")
        else:
            is_export = False
            message = "Instance not found!!"
        return {"is_export": is_export, 'message': message}

    # GET OPTIONS & VARIANTS OF PRODUCT
    def get_options_and_variants(self, option_ids=None, variant_ids=None, shopify_product_id=None):
        options = []
        variants = []
        resp = []
        product_variant_images_arr = []

        if option_ids:
            for options_data in option_ids:
                option_name = options_data.option_name
                option_position = options_data.option_position
                op_val_id = options_data.op_val_id

                values_ids_arr = []
                if op_val_id:
                    for val_id in op_val_id:
                        values_ids_arr.append(val_id.id)

                get_product_option_value = self.env['ds.product_options_values'].search([
                    ('id', 'in', values_ids_arr)
                ])

                values_arr = []
                if get_product_option_value:
                    for option_values_data in get_product_option_value:
                        values_arr.append(option_values_data.option_value)

                    options.append({"name": option_name, "values": values_arr})

            if variant_ids:
                for variant_data in variant_ids:

                    title = variant_data.title
                    title_split = title.split(" / ")
                    total_number_of_options = len(title_split)

                    variant_detail = {
                        'option1': title_split[0],
                        'option2': total_number_of_options in [2, 3] and title_split[1] or "",
                        'option3': total_number_of_options == 3 and title_split[2] or "",
                        'price': variant_data.price,
                        'sku': variant_data.sku or "",
                        'weight': variant_data.weight or "",
                        'weight_unit': variant_data.weight_unit or "kg",
                        'barcode': variant_data.barcode or "",
                        'image': variant_data.variant_image or ""
                    }
                    variants.append(variant_detail)
            else:
                variants.append({"option1": "Default Title",
                                 "price": "",
                                 "sku": "",
                                 "weight": "",
                                 "weight_unit": "kg",
                                 "barcode": ""})

        resp = {'options': options, 'variants': variants, 'variants_images': product_variant_images_arr}
        return resp

    # CREATE VARIANTS ON OPTION CHANGE
    def create_variant_onchange(self, table_name=None, product_options=None, instance=None, insert_id=None):
        variants_inserted_ids = ''
        if table_name and product_options:
            option_value1_arr = []
            option_value2_arr = []
            option_value3_arr = []
            for op_id in product_options:

                value_array = []
                # option_arr = []
                for op_value_data in op_id.op_val_id:
                    attribute_option_value = op_value_data.option_value
                    value_array.append(attribute_option_value)

                if value_array and not option_value1_arr:
                    option_value1_arr = value_array
                elif value_array and option_value1_arr and not option_value2_arr:
                    option_value2_arr = value_array
                elif value_array and option_value1_arr and option_value2_arr and not option_value3_arr:
                    option_value3_arr = value_array

            final_variants_array = []
            if option_value1_arr or option_value2_arr or option_value3_arr:
                if option_value1_arr and not option_value2_arr and not option_value3_arr:
                    final_variants_array = option_value1_arr
                elif option_value1_arr and option_value2_arr and not option_value3_arr:
                    for value1 in option_value1_arr:
                        for value2 in option_value2_arr:
                            final_variants_array.append("{} / {}".format(value1, value2))
                elif option_value1_arr and option_value2_arr and option_value3_arr:
                    for value1 in option_value1_arr:
                        for value2 in option_value2_arr:
                            for value3 in option_value3_arr:
                                final_variants_array.append("{} / {} / {}".format(value1, value2, value3))

                if final_variants_array:
                    variant_array = []
                    for variant_title in final_variants_array:
                        if instance:
                            variant_data = {
                                'title': variant_title,
                                'product_id': insert_id if insert_id else "",
                                'instance_id': instance
                            }
                        else:
                            variant_data = {
                                'title': variant_title,
                                'product_id': insert_id if insert_id else "",
                            }

                        variant_array.append(variant_data)

                    insert_variant = self.env[table_name].create(variant_array)

                    if insert_variant:
                        variants_inserted_ids = insert_variant
                    else:
                        self.write_error_log("create_variant_onchange", "Variant insertion error")

        return variants_inserted_ids

    # EDIT AND EXPORT PRODUCT IN SHOPIFY STORE
    # def edit_and_export_product_by_button(self, product_data, instance):
    def edit_and_export_product_by_button(self, product_data=None):
        is_update = False
        if product_data:
            product_inserted_id = product_data.id
            instance = product_data.instance
            shop_connection = self.action_check_connection(instance_data=instance)
            if shop_connection:

                # GET ATTRIBUTES & ITS VALUES & VARIANTS FROM DATATABLES
                resp = self.get_options_and_variants(option_ids=product_data.product_options, variant_ids=product_data.product_variants,
                                                     shopify_product_id=product_data.product_id)

                export_product_res = self.create_update_product_in_shopify_store(
                    get_product_data=product_data,
                    instance=instance, resp=resp)

                if export_product_res != "":
                    is_update = export_product_res["is_export"]

        return is_update

    # PRODUCT DATA FOR CREATE/UPDATE PURPOSE IN STORE
    def create_update_product_json_data(self, product_data=None, resp=None, shopify_product_id=0):
        update_product_in_shopify = None
        if product_data:
            # GET PRODUCT IMAGES
            product_all_images = product_data.p_images

            prod_images_arr = []
            for p_img_data in product_all_images:
                prod_images_arr.append({"attachment": p_img_data.product_image})

            # if resp and resp.get('variants_images'):
            #     prod_images_arr.extend(resp.get("variants_images"))

            update_product_in_shopify = {
                'title': product_data.product_title or "",
                'status': product_data.product_status or "",
                'product_price': product_data.product_price,
                'body_html': product_data.description if product_data.description != "--" else "",
                'vendor': product_data.vendor if product_data.vendor != "--" else "",
                'tags':  product_data.tags if product_data.tags != "--" else "",
                'options': resp.get('options') if resp and resp.get('options') else [{"name": "Title", "position": 1}],
                'variants': resp.get('variants') if resp and resp.get('variants') else [{"option1": "Default Title"}],
                'images': prod_images_arr
            }

            if shopify_product_id != 0:
                update_product_in_shopify.update({'id': shopify_product_id})

        return update_product_in_shopify

    # CHECKING PRODUCT ALREADY EXPORTED IN STORE OR NOT
    def check_exported_or_not(self, get_product_data=None, instance=None, is_shopify=True, shopify_product_id=0):
        is_export = False
        if get_product_data:
            get_ids = get_product_data.exported_instances_and_ids

            existing_data = {}
            if get_ids:
                existing_data = json.loads(get_ids)

            existing_data.update({instance.store_name: shopify_product_id})

            if is_shopify:      # MANAGING FOR SHOPIFY PRODUCT
                exported_ids = get_product_data.exported_instance
            else:       # MANAGING FOR ODOO PRODUCTS
                exported_ids = get_product_data.exported_in

            export_arr = []
            if exported_ids:
                for e_id in exported_ids:
                    export_arr.append(e_id.id)

            export_arr.append(instance.id)

            if is_shopify:  # MANAGING FOR SHOPIFY PRODUCT
                update_product = get_product_data.write({
                    'exported_instance': export_arr,
                    'exported_instances_and_ids': json.dumps(existing_data)
                })
            else:       # MANAGING FOR ODOO PRODUCTS
                update_product = get_product_data.write({
                    'exported_in': export_arr
                })

            if update_product:
               is_export = True
        return is_export

    # CREATE OR UPDATE PRODUCT IN SHOPIFY STORE
    def create_update_product_in_shopify_store(self, get_product_data=None, instance=None, resp=None):
        is_export = False
        message = "Something went wrong."

        # CHECKING PRODUCT ALREADY EXISTS IN STORE OR NOT START
        product_exported_ids = get_product_data.exported_instance
        exported_arr = []

        if product_exported_ids:
            for export_data in product_exported_ids:
                exported_arr.append(export_data.id)
        # CHECKING PRODUCT ALREADY EXISTS IN STORE OR NOT END

        # CHECKING ID IS AVAILABLE IN EXPORTED DATA HISTORY START
        get_ids = get_product_data.exported_instances_and_ids

        is_odoo_product_id = get_product_data.odoo_product_id

        existing_data = {}
        if get_ids:
            existing_data = json.loads(get_ids)

        update_product_id = 0
        if existing_data:
            if instance.store_name in existing_data.keys():
                update_product_id = existing_data[instance.store_name]

        mode = "create"
        old_product_id = ""
        product_data = {}

        if (exported_arr and (instance.id in exported_arr)) or (get_product_data.instance.id == instance.id) or (update_product_id != 0):
            update_product_id = update_product_id if update_product_id != 0 else get_product_data.product_id
            product_response = None
            try:
                product_response = shopify.Product.find(ids=update_product_id)
            except Exception as e:
                self.write_error_log("create_update_product_in_shopify_store checking product exists", str(e))

            if product_response:
                mode = "update"
                product_data = self.create_update_product_json_data(product_data=get_product_data, shopify_product_id=update_product_id)
            else:
                old_product_id = update_product_id
                product_data = self.create_update_product_json_data(product_data=get_product_data)
        else:
            product_data = self.create_update_product_json_data(product_data=get_product_data)

        product_response = None
        try:
            product_response = shopify.Product.create(product_data)
        except Exception as e:
            self.write_error_log("create_update_product_in_shopify_store", str(e))

        if product_response:
            product_json = product_response.to_dict()

            variant_data_arr = []
            if resp and resp.get("variants"):
                is_variant_created = self.create_variant_with_images(resp_data=resp, product_id=product_json.get("id"))
                if is_variant_created:
                    product_json = is_variant_created.to_dict()

            if not product_json:
                is_export = False
                message = 'Product exported failed.'
            else:
                option_response = {}
                if mode == "update":
                    update_product_id = product_json.get("id")

                    shopify_product_data_qry = self.env['ds.products_tbl'].search([
                        ('product_id', '=', update_product_id), ('instance', '=', instance.id)
                    ])

                    update_product_data = self.create_product_json(product_json, instance.id)

                    if update_product_data:
                        is_update_product = self.update_record(exist_data=shopify_product_data_qry, data=update_product_data)

                        if is_update_product:
                            is_deleted = self.delete_product_extra_details_before_update(shopify_product_data_qry.id, instance.id)

                            if is_deleted:
                                option_response = self.insert_product_extra_details_while_import(
                                    shopify_product_data_qry.id, product_json, instance.id)
                elif mode == "create":
                    if old_product_id != "":
                        old_record_delete = self.env["ds.products_tbl"].search([
                            ("product_id", "=", old_product_id), ("instance", "=", instance.id)
                        ]).unlink()

                        delete_old_sales_record = self.env["product.template"].search([
                            ("product_id", "=", old_product_id), ("instance", "=", instance.id)
                        ]).unlink()

                        if not old_record_delete or not delete_old_sales_record:
                            self.write_error_log("create_update_product_in_shopify_store", "Error while delete old record which is "
                                                                                           "not exists in shopify store")

                    create_product_data = self.create_product_json(product_json, instance.id)

                    if create_product_data:
                        if is_odoo_product_id != 0:     # CREATED PRODUCT IS ODOO PRODUCT
                            create_product_data.update({"odoo_product_id": is_odoo_product_id})
                            inserted_product_id = self.create_record(table_name="ds.products_tbl", data=create_product_data)
                        else:       # CREATED PRODUCT IS SHOPIFY PRODUCT
                            inserted_product_id = self.create_record(table_name="ds.products_tbl", data=create_product_data)

                        if inserted_product_id:
                            # get_product_data = inserted_product_id
                            option_response = self.insert_product_extra_details_while_import(
                                inserted_product_id.id, product_json, instance.id)

                if option_response:
                    is_exported_res = self.check_exported_or_not(get_product_data=get_product_data,
                                                                 instance=instance, is_shopify=True,
                                                                 shopify_product_id=product_json.get("id"))

                    if is_exported_res:
                        is_export = True
                        message = 'Product exported successfully.'
                else:
                    is_export = False
                    message = 'Product exported failed.'
        return {"is_export": is_export, 'message': message}

    # CREATE VARIANT WITH IMAGES
    def create_variant_with_images(self, resp_data=None, product_id=None):
        product_update_response = None
        variant_data_arr = []

        if resp_data:
            for variant_data in resp_data.get("variants"):
                update_variant_data = {
                    'option1': variant_data.get("option1"),
                    'option2': variant_data.get("option2"),
                    'option3': variant_data.get("option3"),
                    'price': variant_data.get("price"),
                    'sku': variant_data.get("sku"),
                    'weight': variant_data.get("weight"),
                    'weight_unit': variant_data.get("weight_unit")
                }

                if variant_data.get("image") != "":
                    upload_image = None
                    try:
                        upload_image = shopify.Image.create({"attachment": variant_data.get("image"), "product_id": product_id})
                    except Exception as e:
                        self.write_error_log("create_variant_with_images create image api", str(e))

                    if upload_image:
                        upload_image_dict = upload_image.to_dict()
                        update_variant_data.update({"image_id": upload_image_dict.get("id")})

                variant_data_arr.append(update_variant_data)

            try:
                product_update_response = shopify.Product.create(
                    {'options': resp_data.get('options'), 'variants': variant_data_arr, 'id': product_id})
            except Exception as e:
                self.write_error_log("create_variant_with_images update product api", str(e))

        return product_update_response

    # SYNC ORDER PROCESS
    def sync_order_from_shopify(self, instance=None, order=None):
        is_import = False
        message = ''
        if instance:
            shop_connection = self.action_check_connection(instance_data=instance)
            if shop_connection:
                response = None
                try:
                    if order:
                        response = shopify.Order.find(order)
                        if response:
                            instance_id = instance.id
                            order_json = response.to_dict()
                            order_id = order_json.get("id")
                            if order_json:
                                is_data_added = self.insert_order_related_data(order_json=order_json, instance=instance)

                                if is_data_added:
                                    is_import = is_data_added.get("is_import")
                                    message = is_data_added.get("message")
                except Exception as e:
                    is_import = False
                    message = e
            else:
                message = "Connection Failed!!"
        return {"is_import": is_import, "message": message}

    # ORDER RELATED DETAILS INSERT INTO TABLES(ORDER, CUSTOMERS,LINE ITEMS)
    def insert_order_related_data(self, order_json=None, instance=None):
        is_import = False
        message = "Something went wrong."

        if order_json and instance:
            order_id = order_json.get("id")
            customer_json_data = order_json.get("customer")

            if customer_json_data:
                customer_main_id = customer_json_data.get("id")
                customer_json = None
                try:
                    customer_json_api = shopify.Customer.find(customer_main_id, fields="id,first_name,last_name,phone,email,total_spent,"
                                                                                       "orders_count,default_address")
                    customer_json = customer_json_api.to_dict()
                except Exception as e:
                    self.write_error_log("insert_order_related_data", str(e))

                if customer_json:
                    is_customer_exists = self.env['ds.customers_tbl'].search([
                        ('customer_id', '=', customer_main_id)
                    ])
                    customer_data = self.create_customer_json(customer_json, instance)
                    inserted_id = 0
                    if not is_customer_exists:
                        customer_response = self.create_record(table_name="ds.customers_tbl", data=customer_data)
                        if customer_response:
                            inserted_id = customer_response.id
                    else:
                        customer_response = self.update_record(exist_data=is_customer_exists, data=customer_data)
                        if customer_response:
                            inserted_id = is_customer_exists.id

                    is_order_exists = self.env['ds.order_tbl'].search([
                        ('order_id', '=', order_id), ('instance_id', '=', instance.id)
                    ])
                    order_data = self.create_order_json(order_json, instance, inserted_id)

                    inserted_order_id = 0
                    if not is_order_exists and inserted_id != 0:
                        order_response = self.create_record(table_name="ds.order_tbl", data=order_data)
                        if order_response:
                            inserted_order_id = order_response.id
                    else:
                        order_response = self.update_record(exist_data=is_order_exists, data=order_data)
                        if order_response:
                            inserted_order_id = is_order_exists.id

                    # LINE ITEMS DATA INSERT / UPDATE
                    if order_response:
                        line_item_data = order_json.get("line_items")
                        if line_item_data:
                            for item in line_item_data:
                                is_line_item_exists = self.env['ds.order_line_items_tbl'].search([
                                    ('line_item_id', '=', item.get("id")),
                                    ('instance_id', '=', instance.id)
                                ])

                                get_product_insert_id = self.env['ds.products_tbl'].search([
                                    ('product_id', '=', item.get("product_id")),
                                    ('instance', '=', instance.id)
                                ])

                                line_item_res = None
                                inserted_product_id = 0
                                if get_product_insert_id:
                                    # PRODUCT ALREADY EXISTS IN STORE
                                    inserted_product_id = get_product_insert_id.id
                                else:
                                    # PRODUCT NOT EXISTS IN STORE
                                    if item.get("product_id"):
                                        product_response = shopify.Product.find(ids=item.get("product_id"))

                                        if product_response:
                                            for product in product_response:
                                                product_json = product.to_dict()
                                                if product_json:
                                                    create_product_data = self.create_product_json(
                                                        product_json, instance.id)

                                                    if create_product_data:
                                                        inserted_product_id = self.create_record(
                                                            table_name="ds.products_tbl",
                                                            data=create_product_data)

                                                        if inserted_product_id:
                                                            inserted_product_id = inserted_product_id.id

                                                            option_response = \
                                                                self.insert_product_extra_details_while_import(
                                                                    inserted_product_id, product_json, instance.id)
                                                            if not option_response:
                                                                is_import = False
                                                                message = "Insert Product Error."
                                                            else:
                                                                is_import = True
                                    else:
                                        line_item_res = True

                                if inserted_product_id != 0:
                                    line_item_data = self.create_line_item_json(item, order_json,
                                                                                instance,
                                                                                inserted_order_id,
                                                                                inserted_product_id)
                                    if not is_line_item_exists:
                                        line_item_res = self.create_record(
                                            table_name="ds.order_line_items_tbl",
                                            data=line_item_data)
                                    else:
                                        line_item_res = self.update_record(
                                            exist_data=is_line_item_exists,
                                            data=line_item_data)
                                if line_item_res:
                                    is_import = True
                                    message = "Order Update Successfully."
                                else:
                                    is_import = False
                                    message = "Order Update Failed."
            else:
                is_import = True
                message = "Order Update Successfully."
        return {"is_import": is_import, "message": message}

    # WRITE ERRORS IN FILE
    def write_error_log(self, function_name=None, message=None):
        file = open("custom/shopify_odoo_connector/models/module_errors.txt", "a")
        now = datetime.now(india)
        error_data = {
            "function": function_name,
            "error": message,
            "date": now.strftime("%d-%m-%Y %H:%M:%S")
        }
        file.write(json.dumps(error_data) + "\n")
        file.close()