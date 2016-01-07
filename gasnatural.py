# -*- coding: utf-8 -*-
from pyquery import PyQuery
import re
from base import InvoiceImporter


class GasNaturalInvoices(InvoiceImporter):
    company = 'gasnatural'
    name = 'Gas Natural'
    base_url = 'https://areaprivada.gasnaturalfenosa.es/ovh-web'
    login_url = '{}/Login.gas?submitBtn=Entra'.format(base_url)
    invoices_url = '{}/SearchInvoiceAndConsumptionList.gas'.format(base_url)
    pdf_url = '{}/DownloadInvoice.gas'.format(base_url)

    def _login(self):
        self.browser.get(self.login_url, verify=False)
        data = {
            'submitBtn': 'submitBtn',
            'language': 'es',
            'acceder': 'Acceder',
            'username': self.username,
            'password': self.password,
        }
        self.browser.post(self.login_url, data=data, verify=False)

    def get_page_pdf_urls(self, response):
        urls = []
        pq = PyQuery(response.content)
        hrefs = [PyQuery(a).attr('href') for a in pq('table#listado_facturas tbody tr td div a')]
        for href in hrefs:
            if href.startswith('/gp/'):
                urls.append((href.split('/gp/')[-1], None))
            else:
                params = re.findall(r"'(.*?)'", href)
                urls.append(('op=PDF&cfactura={}&cd_contrext={}'.format(*params[:2]), params))
        return urls

    def _get_invoices(self):
        response = self.browser.get(self.invoices_url, verify=False)
        pq = PyQuery(response.content)

        invoices = []

        for pdflink in pq.find('span.factura a'):
            invoice = {}

            date = pq(pdflink).text().strip()
            invoice['date'] = '-'.join(date.split('/')[::-1])
            link = pq(pdflink).attr('href')
            invoice_number = re.search(r'invoiceNumber=(\w+)&', link).groups()[0]
            if not self._invoice_exists(invoice):
                invoice['url'] = '{}?invoiceNumber={}&target=%2FInvoiceDetail'.format(self.pdf_url, invoice_number)
                invoice['name'] = self._invoice_name(invoice)
                invoices.append(invoice)

        return invoices
