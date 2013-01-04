from cached import Resource

from lib.bango.client import get_client
from lib.bango.constants import PAYMENT_TYPES
from lib.bango.forms import CreateBillingConfigurationForm
from lib.bango.signals import create


class CreateBillingConfigurationResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'billing'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = CreateBillingConfigurationForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        client = get_client()
        billing = client.client('billing')

        data = form.bango_data
        # Exclude transaction from Bango but send it to the signal later.
        transaction_uuid = data.pop('transaction_uuid')

        types = billing.factory.create('ArrayOfString')
        for f in PAYMENT_TYPES:
            types.string.append(f)
        data['typeFilter'] = types

        price_list = billing.factory.create('ArrayOfPrice')
        for item in form.cleaned_data['prices']:
            price = billing.factory.create('Price')
            price.amount = item.cleaned_data['amount']
            price.currency = item.cleaned_data['currency']
            price_list.Price.append(price)

        data['priceList'] = price_list

        config = billing.factory.create('ArrayOfBillingConfigurationOption')
        configs = {
            'APPLICATION_CATEGORY_ID': '18',
            'APPLICATION_SIZE_KB': 2,
            'BILLING_CONFIGURATION_TIME_OUT': 120,
            'REDIRECT_URL_ONSUCCESS': data.pop('redirect_url_onsuccess'),
            'REDIRECT_URL_ONERROR': data.pop('redirect_url_onerror'),
        }
        for k, v in configs.items():
            opt = billing.factory.create('BillingConfigurationOption')
            opt.configurationOptionName = k
            opt.configurationOptionValue = v
            config.BillingConfigurationOption.append(opt)

        data['configurationOptions'] = config
        resp = get_client().CreateBillingConfiguration(data)
        bundle.data = {'responseCode': resp.responseCode,
                       'responseMessage': resp.responseMessage,
                       'billingConfigurationId': resp.billingConfigurationId}

        # Uncomment this when bug 820198 lands.
        # Until then, transactions are managed in webpay not solitude.
        create_data = data.copy()
        create_data['transaction_uuid'] = transaction_uuid
        create.send(sender=self, bundle=bundle, data=create_data, form=form)
        return bundle
