from odoo import models, fields, api, _


class AuditChecklist(models.Model):
    _name = 'audit.checklist'
    _description = 'Audit Checklist Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Checklist Name', required=True, tracking=True)
    code = fields.Char('Checklist Code', tracking=True)
    description = fields.Text('Description')
    version = fields.Char('Version', default='1.0', tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)

    question_ids = fields.One2many('audit.checklist.question', 'checklist_id',
                                   string='Questions')
    category_ids = fields.Many2many('audit.question.category', string='Categories',
                                    compute='_compute_categories', store=True)

    total_questions = fields.Integer('Total Questions', compute='_compute_question_count', store=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    @api.depends('question_ids.category_id')
    def _compute_categories(self):
        for record in self:
            record.category_ids = record.question_ids.mapped('category_id')

    @api.depends('question_ids')
    def _compute_question_count(self):
        for record in self:
            record.total_questions = len(record.question_ids)

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': _('%s (Copy)') % self.name,
            'version': self.version + ' (Copy)',
        })
        return super(AuditChecklist, self).copy(default)


class AuditChecklistQuestion(models.Model):
    _name = 'audit.checklist.question'
    _description = 'Audit Checklist Question'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence Number', default=10, help="Serial number of the question")
    sl_no = fields.Integer('Sl.No', compute= '_compute_serial_no')
    name = fields.Text('Question', required=True)
    evidence = fields.Text('Evidence', help="Details of evidence required to evaluate the question")
    scoring_criteria = fields.Text('Scoring Criteria', help="Criteria for scoring the question")
    status = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
    ], string='Score', default='3', help="Score or status of the question based on evaluation")
    observation = fields.Text('Observation', help="Observations noted during the audit")
    action = fields.Text('Action', help="Actions to be taken based on the audit findings")

    checklist_id = fields.Many2one('audit.checklist', string='Checklist', ondelete='cascade')
    category_id = fields.Many2one('audit.question.category', string='Category')

    # question_type = fields.Selection([
    #     ('compliance', 'Compliance (Yes/No)'),
    #     ('rating', 'Rating (1-5)'),
    #     ('text', 'Text Answer'),], string='Question Type', default='compliance', required=True)
    #
    # guidance = fields.Text('Guidance Notes')
    # reference = fields.Char('Reference')
    # weight = fields.Float('Weight', default=1.0, help="Importance factor for scoring calculations")

    @api.model
    def create(self, vals):
        # Auto-assign a category if none is provided
        if not vals.get('category_id'):
            default_category = self.env['audit.question.category'].search(
                [('name', '=', 'General')], limit=1)
            if not default_category:
                default_category = self.env['audit.question.category'].create({'name': 'General'})
            vals['category_id'] = default_category.id
        return super(AuditChecklistQuestion, self).create(vals)

    @api.depends('sequence', 'checklist_id')
    def _compute_serial_no(self):
        for line in self.mapped('checklist_id'):
            sl_no = 1
            for lines in line.question_ids:
                lines.sl_no = sl_no
                sl_no += 1



class AuditQuestionCategory(models.Model):
    _name = 'audit.question.category'
    _description = 'Audit Question Category'
    _order = 'sequence, name'

    name = fields.Char('Category Name', required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=10)
    color = fields.Integer('Color Index')

    question_ids = fields.One2many('audit.checklist.question', 'category_id',
                                   string='Questions')
    question_count = fields.Integer('Question Count', compute='_compute_question_count', store=True)

    @api.depends('question_ids')
    def _compute_question_count(self):
        for record in self:
            record.question_count = len(record.question_ids)