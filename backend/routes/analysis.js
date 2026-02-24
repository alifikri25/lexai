const express = require('express');
const router = express.Router();
const { supabaseAdmin } = require('../services/supabase');
const authMiddleware = require('../middleware/auth');

// GET /api/analysis/:documentId
router.get('/:documentId', authMiddleware, async (req, res) => {
    try {
        // Verify document belongs to user
        const { data: doc, error: docError } = await supabaseAdmin
            .from('documents')
            .select('id')
            .eq('id', req.params.documentId)
            .eq('user_id', req.user.id)
            .single();

        if (docError || !doc) {
            return res.status(404).json({ error: 'Dokumen tidak ditemukan' });
        }

        const { data, error } = await supabaseAdmin
            .from('analyses')
            .select('*')
            .eq('document_id', req.params.documentId)
            .order('created_at', { ascending: false })
            .limit(1)
            .single();

        if (error) {
            return res.status(404).json({ error: 'Analisis belum tersedia' });
        }

        res.json({ analysis: data });
    } catch (err) {
        console.error('Get analysis error:', err);
        res.status(500).json({ error: 'Gagal mengambil hasil analisis' });
    }
});

module.exports = router;
