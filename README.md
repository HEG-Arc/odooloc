# OdooSIM
# Getting started

## Prerequisities
Docker https://www.docker.com/get-started

## usage
- clone the repository

``git clone git@github.com:HEG-Arc/opensim.git``

- build and start
 
``docker-compose up -d``

This will setup an odoo 11 instance with opensim, sale_management,purchase,stock module installed

_access:_
    
      http://localhost:8069
    
      default odoo admin login : admin/admin
      

- stop and delete containers (to start again from fresh data)

``docker-compose down``


# shell access


``docker-compose -f docker-compose.yml -f docker-compose.yml run shell
``

then...

> \>>>env['res.users'].search([]).mapped('name')
>
>['Default Administrator', 'Player A1'] 

 



 

