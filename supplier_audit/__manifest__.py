{
    'name': 'Supplier Audit Management',
    'version': '1.0',
    'sequence': -100,
    'category': 'Inventory/Purchase',
    'summary': 'Supplier audit management system',
    'description': """
        This module provides functionality to manage supplier audits:
        * Create and manage audit checklists
        * Schedule and conduct supplier audits
        * Record audit findings
        * Track corrective actions
        * Generate audit reports
    """,
    'author': 'ASD',
    'website': 'https://www.asdsoftwares.com',
    'depends': ['base', 'purchase', 'contacts', 'mail','web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/audit_checklist_data.xml',
        'views/audit_checklist_views.xml',
        'views/audit_finding_views.xml',
        'views/corrective_action_views.xml',
        'views/supplier_audit_views.xml',
        'views/menu_views.xml',
        'report/supplier_audit_report.xml',
        'report/supplier_audit_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',
            'supplier_audit/static/src/js/radar_chart_widget.js',
            'supplier_audit/static/src/xml/radar_chart_templates.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
