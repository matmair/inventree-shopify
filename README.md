# inventree-shopify

Integrate your [InvenTree](https://inventree.org) instance stock with [Shopify](https://www.shopify.com/).

## Features

Sync changes between Shopify inventory levels (nventory per location) and InvenTree stock items. Only supports non-serialized InvenTree stock items at the moment.

## Installation

1. Install in your instance via [pip install method](https://docs.inventree.org/en/latest/extend/plugins/install/?h=plugin#plugin-installation-file-pip).
  - Add "inventree-shopify" to plugins.txt
  - Run "invoke update" from inventree-server. See (https://docs.inventree.org/en/latest/start/docker_install/#update-database)
2. Add a private app to your Shopify store.
  - Use the scopes: "write_inventory, read_inventory, write_product_listings, read_product_listings, write_products, read_products"
3. Go to the inventree-shopify settings in InvenTree and fill in the settings for the plugin from your new private app.
  - Use the "Admin API access token" in "API Passwort"
  - Use the "API key" in "API Key"
  - USe the "API secret key" in "API Shared Secret"
4. Click the webhooks link in the settings - make sure your instance is reachable for shopify.
5. Open the Shopify plane in InvenTree. You can now link your Shopify inventroy levels to your InvenTree stock items.

## Caveat

Your instance must be reachable for webhooks from Shopify so use ngrok or something like that to expose your instance with HTTPS.
Open your instance on that URL for the first setup.

## State of the code

This code is only running on a few instances with rarely used Shopify stores (maybe 40-50 inventory shifts a month). It is not tested with a lot of inventory shifts and it is not tested with a lot of different Shopify stores. So use it at your own risk.

If you use this more extensively please let me know so I can remove this warning.

## Contribute

Feel free to submit issues or feature requests here or just send me a mail to code AT mjmair DOT com

## License

This code is licensed under MIT. I persume no liability for any damages and do not provide any warranty.
