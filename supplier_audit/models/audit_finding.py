from odoo import models, fields, api, _
from datetime import timedelta


class AuditFinding(models.Model):
    _name = 'audit.finding'
    _description = 'Audit Finding'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char('Finding Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    description = fields.Text('Finding Description', required=True, tracking=True)
    audit_id = fields.Many2one('supplier.audit', string='Audit', required=True,
                               ondelete='cascade', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 related='audit_id.partner_id', store=True)
    question_line_id = fields.Many2one('supplier.audit.question.line',
                                       string='Related Question', tracking=True)
    category_id = fields.Many2one('audit.question.category', string='Category',
                                  related='question_line_id.category_id', store=True)

    finding_date = fields.Date('Finding Date', default=fields.Date.context_today, tracking=True)

    severity = fields.Selection([
        ('critical', 'Critical'),
        ('major', 'Major'),
        ('minor', 'Minor'),
        ('observation', 'Observation'),
    ], string='Severity', required=True, tracking=True)

    standard_reference = fields.Char('Standard/Requirement Reference', tracking=True)
    evidence = fields.Text('Evidence', tracking=True)
    root_cause = fields.Text('Root Cause Analysis', tracking=True)

    corrective_action_ids = fields.One2many('corrective.action', 'finding_id',
                                            string='Corrective Actions')
    action_count = fields.Integer('Action Count', compute='_compute_action_count', store=True)

    state = fields.Selection([
        ('open', 'Open'),
        ('action_defined', 'Action Defined'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ], string='Status', default='open', tracking=True, compute='_compute_state', store=True)

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    due_date = fields.Date('Due Date', tracking=True)
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    company_id = fields.Many2one('res.company', related='audit_id.company_id', store=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('audit.finding') or _('New')
        return super(AuditFinding, self).create(vals)

    @api.depends('corrective_action_ids.state')
    def _compute_state(self):
        for record in self:
            if not record.corrective_action_ids:
                record.state = 'open'
            elif all(action.state == 'completed' for action in record.corrective_action_ids):
                record.state = 'closed'
            elif any(action.state == 'in_progress' for action in record.corrective_action_ids):
                record.state = 'in_progress'
            else:
                record.state = 'action_defined'

    @api.depends('corrective_action_ids')
    def _compute_action_count(self):
        for record in self:
            record.action_count = len(record.corrective_action_ids)

    def action_create_corrective_action(self):
        return {
            'name': _('New Corrective Action'),
            'type': 'ir.actions.act_window',
            'res_model': 'corrective.action',
            'view_mode': 'form',
            'context': {
                'default_finding_id': self.id,
                'default_audit_id': self.audit_id.id,
                'default_partner_id': self.partner_id.id,
                'default_description': 'Corrective action for: ' + self.description,
            },
            'target': 'new',
        }