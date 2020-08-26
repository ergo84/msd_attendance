{
    'name': "msd_attendance",
    'summary': """
        勤務表管理
        """,
    'sequence': 1,
    'description': """
        This application allows you to manage your employees' attendance report.
        The whole flow is implemented as:
---------------------------------
* Draft attendance report
* Submitted by the employee to his manager
* Approved by his manager
* Validation by the Department of central management
    """,
    'author': "msd",
    'website':'https://www.msdcorp.co.jp/',
    'category': 'tools',
    'version': '0.1',
    'depends': ['base','mail'],
    'data': [
        'security/msd_attendance_security.xml',
        'security/ir.model.access.csv',
        # 'security/ir_rule.xml',
        'views/msd_attendance.xml',

    ],
    'installable': True,
    'application': True,
}
