
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MsdAttendance(models.Model):
    _name = "msd.attendance"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "msd_attendance"
    _order = "create_date desc, id desc"
    _check_company_auto = True

    @api.model
    def _default_employee_id(self):
        return self.env.user.employee_id

    @api.model
    def _default_approver(self):
        return self.env.user.employee_id.parent_id

    # @api.model
    # def _default_pjcode(self):
    #     return self.env.user.employee_id.pj_cd

    title = fields.Char(string="勤務表報告", copy=False, help="勤務表の報告です")
    employee_id = fields.Many2one('hr.employee', string="従業員", readonly=True, default=_default_employee_id)
    state = fields.Selection([
        ('draft', 'ドラフト'),
        ('reported', '提出済'),
        ('approved', '確認済')
    ],  string='ステータス', tracking=True, default='draft')
    user_id = fields.Many2one('res.users', 'Manager', readonly=True, copy=False,
                               tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department')
    pjcode = fields.Char(string="PJコード", required=True, default=lambda self: self.env['ss.order']._get_pj_cds(self.env.user.employee_id.id))
    workload = fields.Float(string="工数")
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    approver = fields.Many2one('hr.employee', string="承認者", default=_default_approver)
    date_start = fields.Date(string="開始日")
    date_end = fields.Date(string="終了日")
    remarks = fields.Text(string="備考欄")
    attachment = fields.Char(string="添付ファイル")

    def _compute_attachment_number(self):
        """附件上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'msd.attendance'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    def action_get_attachment_view(self):
        """附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'msd.attendance'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'msd.attendance', 'default_res_id': self.id}
        return res

    image_1920 = fields.Image(string="図書写真")
    name = fields.Char(string="書名")
    isbn = fields.Char(string="作成時間", copy=False)
    author = fields.Char(string="作者")
    pages = fields.Integer(string="ページ数")
    publish_date = fields.Date(string="出版時期")
    publisher = fields.Char(string="出版社")
    price = fields.Float(string="定価", digits=(7, 2))
    description = fields.Text(string="概要", help="""本図書の概要説明""")
    binding_type = fields.Selection(
        [("common", "普通"), ("hardcover", "ハードカバー")],
        string="図書形式", index=True, default='common'
    )
    e_link = fields.Html(string="電子版リンク")
    borrowed = fields.Boolean(string="貸出中", default=False)
    date_last_borrowed = fields.Datetime("最後の貸出時刻", index=True)

    #@api.model
    #def name_get(self):
        #result = []
        #for book in self:
         #   result.append((book.id, '%s(%s)' % (book.name, book.isbn)))
        #return result
    # def action_return(self):
    #     self.borrowed = False
    #     self.date_last_borrowed = None
    def _default_employee_id(self):
        return self.env.user.employee_id

    def _get_employee_id_domain(self):
        res = [('id', '=', 0)]  # Nothing accepted by domain, by default
        if self.user_has_groups('msd_attendance.group_msd_attendance_user'):
            res = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]"  # Then, domain accepts everything
        elif self.user_has_groups('msd_attendance.group_msd_attendance_team_approver') and self.env.user.employee_ids:
            user = self.env.user
            employee = self.env.user.employee_id
            res = [
                '|', '|', '|',
                ('department_id.manager_id', '=', employee.id),
                ('parent_id', '=', employee.id),
                ('id', '=', employee.id),
                ('expense_manager_id', '=', user.id),
                '|', ('company_id', '=', False), ('company_id', '=', employee.company_id.id),
            ]
        elif self.env.user.employee_id:
            employee = self.env.user.employee_id
            res = [('id', '=', employee.id), '|', ('company_id', '=', False),
                   ('company_id', '=', employee.company_id.id)]
        return res

    def action_submit_attendance(self):
        self.write({'state': 'reported'})
        self.activity_update()

    def approve_attendance(self):
        # if not self.user_has_groups('hr_expense.group_hr_expense_team_approver'):
        #     raise UserError(_("Only Managers and HR Officers can approve expenses"))
        # elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
        #     current_managers = self.employee_id.expense_manager_id | self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id
        #
        #     if self.employee_id.user_id == self.env.user:
        #         raise UserError(_("You cannot approve your own expenses"))
        #
        #     if not self.env.user in current_managers and not self.user_has_groups('hr_expense.group_hr_expense_user') and self.employee_id.expense_manager_id != self.env.user:
        #         raise UserError(_("You can only approve your department expenses"))
        #
        # responsible_id = self.user_id.id or self.env.user.id
        #self.write({'state': 'approve', 'user_id': responsible_id})
        self.write({'state': 'approved'})
        self.activity_update()

    # def action_process_attendance(self):
    #     self.write({'state': 'done'})
    #     self.activity_update()

    # --------------------------------------------
    # Mail Thread
    # --------------------------------------------

    # def _track_subtype(self, init_values):
    #     self.ensure_one()
    #     if 'state' in init_values and self.state == 'approve':
    #         return self.env.ref('hr_expense.mt_expense_approved')
    #     elif 'state' in init_values and self.state == 'cancel':
    #         return self.env.ref('hr_expense.mt_expense_refused')
    #     elif 'state' in init_values and self.state == 'done':
    #         return self.env.ref('hr_expense.mt_expense_paid')
    #     return super(MsdAttendance, self)._track_subtype(init_values)
    #
    # def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
    #     res = super(MsdAttendance, self)._message_auto_subscribe_followers(updated_values, subtype_ids)
    #     if updated_values.get('employee_id'):
    #         employee = self.env['hr.employee'].browse(updated_values['employee_id'])
    #         if employee.user_id:
    #             res.append((employee.user_id.partner_id.id, subtype_ids, False))
    #     return res

    def _get_responsible_for_approval(self):
        if self.user_id:
            return self.user_id
        elif self.employee_id.parent_id.user_id:
            return self.employee_id.parent_id.user_id
        elif self.employee_id.department_id.manager_id.user_id:
            return self.employee_id.department_id.manager_id.user_id
        return self.env['res.users']

    def activity_update(self):
        # for expense_report in self.filtered(lambda hol: hol.state in ['reported', 'approved', 'done']):
        for expense_report in self.filtered(lambda hol: hol.state in ['reported']):
            self.activity_schedule(
                'msd_attendance.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        self.filtered(lambda hol: hol.state == 'approved').activity_feedback(['msd_attendance.mail_act_expense_approval'])
        # self.filtered(lambda hol: hol.state == 'cancel').activity_unlink(['msd_attendance.mail_act_expense_approval'])
