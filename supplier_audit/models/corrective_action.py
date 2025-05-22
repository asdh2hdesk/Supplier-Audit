from odoo import models, fields, api, _
from datetime import timedelta


class CorrectiveAction(models.Model):
    _name = 'corrective.action'
    _description = 'Corrective Action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date, id'

    name = fields.Char('Action Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    description = fields.Text('Action Description', required=True, tracking=True)

    audit_id = fields.Many2one('supplier.audit', string='Audit',
                               ondelete='cascade', tracking=True)
    finding_id = fields.Many2one('audit.finding', string='Related Finding',
                                 ondelete='cascade', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 required=True, tracking=True)

    action_type = fields.Selection([
        ('corrective', 'Corrective Action'),
        ('preventive', 'Preventive Action'),
        ('improvement', 'Improvement')
    ], string='Action Type', default='corrective', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical')
    ], string='Priority', default='1', tracking=True)

    planned_date = fields.Date('Planned Start Date', tracking=True)
    due_date = fields.Date('Due Date', required=True, tracking=True)
    completion_date = fields.Date('Completion Date', tracking=True)

    assigned_to = fields.Many2one('res.users', string='Assigned To',
                                  tracking=True, required=True)
    approved_by = fields.Many2one('res.users', string='Approved By', tracking=True)

    effectiveness_check_required = fields.Boolean('Effectiveness Check Required',
                                                  default=True, tracking=True)
    effectiveness_check_date = fields.Date('Effectiveness Check Date', tracking=True)
    effectiveness_result = fields.Selection([
        ('effective', 'Effective'),
        ('partial', 'Partially Effective'),
        ('ineffective', 'Ineffective')
    ], string='Effectiveness Result', tracking=True)

    notes = fields.Text('Notes')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('corrective.action') or _('New')
        return super(CorrectiveAction, self).create(vals)

    def action_set_planned(self):
        self.write({'state': 'planned'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_review(self):
        self.write({'state': 'review'})

    def action_complete(self):
        self.write({
            'state': 'completed',
            'completion_date': fields.Date.today()
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('finding_id')
    def _onchange_finding(self):
        if self.finding_id:
            self.audit_id = self.finding_id.audit_id.id
            self.partner_id = self.finding_id.partner_id.id