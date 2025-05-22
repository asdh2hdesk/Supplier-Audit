from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class SupplierAudit(models.Model):
    _name = 'supplier.audit'
    _description = 'Supplier Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, id desc'

    name = fields.Char('Audit Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 required=True, tracking=True,
                                 domain=[('supplier_rank', '>', 0)])
    audit_date = fields.Date('Audit Date', required=True, tracking=True)
    end_date = fields.Date('End Date', tracking=True)
    duration = fields.Integer('Duration (days)', compute='_compute_duration', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    auditor_id = fields.Many2one('res.users', string='Lead Auditor',
                                 required=True, default=lambda self: self.env.user, tracking=True)
    audit_team_ids = fields.Many2many('res.users', 'audit_team_users_rel', 'audit_id', 'user_id',
                                      string='Audit Team')

    checklist_id = fields.Many2one('audit.checklist', string='Audit Checklist',
                                   required=True, tracking=True)
    question_line_ids = fields.One2many('supplier.audit.question.line', 'audit_id',
                                        string='Audit Questions')
    finding_ids = fields.One2many('audit.finding', 'audit_id', string='Audit Findings')
    corrective_action_ids = fields.One2many('corrective.action', 'audit_id',
                                            string='Corrective Actions')

    total_questions = fields.Integer('Total Questions', compute='_compute_progress_stats', store=True)
    completed_questions = fields.Integer('Completed Questions',
                                         compute='_compute_progress_stats', store=True)
    completion_rate = fields.Float('Completion Rate (%)',
                                   compute='_compute_progress_stats', store=True)

    compliance_score = fields.Float('Compliance Score (%)',
                                    compute='_compute_compliance_score', store=True)

    notes = fields.Text('Notes')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    # Statistical fields
    critical_findings = fields.Integer('Critical Findings',
                                       compute='_compute_findings_stats', store=True)
    major_findings = fields.Integer('Major Findings',
                                    compute='_compute_findings_stats', store=True)
    minor_findings = fields.Integer('Minor Findings',
                                    compute='_compute_findings_stats', store=True)
    open_actions = fields.Integer('Open Actions',
                                  compute='_compute_action_stats', store=True)

    attachment_ids = fields.One2many('ir.attachment', 'res_id', string='Attachments',
                                     domain=[('res_model', '=', 'supplier.audit')],
                                     auto_join=True)

    result = fields.Selection([
        ('pass', 'Pass'),
        ('conditional_pass', 'Conditional Pass'),
        ('fail', 'Fail'),
    ], string='Audit Result', tracking=True)

    @api.depends('audit_date', 'end_date')
    def _compute_duration(self):
        for record in self:
            if record.audit_date and record.end_date:
                if record.end_date >= record.audit_date:
                    delta = record.end_date - record.audit_date
                    record.duration = delta.days + 1
                else:
                    record.duration = 0
            else:
                record.duration = 0

    @api.depends('question_line_ids.state')
    def _compute_progress_stats(self):
        for record in self:
            record.total_questions = len(record.question_line_ids)
            record.completed_questions = len(record.question_line_ids.filtered(
                lambda x: x.state == 'answered'))
            record.completion_rate = (
                        record.completed_questions / record.total_questions * 100) if record.total_questions else 0

    @api.depends('question_line_ids.compliance')
    def _compute_compliance_score(self):
        for record in self:
            answered_questions = record.question_line_ids.filtered(
                lambda x: x.state == 'answered' and x.question_type == 'compliance')
            if answered_questions:
                compliant_count = len(answered_questions.filtered(lambda x: x.compliance == 'compliant'))
                record.compliance_score = (compliant_count / len(answered_questions)) * 100
            else:
                record.compliance_score = 0

    @api.depends('finding_ids.severity')
    def _compute_findings_stats(self):
        for record in self:
            record.critical_findings = len(record.finding_ids.filtered(lambda f: f.severity == 'critical'))
            record.major_findings = len(record.finding_ids.filtered(lambda f: f.severity == 'major'))
            record.minor_findings = len(record.finding_ids.filtered(lambda f: f.severity == 'minor'))

    @api.depends('corrective_action_ids.state')
    def _compute_action_stats(self):
        for record in self:
            record.open_actions = len(record.corrective_action_ids.filtered(
                lambda a: a.state not in ['completed', 'cancelled']))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('supplier.audit') or _('New')

        audit = super(SupplierAudit, self).create(vals)

        # Create question lines based on the selected checklist
        if audit.checklist_id:
            for question in audit.checklist_id.question_ids:
                self.env['supplier.audit.question.line'].create({
                    'audit_id': audit.id,
                    'question_id': question.id,
                    'name': question.name,
                    'category_id': question.category_id.id,
                    'question_type': question.question_type,
                    'weight': question.weight,
                })

        return audit

    def action_plan(self):
        self.write({'state': 'planned'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        # Check if all questions are answered
        if self.completion_rate < 100:
            raise ValidationError(_("All questions must be answered before completing the audit."))

        # Determine audit result based on findings and scores
        result = 'pass'  # Default
        if self.critical_findings > 0:
            result = 'fail'
        elif self.major_findings > 0 or self.compliance_score < 80:
            result = 'conditional_pass'

        self.write({
            'state': 'done',
            'result': result
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def create_finding(self):
        return {
            'name': _('New Finding'),
            'type': 'ir.actions.act_window',
            'res_model': 'audit.finding',
            'view_mode': 'form',
            'context': {
                'default_audit_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
            'target': 'new',
        }

    def create_corrective_action(self):
        return {
            'name': _('New Corrective Action'),
            'type': 'ir.actions.act_window',
            'res_model': 'corrective.action',
            'view_mode': 'form',
            'context': {
                'default_audit_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
            'target': 'new',
        }


class SupplierAuditQuestionLine(models.Model):
    _name = 'supplier.audit.question.line'
    _description = 'Supplier Audit Question Line'
    _order = 'sequence, id'

    audit_id = fields.Many2one('supplier.audit', string='Audit', ondelete='cascade')
    question_id = fields.Many2one('audit.checklist.question', string='Question Template')
    name = fields.Text('Question', required=True)
    sequence = fields.Integer('Sequence', default=10)
    category_id = fields.Many2one('audit.question.category', string='Category')

    question_type = fields.Selection([
        ('compliance', 'Compliance (Yes/No)'),
        ('rating', 'Rating (1-5)'),
        ('text', 'Text Answer'),
    ], string='Question Type', default='compliance', required=True)

    state = fields.Selection([
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('na', 'Not Applicable'),
    ], string='Status', default='pending')

    # For compliance questions
    compliance = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
    ], string='Compliance')

    # For rating questions
    rating = fields.Selection([
        ('1', '1 - Poor'),
        ('2', '2 - Below Average'),
        ('3', '3 - Average'),
        ('4', '4 - Good'),
        ('5', '5 - Excellent'),
    ], string='Rating')

    text_answer = fields.Text('Answer')
    evidence = fields.Text('Evidence/Observations')
    finding_ids = fields.One2many('audit.finding', 'question_line_id', string='Related Findings')
    weight = fields.Float('Weight', default=1.0)

    @api.onchange('compliance', 'rating', 'text_answer')
    def _onchange_answer(self):
        if self.question_type == 'compliance' and self.compliance:
            self.state = 'answered'
        elif self.question_type == 'rating' and self.rating:
            self.state = 'answered'
        elif self.question_type == 'text' and self.text_answer:
            self.state = 'answered'
        else:
            self.state = 'pending'

    def mark_as_not_applicable(self):
        self.state = 'na'