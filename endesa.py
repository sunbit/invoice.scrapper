# -*- coding: utf-8 -*-
from pyquery import PyQuery
import re
import random
import datetime
from collections import OrderedDict
import math
from base import InvoiceImporter


class EndesaInvoices(InvoiceImporter):
    company = 'endesa'
    name = 'Endesa'
    base_url = 'https://www.endesaclientes.com'
    login_url = '{}/sso/login'.format(base_url)
    post_login_url = '{}/oficina/gestiononline?neolpostlogin=true'.format(base_url)
    invoices_url = '{}/oficina/mis-facturas.html?random='.format(base_url)
    search_invoices_url = '{}/obtenerBuscadorFacturasGP.do'.format(base_url)

    def _login(self):
        data = OrderedDict()
        data['location'] = 'ib-es',
        data['loginurl'] = '/Login.html',
        data['service'] = '/oficina/gestiononline',
        data['alias'] = self.username,
        data['password'] = self.password,
        data['loginButton'] = 'Acceder'

        self.browser.headers.update({
            'Referer': 'https://www.endesaclientes.com',
            'Pragma': 'no-cache'
        })
        response = self.browser.post(self.login_url, data=data, verify=False)
        self.browser.get(self.post_login_url, verify=False)

    def _pdf_download_url(self, invoice):
        randomnum = str(int(math.floor((random.random() * 99999) + 1)))

        data = OrderedDict()
        data['pagename'] = 'SiteEntry_IB_ES/Bill_Search/ValidateClientDownloadBill'
        data['locale'] = 'null'
        data['jsonDownloadPdf'] = '{{"billSearch":{{"billNumber":"{billNumber}","secBill":"{secBill}","contractNumber":"","holderCompanyCode":"{holderCompanyCode}","businessLine":"{businessLine}","numscct":"","refBill":"{refBill}"}}}}'.format(**invoice)
        data['billNum'] = invoice['billNumber']

        randomnum = str(int(math.floor((random.random() * 99999) + 1)))
        response = self.browser.post('https://www.endesaclientes.com/ss/Satellite?rand=' + randomnum, data=data, verify=False)
        return '{}/{}'.format(
            self.base_url,
            re.search(r'location.href=\'(.*?)\'', response.content).groups()[0]
        )

    def _get_invoices(self):
        randomnum = str(int(math.floor((random.random() * 99999) + 1)))
        response = self.browser.get('https://www.endesaclientes.com/ss/Satellite?c=Page&pagename=SiteEntry_IB_ES%2FBill_Search%2FSearch_List&rand={}'.format(randomnum))
        pq = PyQuery(response.content)
        invoices = []

        def getParam(name, rowid):
            return pq.find('input[id={}_{}]'.format(name, rowid))[0].value

        for row in pq.find('.invoices_body_row'):
            invoice = {}
            row_id = row.attrib['id'].replace('trBill', '')
            invoice['billNumber'] = getParam('numBill', row_id)
            invoice['secBill'] = getParam('secBill', row_id)
            invoice['contractNumber'] = getParam('contractNumber', row_id)
            invoice['holderCompanyCode'] = getParam('holderCompanyCode', row_id)
            invoice['businessLine'] = getParam('businessLine', row_id)
            invoice['numscct'] = ''
            invoice['refBill'] = getParam('refBill', row_id)

            date = pq(row).find('td')[3].text.strip()
            invoice['date'] = datetime.datetime.strptime(date, '%a %b %d %H:%M:%S %Z %Y').strftime('%Y-%m-%d')

            if not self._invoice_exists(invoice):
                invoice['method'] = 'get'
                invoice['url'] = self._pdf_download_url(invoice)
                invoice['name'] = self._invoice_name(invoice)
                invoices.append(invoice)
        return invoices
