# -*- coding: utf-8 -*-
{
    'name': "Reporte de asistencia",
    'version': "13.05",
    'author': "IT Admin",
    'category': "",
    'depends': ['hr_attendance','om_hr_payroll', 'nomina_cfdi_ee', 
                'web_tree_dynamic_colored_field'
                ]
    ,
    'data': [
            'security/ir.model.access.csv',
            'views/reporte_asistencia_view.xml',
            'data/if_roll_number.xml',
            'views/res_config_settings_view.xml',
            'views/hr_payrol_run.xml',
    ],
    'installable': True,
}
