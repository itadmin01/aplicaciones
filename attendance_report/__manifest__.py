# -*- coding: utf-8 -*-
{
    'name': "Reporte de asistencia",
    'version': "13.0.4",
    'author': "IT Admin",
    'category': "",
    'depends': ['hr_attendance','om_hr_payroll', 'nomina_cfdi_ee', 
                'web_tree_dynamic_colored_field'
                ]
    ,
    'data': [
            'security/ir.model.access.csv',
           # 'templates/assets.xml',
           # 'wizard/import_attendance_view.xml',
           # 'wizard/remain_import_attandance.xml',
            'views/reporte_asistencia_view.xml',
            'data/if_roll_number.xml',
            'views/res_config_settings_view.xml',
            'views/hr_payrol_run.xml',
    ],
    'installable': True,
}
