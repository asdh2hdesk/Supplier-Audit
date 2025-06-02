from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class SupplierAudit(models.Model):
    _name = 'supplier.audit'
    _description = 'Supplier Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, id desc'

    name = fields.Char('Audit Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 required=True)
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

    question_line_ids = fields.One2many('supplier.audit.question.line', 'audit_id',
                                        string='Audit Questions')

    # Category ID fields - Now editable regular fields
    category_1_id = fields.Many2one('audit.question.category', string='Category 1')
    category_2_id = fields.Many2one('audit.question.category', string='Category 2')
    category_3_id = fields.Many2one('audit.question.category', string='Category 3')
    category_4_id = fields.Many2one('audit.question.category', string='Category 4')
    category_5_id = fields.Many2one('audit.question.category', string='Category 5')
    category_6_id = fields.Many2one('audit.question.category', string='Category 6')
    category_7_id = fields.Many2one('audit.question.category', string='Category 7')
    category_8_id = fields.Many2one('audit.question.category', string='Category 8')
    category_9_id = fields.Many2one('audit.question.category', string='Category 9')
    category_10_id = fields.Many2one('audit.question.category', string='Category 10')

    # Category Name fields - Still computed
    category_1_name = fields.Char('Category 1 Name', compute='_compute_category_names', store=True)
    category_2_name = fields.Char('Category 2 Name', compute='_compute_category_names', store=True)
    category_3_name = fields.Char('Category 3 Name', compute='_compute_category_names', store=True)
    category_4_name = fields.Char('Category 4 Name', compute='_compute_category_names', store=True)
    category_5_name = fields.Char('Category 5 Name', compute='_compute_category_names', store=True)
    category_6_name = fields.Char('Category 6 Name', compute='_compute_category_names', store=True)
    category_7_name = fields.Char('Category 7 Name', compute='_compute_category_names', store=True)
    category_8_name = fields.Char('Category 8 Name', compute='_compute_category_names', store=True)
    category_9_name = fields.Char('Category 9 Name', compute='_compute_category_names', store=True)
    category_10_name = fields.Char('Category 10 Name', compute='_compute_category_names', store=True)

    # Category question line fields
    category_1_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_2_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_3_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_4_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_5_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_6_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_7_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_8_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_9_question_ids = fields.One2many('supplier.audit.question.line',
                                              compute='_compute_category_question_lines')
    category_10_question_ids = fields.One2many('supplier.audit.question.line',
                                               compute='_compute_category_question_lines')

    # Category scoring fields for all 10 categories
    category_1_total_questions = fields.Integer('Category 1 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_1_total_score = fields.Integer('Category 1 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_1_max_score = fields.Integer('Category 1 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_1_percentage = fields.Float('Category 1 %', compute='_compute_category_scores', store=True, default=0.0)

    category_2_total_questions = fields.Integer('Category 2 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_2_total_score = fields.Integer('Category 2 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_2_max_score = fields.Integer('Category 2 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_2_percentage = fields.Float('Category 2 %', compute='_compute_category_scores', store=True, default=0.0)

    category_3_total_questions = fields.Integer('Category 3 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_3_total_score = fields.Integer('Category 3 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_3_max_score = fields.Integer('Category 3 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_3_percentage = fields.Float('Category 3 %', compute='_compute_category_scores', store=True, default=0.0)

    category_4_total_questions = fields.Integer('Category 4 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_4_total_score = fields.Integer('Category 4 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_4_max_score = fields.Integer('Category 4 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_4_percentage = fields.Float('Category 4 %', compute='_compute_category_scores', store=True, default=0.0)

    category_5_total_questions = fields.Integer('Category 5 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_5_total_score = fields.Integer('Category 5 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_5_max_score = fields.Integer('Category 5 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_5_percentage = fields.Float('Category 5 %', compute='_compute_category_scores', store=True, default=0.0)

    category_6_total_questions = fields.Integer('Category 6 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_6_total_score = fields.Integer('Category 6 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_6_max_score = fields.Integer('Category 6 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_6_percentage = fields.Float('Category 6 %', compute='_compute_category_scores', store=True, default=0.0)

    category_7_total_questions = fields.Integer('Category 7 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_7_total_score = fields.Integer('Category 7 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_7_max_score = fields.Integer('Category 7 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_7_percentage = fields.Float('Category 7 %', compute='_compute_category_scores', store=True, default=0.0)

    category_8_total_questions = fields.Integer('Category 8 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_8_total_score = fields.Integer('Category 8 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_8_max_score = fields.Integer('Category 8 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_8_percentage = fields.Float('Category 8 %', compute='_compute_category_scores', store=True, default=0.0)

    category_9_total_questions = fields.Integer('Category 9 Questions', compute='_compute_category_scores', store=True,
                                                default=0)
    category_9_total_score = fields.Integer('Category 9 Score', compute='_compute_category_scores', store=True,
                                            default=0)
    category_9_max_score = fields.Integer('Category 9 Max Score', compute='_compute_category_scores', store=True,
                                          default=0)
    category_9_percentage = fields.Float('Category 9 %', compute='_compute_category_scores', store=True, default=0.0)

    category_10_total_questions = fields.Integer('Category 10 Questions', compute='_compute_category_scores',
                                                 store=True, default=0)
    category_10_total_score = fields.Integer('Category 10 Score', compute='_compute_category_scores', store=True,
                                             default=0)
    category_10_max_score = fields.Integer('Category 10 Max Score', compute='_compute_category_scores', store=True,
                                           default=0)
    category_10_percentage = fields.Float('Category 10 %', compute='_compute_category_scores', store=True, default=0.0)


    @api.depends('question_line_ids.status', 'question_line_ids.category_id', 'question_line_ids.state')
    def _compute_category_scores(self):
        for rec in self:
            try:
                # Initialize all scores to 0
                for i in range(1, 11):
                    setattr(rec, f'category_{i}_total_questions', 0)
                    setattr(rec, f'category_{i}_total_score', 0)
                    setattr(rec, f'category_{i}_max_score', 0)
                    setattr(rec, f'category_{i}_percentage', 0.0)

                # Group questions by category
                category_stats = {}
                for question in rec.question_line_ids.filtered(lambda q: q.state == 'answered' and q.category_id):
                    cat_id = question.category_id.id
                    if cat_id not in category_stats:
                        category_stats[cat_id] = {
                            'total_questions': 0,
                            'total_score': 0,
                            'max_score': 0
                        }

                    category_stats[cat_id]['total_questions'] += 1
                    category_stats[cat_id]['total_score'] += int(question.status)
                    category_stats[cat_id]['max_score'] += 3  # Each question has max score of 3

                # Map stats to category fields
                for i in range(1, 11):
                    category = getattr(rec, f'category_{i}_id')
                    if category and category.id in category_stats:
                        stats = category_stats[category.id]
                        setattr(rec, f'category_{i}_total_questions', stats['total_questions'])
                        setattr(rec, f'category_{i}_total_score', stats['total_score'])
                        setattr(rec, f'category_{i}_max_score', stats['max_score'])

                        if stats['max_score'] > 0:
                            percentage = (stats['total_score'] / stats['max_score']) * 100
                            setattr(rec, f'category_{i}_percentage', percentage)

            except Exception as e:
                _logger.error(f"Error computing category scores: {e}")
                # If error occurs, set all to 0
                for i in range(1, 11):
                    setattr(rec, f'category_{i}_percentage', 0.0)

    def get_category_data(self):
        """Returns structured data for all categories for use in views"""
        self.ensure_one()
        categories = []
        for i in range(1, 11):
            category_id = getattr(self, f'category_{i}_id')
            if not category_id:
                continue

            categories.append({
                'index': i,
                'name': getattr(self, f'category_{i}_name'),
                'total_questions': getattr(self, f'category_{i}_total_questions'),
                'total_score': getattr(self, f'category_{i}_total_score'),
                'max_score': getattr(self, f'category_{i}_max_score'),
                'percentage': getattr(self, f'category_{i}_percentage'),
            })
        return categories

    @api.depends('category_1_id', 'category_2_id', 'category_3_id', 'category_4_id', 'category_5_id',
                 'category_6_id', 'category_7_id', 'category_8_id', 'category_9_id', 'category_10_id')
    def _compute_category_names(self):
        for rec in self:
            try:
                for i in range(10):
                    category_field = f'category_{i + 1}_id'
                    name_field = f'category_{i + 1}_name'

                    category = getattr(rec, category_field)
                    if category and category.exists():
                        setattr(rec, name_field, category.name)
                    else:
                        setattr(rec, name_field, '')
            except Exception as e:
                # Reset all name fields on error
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"Error in _compute_category_names: {e}")

                for i in range(10):
                    setattr(rec, f'category_{i + 1}_name', '')

    @api.depends('question_line_ids.category_id')
    def _compute_category_question_lines(self):
        for rec in self:
            try:
                for i in range(10):
                    category_field = f'category_{i + 1}_id'
                    question_field = f'category_{i + 1}_question_ids'

                    category = getattr(rec, category_field)
                    if category and category.exists():
                        # Filter question lines by category record
                        lines = rec.question_line_ids.filtered(
                            lambda l: l.category_id == category
                        )
                        setattr(rec, question_field, lines)
                    else:
                        # Set empty recordset
                        setattr(rec, question_field, self.env['supplier.audit.question.line'])
            except Exception as e:
                # Reset all question line fields on error
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"Error in _compute_category_question_lines: {e}")

                for i in range(10):
                    setattr(rec, f'category_{i + 1}_question_ids',
                            self.env['supplier.audit.question.line'])

    @api.onchange('category_1_id', 'category_2_id', 'category_3_id', 'category_4_id', 'category_5_id',
                  'category_6_id', 'category_7_id', 'category_8_id', 'category_9_id', 'category_10_id')
    def _onchange_categories(self):
        """Update question lines when categories are changed"""
        for rec in self:
            # Get all current categories
            current_categories = [
                rec.category_1_id, rec.category_2_id, rec.category_3_id,
                rec.category_4_id, rec.category_5_id, rec.category_6_id,
                rec.category_7_id, rec.category_8_id, rec.category_9_id,
                rec.category_10_id
            ]

            # Update category names
            rec._compute_category_names()

    def update_all_question_categories(self):
        """Update all question lines to use the current categories"""
        for rec in self:
            # Get all current categories
            current_categories = [
                rec.category_1_id, rec.category_2_id, rec.category_3_id,
                rec.category_4_id, rec.category_5_id, rec.category_6_id,
                rec.category_7_id, rec.category_8_id, rec.category_9_id,
                rec.category_10_id
            ]

            # Assign each question to one of the current categories
            for line in rec.question_line_ids:
                if line.category_id not in current_categories:
                    # Assign to first available category
                    for cat in current_categories:
                        if cat:
                            line.category_id = cat
                            break

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

    @api.depends('question_line_ids.status')
    def _compute_compliance_score(self):
        for record in self:
            answered_questions = record.question_line_ids.filtered(
                lambda x: x.state == 'answered')
            if answered_questions:
                # Assuming status '3' is fully compliant, '2' is partially, etc.
                total_score = sum(int(q.status) for q in answered_questions)
                max_possible_score = len(answered_questions) * 3  # Max score is 3
                print(total_score)
                print(max_possible_score)
                record.compliance_score = (total_score / max_possible_score) if max_possible_score else 0
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
            # Get unique categories from checklist questions
            categories = audit.checklist_id.question_ids.mapped('category_id').filtered(lambda x: x)
            categories = list(set(categories))[:10]  # Get up to 10 unique categories

            # Set the category fields
            for i, cat in enumerate(categories):
                setattr(audit, f'category_{i + 1}_id', cat)

            # Create question lines
            for question in audit.checklist_id.question_ids:
                self.env['supplier.audit.question.line'].create({
                    'audit_id': audit.id,
                    'question_id': question.id,
                    'name': question.name,
                    'category_id': question.category_id.id if question.category_id else categories[
                        0].id if categories else False,
                    'evidence': question.evidence,
                    'scoring_criteria': question.scoring_criteria,
                    'observation': question.observation,
                    'action': question.action,
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
    category_id = fields.Many2one(
        'audit.question.category',
        string="Category",
        required=True,
        ondelete='restrict'
    )
    evidence = fields.Text('Evidence/Observations')
    scoring_criteria = fields.Text('Scoring Criteria', help="Criteria for scoring the question")
    status = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
    ], string='Status', default='0', help="Score or status of the question based on evaluation")
    observation = fields.Text('Observation', help="Observations noted during the audit")
    action = fields.Text('Action', help="Actions to be taken based on the audit findings")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('na', 'Not Applicable'),
    ], string='Status', default='pending')

    finding_ids = fields.One2many('audit.finding', 'question_line_id', string='Related Findings')

    def mark_as_not_applicable(self):
        self.state = 'na'

    @api.onchange('status')
    def _onchange_status_set_state(self):
        for record in self:
            if record.status and record.status != '0':
                record.state = 'answered'