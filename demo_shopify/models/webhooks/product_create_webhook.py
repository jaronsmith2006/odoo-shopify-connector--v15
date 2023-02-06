from flask import Flask, request
from flask import json


app = Flask(__name__)


@app.route('/test_webhook', methods=['POST'])
def test_webhook():
    if request.method == "POST":
        try:
            print(request.data)
            print(request.url)
            return 'success'

            product_json = request.data
            if product_json:
                product_id = product_json.get("id")
                product_title = product_json.get("title")
                product_status = product_json.get("status")
                product_vendor = product_json.get("vendor")
                product_tags = product_json.get("tags")

                product_image = ''
                if product_json.get("image") and product_json.get("image").get("src"):
                    # product_image = (product_json.get("image").get("src"))
                    product_image = base64.b64encode(
                        requests.get((product_json.get("image").get("src")).strip()).content).replace(b'\n', b'')

                create_product_data = {
                    # 'store_name': instance.store_name,
                    'product_id': product_id,
                    'product_title': product_title,
                    'product_image': product_image,
                    'vendor': product_vendor,
                    'tags': product_tags,
                    'product_status': product_status,
                    # 'instance': instance.id
                }

                create_product_response = self.env['ds.products_tbl'].create(create_product_data)

                inserted_product_id = ''
                if create_product_response:
                    inserted_product_id = create_product_response.id

                option_response = self.env['demo_shopify.common'].insert_product_extra_details_while_import(inserted_product_id, product_json, instance.id)

                # if not option_response:
                #     is_import = False

        except Exception as e:
            print("error: ", e)
        return 'success'
    else:
        print("Webhook not called")


if __name__ == "__main__":
    app.run()
