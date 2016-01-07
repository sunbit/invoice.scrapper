# invoice.scrapper
Invoice automatic scrapper
===========================

This collection of scripts, property configured as a cron task, automatically downloads invoices for the implemented providers in a designated folder.

To configure the providers that will be consulted, you have to fill in a tasks.json with some minimum information, and for each provider, add it to the tasks list:

        {
            "company": "simyo",
            "options": {
                "username": "",
                "password": "",
                "user": "User 2"
            }

Where company is the company attribute of the imporer class related to thhat company. The username and password are mandatory, while user property is optional. If user provided it will be used to generate the filename of the downloaded invoice. Usefull when having more than one account for each provider.

A folder will be created the first time for each provider, and the invoices will be stored there.
