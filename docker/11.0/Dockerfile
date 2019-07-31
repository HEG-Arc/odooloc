FROM odoo:11.0

# install git
USER root
# address missing phonenumbers requirement in odoo11.0 image
# INFO odoo odoo.addons.sms.wizard.send_sms: The `phonenumbers` Python module is not available. Phone number validation will be skipped.
RUN pip3 install phonenumbers viivakoodi

# install git to allow  retrieving extra addons from source
RUN apt-get -y update && apt-get -y install git

WORKDIR /tmp
# retrieve our source addons dependencies (cbc accountant)
# git archive not supported by github (but supported by bitbucket)
#RUN git archive --output=/tmp/archive.zip --remote=git@github.com:rogerxu/webpack-demo.git master app/images /tmp/var/lib/odoo/addons/11.0/
RUN git clone --depth=1 --branch=11.0 --single-branch https://github.com/CubicERP/apps.git
RUN mkdir -p /opt/odoo/community_addons
RUN cp -av apps/account_accountant_cbc /opt/odoo/community_addons; cp -av apps/account_report_cbc /opt/odoo/community_addons
RUN rm -rf apps
# add account_chart_template_multicompany module from addons-onestein
# to allow automatic installation of default chart of account to all companies
RUN git clone --depth=1 --branch=10.0 --single-branch https://github.com/onesteinbv/addons-onestein.git
RUN cp -av addons-onestein/account_chart_template_multicompany /opt/odoo/community_addons
RUN rm -rf addons-onestein
USER odoo
WORKDIR /
COPY ./wait-for-postgres.sh /
# wait-for-postgres waits for db availability then call baseimage entrypoint.sh with all CMD arguments
ENTRYPOINT ["./wait-for-postgres.sh"]
