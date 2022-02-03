{
    'name': "Mstech Timajas",
    "category": "External Service",
    'author': "Meditech",
    'summary':"Mstech External Service - Timajas",
    'depends': [
        'sale',
        'stock',
        'industry_fsm',
        'industry_fsm_sale',
        'maintenance',

    ],
    'data': [
        'data/project_data.xml',
        'views/view_project_task.xml',
        'views/maintenance_request.xml',
        'views/product_template.xml',
    ],
    'installable' : True,
    'auto_install' :  False,
    'application' :  False,
}
