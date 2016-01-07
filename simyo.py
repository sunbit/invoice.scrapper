# -*- coding: utf-8 -*-
from pyquery import PyQuery
import re
from base import InvoiceImporter


class SimyoInvoices(InvoiceImporter):
    company = 'simyo'
    name = 'Simyo'

    base_url = 'https://www.simyo.es'
    login_url = '{}/simyo/publicarea/login/j_security_check'.format(base_url)
    invoices_url = '{}/simyo/privatearea/customer/invoice.htm'.format(base_url)

    def _login(self):
        data = {
            'j_username': self.username,
            'j_password': self.password,
        }

        resp = self.browser.post(self.login_url, data=data, verify=False)
        if resp.status_code == 401:
            raise Exception('Error on Simyo login, possibly captcha detected')

    def _get_invoices(self):
        response = self.browser.get(self.invoices_url, verify=False)
        invoices = []
        html = response.content
        pq = PyQuery(html)

        for item in pq('table#lista_facturas td.pdf a'):
            href = item.attrib['href']
            month, year = re.search(r'invoiceNO=\d+(\d{2})(\d{2})', href).groups()

            invoice = {}
            # As we don't have the day of the month, assume a safe-late number
            invoice['date'] = '-'.join([str(year), str(month), '29'])

            if not self._invoice_exists(invoice):
                invoice['url'] = '{}{}'.format(self.base_url, href)
                invoice['name'] = self._invoice_name(invoice)
                invoices.append(invoice)
        return invoices
