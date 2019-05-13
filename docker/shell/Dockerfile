# optional extra container to run odoo shell
# docker-compose -f docker-compose
FROM opensim_odoo:latest

USER root
RUN pip3 install ipython ptpython jupyter
RUN mkdir -p /mnt/notebooks

WORKDIR /mnt/notebooks/
# jupyter/ipython notebook not yet working
#ENTRYPOINT ["shell","notebook", "--ip", "0.0.0.0", "--allow-root","/mnt/notebooks"]
# defaulting to terminal based ptbython REPL
ENTRYPOINT ["odoo", "shell", "--shell-interface=ptpython", "-d", "odoo", "--db_user=odoo", "--db_password=odoo", "--db_host=db", "--addons-path=/opt/odoo/community_addons,/mnt/extra-addons"]


