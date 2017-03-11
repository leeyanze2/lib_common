def base_html(request):
    from generic_ecom.settings import NV_CLIENT_DETAILS
    return {
        'nv_client': {
            "shop_name": NV_CLIENT_DETAILS.get("SHOP_NAME", "")
        }
    }
