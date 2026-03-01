const express = require('express');
const router = express.Router();
const axios = require('axios');
const { supabaseAdmin } = require('../services/supabase');
const authMiddleware = require('../middleware/auth');

const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';

// GET /api/contracts/templates — list all contract templates
router.get('/templates', authMiddleware, async (req, res) => {
    try {
        const response = await axios.get(`${aiServiceUrl}/api/contracts/templates`);
        res.json(response.data);
    } catch (err) {
        console.error('Get templates error:', err.message);
        res.status(500).json({ error: 'Gagal mengambil daftar template' });
    }
});

// GET /api/contracts/templates/:id — get template detail
router.get('/templates/:id', authMiddleware, async (req, res) => {
    try {
        const response = await axios.get(`${aiServiceUrl}/api/contracts/templates/${req.params.id}`);
        res.json(response.data);
    } catch (err) {
        if (err.response?.status === 404) {
            return res.status(404).json({ error: 'Template tidak ditemukan' });
        }
        console.error('Get template error:', err.message);
        res.status(500).json({ error: 'Gagal mengambil detail template' });
    }
});

// POST /api/contracts/draft — generate contract draft
router.post('/draft', authMiddleware, async (req, res) => {
    try {
        const { template_id, form_data, title } = req.body;
        if (!template_id || !form_data) {
            return res.status(400).json({ error: 'template_id dan form_data wajib diisi' });
        }

        // Call AI service to generate draft
        const response = await axios.post(`${aiServiceUrl}/api/contracts/draft`, {
            template_id,
            form_data,
        }, { timeout: 120000 });

        const draft = response.data;

        // Save to database
        const { data: savedDraft, error: dbError } = await supabaseAdmin
            .from('contract_drafts')
            .insert({
                user_id: req.user.id,
                template_type: template_id,
                title: title || draft.template_name,
                draft_content: draft.draft_content,
                form_data: form_data,
            })
            .select()
            .single();

        if (dbError) {
            console.error('DB save error:', dbError);
            // Still return draft even if save fails
            return res.json({ draft, saved: false });
        }

        res.status(201).json({
            draft: { ...draft, id: savedDraft.id },
            saved: true,
        });
    } catch (err) {
        console.error('Draft error:', err.message);
        res.status(500).json({ error: err.response?.data?.detail || 'Gagal membuat draft kontrak' });
    }
});

// POST /api/contracts/export — export contract to Word/PDF
router.post('/export', authMiddleware, async (req, res) => {
    try {
        const { title, content, format } = req.body;
        if (!content || !format) {
            return res.status(400).json({ error: 'content dan format wajib diisi' });
        }

        const response = await axios.post(`${aiServiceUrl}/api/contracts/export`, {
            title: title || 'Kontrak',
            content,
            format,
        }, {
            timeout: 30000,
            responseType: 'arraybuffer',
        });

        const contentType = format === 'docx'
            ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            : 'application/pdf';

        const filename = format === 'docx'
            ? `LexAI_Kontrak_${title || 'draft'}.docx`
            : `LexAI_Kontrak_${title || 'draft'}.pdf`;

        res.set({
            'Content-Type': contentType,
            'Content-Disposition': `attachment; filename="${filename}"`,
        });
        res.send(Buffer.from(response.data));
    } catch (err) {
        console.error('Export error:', err.message);
        res.status(500).json({ error: 'Gagal mengexport kontrak' });
    }
});

// GET /api/contracts — list user's contract drafts
router.get('/', authMiddleware, async (req, res) => {
    try {
        const { data, error } = await supabaseAdmin
            .from('contract_drafts')
            .select('id, template_type, title, created_at, updated_at')
            .eq('user_id', req.user.id)
            .order('created_at', { ascending: false });

        if (error) throw error;

        res.json({ drafts: data || [] });
    } catch (err) {
        console.error('List drafts error:', err.message);
        res.status(500).json({ error: 'Gagal mengambil daftar draft' });
    }
});

// GET /api/contracts/:id — get a specific draft
router.get('/:id', authMiddleware, async (req, res) => {
    try {
        const { data, error } = await supabaseAdmin
            .from('contract_drafts')
            .select('*')
            .eq('id', req.params.id)
            .eq('user_id', req.user.id)
            .single();

        if (error || !data) {
            return res.status(404).json({ error: 'Draft tidak ditemukan' });
        }

        res.json({ draft: data });
    } catch (err) {
        console.error('Get draft error:', err.message);
        res.status(500).json({ error: 'Gagal mengambil draft' });
    }
});

// DELETE /api/contracts/:id — delete a draft
router.delete('/:id', authMiddleware, async (req, res) => {
    try {
        const { data, error } = await supabaseAdmin
            .from('contract_drafts')
            .delete()
            .eq('id', req.params.id)
            .eq('user_id', req.user.id);

        if (error) throw error;

        res.json({ message: 'Draft berhasil dihapus' });
    } catch (err) {
        console.error('Delete draft error:', err.message);
        res.status(500).json({ error: 'Gagal menghapus draft' });
    }
});

module.exports = router;
