# -*- coding: utf-8 -*-
from pyquery import PyQuery
import re
from base import InvoiceImporter


class SoreaInvoices(InvoiceImporter):
    company = 'sorea'
    name = 'Sorea'
    base_url = 'https://www.aguasonline.es/sorea/ofvirtual'
    home_url = '{}/home.aspx'.format(base_url)
    contracts_preload_url = '{}/Cargando.aspx?pgContratos.aspx'.format(base_url)
    contracts_url = '{}/Contratos.aspx'.format(base_url)
    loader_url = '{}/cargando1.aspx'.format(base_url)

    def update_viewstate(self, response):
        pq = PyQuery(response.content)
        self.viewstate = pq('input[name=__VIEWSTATE]').val()

    def _login(self):
        response = self.browser.get(self.home_url, verify=False)
        self.update_viewstate(response)
        data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': self.viewstate,
            'CWRegistro1:tboxUsuario': self.username,
            'CWRegistro1:tboxClave': self.password,
            'CWRegistro1:cmdEntrar': 'entrar'
        }
        response = self.browser.post(self.home_url, data=data, verify=False)
        response = self.browser.get(self.loader_url)
        self.update_viewstate(response)

    def _forge_pdf_url(self, item):
        pq = PyQuery(item)
        href = pq(item).find('a').attr('href')
        pdfid = re.search(r"doPostBack\('(.*?)'", href).groups()[0]

        data = {
            '__EVENTTARGET': pdfid.replace('$', ':'),
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': self.viewstate,
        }
        response = self.browser.post(self.contracts_url, data=data, verify=False)
        params = re.search(r"AbreFactura1\('(\w+)',(\w+),(\w+),'(\w+)','(\w+)','([\w,-\.]+)','([\w/]+)','(\w+)','(\w+)'", response.content).groups()

        qs = "ns={}&na={}&nper={}&npol={}&nf={}&ni={}&ne={}&idDoc={}&idDocFact={}".format(*params)
        url = '{}/verfacturas.aspx?{}'.format(self.base_url, qs)

        response = self.browser.get(url, verify=False)
        if 'verfacturas' not in response.url:
            self.log(u'  > Invoice not available now, try again later')
            return None

        srcs = [PyQuery(frame).attr('src') for frame in PyQuery(response.content).find('frame')]
        return '{}/{}'.format(self.base_url, srcs[1])

    def _get_invoices(self):
        response = self.browser.get(self.contracts_preload_url, verify=False)
        response = self.browser.get(self.contracts_url, verify=False)
        self.update_viewstate(response)
        data = {
            '__EVENTTARGET': 'botonFacturacion',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': self.viewstate,
        }
        response = self.browser.post(self.contracts_url, data=data, verify=False)
        self.update_viewstate(response)
        pq = PyQuery(response.content)
        items = pq('table#dgridFacturas tr')[1:]

        invoices = []
        for item in items:
            invoice = {}

            text = pq(item).find('td a').text()
            invoice_parts = re.search(r'((?:\w)+)\s+(\d+/\d+/\d+)\s+([\w-]+)\s+([\d\.,-]+)\s+', text)

            if invoice_parts is not None:
                numinvoice, date, period, amount = invoice_parts.groups()

                invoice['date'] = '-'.join(date.split('/')[::-1])
                invoice['name'] = self._invoice_name(invoice)

                if not self._invoice_exists(invoice):
                    invoice['url'] = self._forge_pdf_url(item)

                    if invoice['url']:
                        invoices.append(invoice)

        return invoices
