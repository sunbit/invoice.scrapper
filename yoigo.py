# -*- coding: utf-8 -*-
from base import InvoiceImporter


class YoigoInvoices(InvoiceImporter):
    company = 'yoigo'
    name = 'Yoigo'

    base_url = 'https://miyoigo.yoigo.com'
    login_url = '{}/miyoigo-backend/auth'.format(base_url)
    invoices_url = '{}/miyoigo-backend/api/invoice?_dc=1384267374266&page=1&start=0&limit=25'.format(base_url)

    def _login(self):
        data = {
            'username': self.username,
            'password': self.password,
        }
        self.browser.post(self.login_url, data=data, verify=False)

    def _get_invoices(self):
        response = self.browser.get(self.invoices_url, verify=False)
        invoices = []

        for item in [f for f in response.json() if f['pdfLink']]:
            invoice = {}
            invoice['date'] = '-'.join(item['invoiceDate'].split('/')[::-1])

            if not self._invoice_exists(invoice):
                invoice['url'] = '{}{}'.format(self.base_url, item['pdfLink'])
                invoice['name'] = self._invoice_name(invoice)
                invoices.append(invoice)

        return invoices
