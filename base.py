# -*- coding: utf-8 -*-
import requests
import traceback
import os
import smtplib
from email.mime.text import MIMEText
import time


MESSAGE = u"""La següent factura s'ha afegit a la carpeta del Dropbox:

{}

"""


class InvoiceImporter(object):
    def __init__(self, **kwargs):
        """
            Sets all kwargs options as class attributes and prepares a browser
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.name = unicode(self.name)

        self.browser = requests.Session()
        self.browser.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36'}
        )
        self.log(u'\n* Searching {} invoices...'.format(self.name))

    def save_response(self, response, folder='.', name='response.html'):
        """
            Stores a response body to disk
        """
        open(u'{}/{}'.format(folder, name), 'w').write(response.content)

    def send_mail(self, subject, message):
        """
            Send the message to the current task recipients
        """
        msg = MIMEText(message.encode('utf-8'))
        msg['Subject'] = subject
        msg['From'] = self.notification_mail
        msg['To'] = ','.join(self.recipients)

        try:
            mailer = smtplib.SMTP('localhost')
            mailer.sendmail(self.notification_mail, self.recipients, msg.as_string())
            mailer.quit()
        except:
            self.log(u"    x Error when sending mail")
            print msg.as_string()

    def log(self, message):
        print message
        self.logger.info(message)

    def login(self, debug=False):
        """
            Safely executes a task custom login method.
            Repeats without catching error for debugging if required.
        """
        try:
            self._login()
        except Exception:
            trcback = traceback.format_exc()
            self.send_mail(u"Error al fer login: factures {} \n\n{}".format(self.name, trcback), u"")

            if debug:
                self.login()

    def _login(self):
        """
            Method to be implemented by custom importers, must leave the self.browser
            in an authenticated status
        """
        pass

    def _get_invoices(self):
        """
            Method to be implemented by custom importers, must return a list of dicts,
            containing at least date, name, and url of the invoice
        """
        pass

    def _get_folder(self):
        """
            Constructs the folder name for this task.
            Repeats without catching error for debugging if required.
        """
        folder_name = '{}/{}'.format(os.path.expanduser(self.invoices_folder), self.name)
        #mkdir(folder_name, p=True)
        return folder_name

    def save_invoices(self, debug=False):
        """
            Safely executes a task custom save_invoices method
        """
        try:
            self._save_invoices()
        except Exception:
            trcback = traceback.format_exc()
            self.send_mail(u"Error al descarregar: factures {} \n\n{}".format(self.name, trcback), u"")
            if debug:
                self._login()

    def _download_pdf(self, invoice):
        """
            Downloads a pdf using the parameters defined in the invoice
        """
        request_method = invoice.get('method', 'get')
        requester = getattr(self.browser, request_method)
        extra_args = {}
        extra_args['verify'] = False
        data = invoice.get('data', None)
        if request_method == 'post' and data:
            extra_args['data'] = data

        response = requester(invoice['url'], **extra_args)
        if response.headers['content-type'] in ['application/octet-stream', 'application/pdf']:
            self.save_response(response, name=invoice['name'], folder=self._get_folder())
            self.log(u'    · {} Saved'.format(invoice['name']))
            return True
        else:
            self.log(u'    x {} Not saved, this is not a pdf file.'.format(invoice['name']))
            return False

    def _save_invoices(self):
        """
            Gets the new_invoices list of the custom importer, and
            downloads them. Notifies user when done.
        """
        new_invoices = self._get_invoices()
        if new_invoices:
            self.log(u'  > Found {} new invoices'.format(len(new_invoices)))
            for invoice in new_invoices:
                time.sleep(self.delay_between_downloads)
                success = self._download_pdf(invoice)
                if success:
                    self.send_mail('Nova factura {}'.format(self.name), MESSAGE.format(invoice['name']))

        else:
            self.log('  > There are no new invoices')

    def _invoice_name(self, invoice):
        """
            Forges the filename of the invoice, based on invoice date.
            Expects a dict with at least a "date" key
        """
        user = unicode(getattr(self, 'user', ''))
        user = u' {}'.format(user) if user else u''

        invoice_name = u'FACTURA {}{} {}.pdf'.format(self.name.upper(), user, invoice['date'])
        return invoice_name

    def _invoice_exists(self, invoice):
        """
            Checks if the invoice is already dowloaded in the importer folder
        """
        exists = os.path.exists(u'{}/{}'.format(self._get_folder(), self._invoice_name(invoice)))
        return exists








